from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import load_config
from .keyword_aliases import keyword_intent_group, normalize_keyword, normalize_literal_keyword
from .keywords import apply_initial_intent_score, rank_keywords
from .models import Briefing, KeywordCandidate
from .paths import Paths, safe_filename


USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
SEARCHAD_BASE_URL = "https://api.searchad.naver.com"
SEARCHAD_KEYWORD_TOOL_PATH = "/keywordstool"


def check_keywords(paths: Paths, keywords: list[KeywordCandidate], briefing: Briefing | None = None) -> None:
    paths.serp_dir.mkdir(parents=True, exist_ok=True)
    config = load_config()
    for index, candidate in enumerate(keywords):
        candidate = keywords[index]
        if index:
            time.sleep(0.35)
        result = collect_keyword_evidence(candidate.keyword, config)
        if briefing:
            filter_result_related_keywords(result, briefing)
        apply_result(candidate, result)
        write_analysis(paths, candidate.keyword, result)

    rank_keywords(keywords)


def collect_keyword_evidence(keyword: str, config) -> dict:
    autocomplete_terms = fetch_autocomplete(keyword)
    searchad = fetch_searchad(keyword, config)
    search_counts = fetch_search_counts(keyword, config)
    mobile_search = {
        "status": "SKIPPED",
        "reason": "Mobile SERP HTML parsing is not part of default API keyword scoring; use browser QA separately for blog exposure/influencer checks.",
        "blog_exposure": "UNKNOWN",
        "influencer_dominance": "UNKNOWN",
    }
    return {
        "keyword": keyword,
        "autocomplete_terms": autocomplete_terms,
        "searchad": searchad,
        "naver_search_api": search_counts,
        "mobile_search": mobile_search,
        "memo": "",
    }


def fetch_autocomplete(keyword: str) -> list[str]:
    url = "https://ac.search.naver.com/nx/ac?" + urlencode({
        "q": keyword,
        "q_enc": "UTF-8",
        "st": "100",
        "r_format": "json",
        "r_enc": "UTF-8",
        "r_unicode": "0",
        "t_koreng": "1",
        "ans": "2",
        "run": "2",
        "rev": "4",
        "con": "0",
    })
    try:
        data = http_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return [f"ERROR: {exc}"]
    terms: list[str] = []
    for group in data.get("items", []):
        for item in group:
            if isinstance(item, list) and item:
                term = clean_text(str(item[0]))
                if term and term not in terms:
                    terms.append(term)
    return terms


def fetch_searchad(keyword: str, config) -> dict:
    if not (
        config.naver_searchad_access_license
        and config.naver_searchad_secret_key
        and config.naver_searchad_customer_id
    ):
        return {
            "status": "SKIPPED",
            "reason": "NAVER_SEARCHAD_ACCESS_LICENSE/NAVER_SEARCHAD_SECRET_KEY/NAVER_SEARCHAD_CUSTOMER_ID not set",
        }

    timestamp = str(int(time.time() * 1000))
    method = "GET"
    signature = searchad_signature(timestamp, method, SEARCHAD_KEYWORD_TOOL_PATH, config.naver_searchad_secret_key)
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": config.naver_searchad_access_license,
        "X-Customer": config.naver_searchad_customer_id,
        "X-Signature": signature,
    }
    url = SEARCHAD_BASE_URL + SEARCHAD_KEYWORD_TOOL_PATH + "?" + urlencode({
        "hintKeywords": keyword.replace(" ", ""),
        "showDetail": 1,
    })
    try:
        data = http_json(url, headers=headers)
    except HTTPError as exc:
        return {"status": "ERROR", "error": f"HTTP {exc.code}: {safe_error_body(exc)}"}
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "ERROR", "error": str(exc)}

    raw_items = data.get("keywordList") or []
    items = [normalize_searchad_item(item) for item in raw_items if item.get("relKeyword")]
    exact = pick_searchad_item(keyword, items)
    return {
        "status": "OK" if items else "EMPTY",
        "exact": exact,
        "keywordList": items,
        "related_keywords": [
            item for item in items
            if normalize_keyword(item["relKeyword"]) != normalize_keyword(keyword)
        ][:30],
    }


def fetch_search_counts(keyword: str, config) -> dict:
    if not (config.naver_client_id and config.naver_client_secret):
        return {"status": "SKIPPED", "reason": "NAVER_CLIENT_ID/NAVER_CLIENT_SECRET not set"}

    headers = {
        "X-Naver-Client-Id": config.naver_client_id,
        "X-Naver-Client-Secret": config.naver_client_secret,
    }
    out = {"status": "OK"}
    out["blog"] = fetch_search_total("https://openapi.naver.com/v1/search/blog.json", keyword, headers)
    out["cafe"] = "SKIPPED: cafe count is not part of default blog competition scoring"
    return out


def fetch_search_total(endpoint: str, keyword: str, headers: dict) -> int | str:
    for display in (1, 10):
        url = endpoint + "?" + urlencode({"query": keyword, "display": display, "start": 1, "sort": "sim"})
        try:
            return http_json(url, headers=headers).get("total", "")
        except HTTPError as exc:
            if display == 1 and exc.code in (400, 401, 403):
                continue
            return f"ERROR: HTTP {exc.code}: {safe_error_body(exc)}"
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            return f"ERROR: {exc}"
    return "ERROR: search API failed"


def fetch_mobile_search(keyword: str) -> dict:
    url = "https://m.search.naver.com/search.naver?" + urlencode({"query": keyword})
    try:
        html = http_text(url)
    except (HTTPError, URLError, TimeoutError) as exc:
        return {"status": "ERROR", "error": str(exc)}

    text = clean_text(html)
    return {
        "status": "OK",
        "blog_exposure": classify_blog_exposure(text),
        "influencer_dominance": "UNKNOWN",
        "related_terms": [],
        "recommended_terms": [],
        "ai_questions": [],
        "parser_note": "Mobile HTML fetched. Related/recommended/AI terms require a stable browser parser; autocomplete remains the reliable public SERP signal.",
        "html_excerpt": text[:2000],
    }


def apply_result(candidate: KeywordCandidate, result: dict) -> None:
    autocomplete = clean_terms(result.get("autocomplete_terms", []))
    mobile = result.get("mobile_search") or {}
    searchad = result.get("searchad") or {}
    counts = result.get("naver_search_api") or {}
    exact = searchad.get("exact") or {}

    candidate.autocomplete_seen = mark_seen(candidate.keyword, autocomplete)
    candidate.related_seen = "UNKNOWN"
    candidate.recommended_seen = "UNKNOWN"
    candidate.ai_question_seen = "UNKNOWN"
    candidate.blog_exposure = mobile.get("blog_exposure") or "UNKNOWN"
    candidate.influencer_dominance = mobile.get("influencer_dominance") or "UNKNOWN"

    if exact:
        candidate.monthly_pc_searches = string_value(exact.get("monthlyPcQcCnt"))
        candidate.monthly_mobile_searches = string_value(exact.get("monthlyMobileQcCnt"))
        candidate.monthly_searches = string_value(exact.get("monthlySearches"))
        candidate.searchad_comp_idx = string_value(exact.get("compIdx"))
        candidate.monthly_pc_ctr = string_value(exact.get("monthlyAvePcCtr"))
        candidate.monthly_mobile_ctr = string_value(exact.get("monthlyAveMobileCtr"))
        candidate.pl_avg_depth = string_value(exact.get("plAvgDepth"))

    candidate.search_volume_status = search_volume_status(candidate, searchad)
    if isinstance(counts.get("blog"), int):
        candidate.blog_count = str(counts["blog"])
        candidate.blog_count_status = "OK"
    else:
        candidate.blog_count_status = f"UNAVAILABLE: {counts.get('status', 'UNKNOWN')}"
    if isinstance(counts.get("cafe"), int):
        candidate.cafe_count = str(counts["cafe"])
    if candidate.blog_count:
        candidate.competition_total = candidate.blog_count
        monthly = parse_count(candidate.monthly_searches)
        if monthly:
            candidate.blog_competition_ratio = f"{int(candidate.blog_count) / monthly:.2f}"
            candidate.competition_ratio = candidate.blog_competition_ratio

    candidate.evidence_summary = summarize_evidence(
        autocomplete,
        [item.get("relKeyword", "") for item in searchad.get("related_keywords", [])],
    )
    candidate.intent_group = candidate.intent_group or keyword_intent_group(candidate.keyword)
    provisional = score_candidate(candidate)
    candidate.provisional_score = str(provisional)
    missing = missing_evidence(candidate, searchad, counts)
    candidate.missing_evidence = ", ".join(missing)
    if missing:
        candidate.analysis_status = "INCOMPLETE"
        candidate.score = ""
        candidate.recommended = "보류"
    else:
        candidate.analysis_status = "COMPLETE"
        candidate.score = str(provisional)
        if not has_target_intent(candidate):
            candidate.recommended = "본문 맥락" if candidate.selected else ""
        else:
            candidate.recommended = "추천" if provisional >= 8 else ("검토" if provisional >= 5 else "")
    candidate.scoring_basis = build_scoring_basis(candidate, searchad, counts)


def related_candidates(result: dict, briefing: Briefing) -> list[dict]:
    searchad = result.get("searchad") or {}
    out = []
    for item in searchad.get("related_keywords", [])[:12]:
        keyword = clean_text(str(item.get("relKeyword") or ""))
        if keyword and is_relevant_related_keyword(keyword, briefing):
            out.append({"keyword": keyword, "source": "searchad-related", "searchad_item": item})
    return out


def is_relevant_related_keyword(keyword: str, briefing: Briefing) -> bool:
    normalized = normalize_keyword(keyword)
    specific_anchors = relevance_anchors(briefing)
    if any(anchor and anchor in normalized for anchor in specific_anchors):
        return True
    destination_anchors = [
        normalize_keyword(value)
        for value in (briefing.destination, "상하이" if briefing.destination == "상해" else "", "상해" if briefing.destination == "상하이" else "")
        if value
    ]
    has_destination = any(anchor in normalized for anchor in destination_anchors)
    topic_intents = {
        "숙소": ("호텔", "숙소", "민박", "숙박", "호캉스", "게스트하우스", "펜션"),
        "맛집·카페": ("맛집", "카페", "식당", "레스토랑", "디저트", "파티세리", "베이커리", "메뉴", "웨이팅", "현지인맛집", "먹거리", "마라탕", "훠궈", "딤섬"),
        "관광지": ("가볼만한곳", "관광지", "명소", "코스", "입장료", "소요시간", "포토존", "가는법"),
        "교통": ("공항", "시내", "택시", "버스", "지하철", "교통", "이동", "가는법", "비용", "시간"),
        "쇼핑·구매": ("쇼핑", "쇼핑리스트", "추천템", "화장품", "약국", "가격", "택스리펀", "할인", "기념품"),
    }
    has_topic_intent = any(anchor in normalized for anchor in topic_intents.get(briefing.topic, ()))
    if has_destination and has_topic_intent:
        return True
    if briefing.topic == "교통":
        start = normalize_keyword(str(briefing.details.get("출발지") or ""))
        end = normalize_keyword(str(briefing.details.get("도착지") or ""))
        return bool(start and end and start in normalized and end in normalized)
    return False


def filter_result_related_keywords(result: dict, briefing: Briefing) -> None:
    searchad = result.get("searchad") or {}
    related = searchad.get("related_keywords") or []
    searchad["related_keywords"] = [
        item for item in related
        if is_relevant_related_keyword(str(item.get("relKeyword") or ""), briefing)
    ][:12]


def relevance_anchors(briefing: Briefing) -> list[str]:
    generic = {
        "호텔", "숙소", "민박", "추천", "후기", "가격", "위치", "조식", "가성비",
        "맛집", "카페", "식당", "메뉴", "웨이팅", "관광지", "가볼만한곳",
        "명소", "코스", "입장료", "소요시간", "포토존", "교통", "이동",
        "가는법", "택시", "버스", "지하철", "시내", "공항",
        "쇼핑", "쇼핑리스트", "추천템", "화장품", "약국", "택스리펀", "할인",
        "상하이", "상해", "상하이호텔위치추천", "상해호텔추천",
    }
    anchors = []
    subject = normalize_keyword(briefing.subject_name)
    for token in re.split(r"[\s·/()_-]+", briefing.subject_name):
        token = normalize_keyword(token)
        if len(token) >= 2 and token not in generic:
            anchors.append(token)
    for value in (briefing.details.get("메인 키워드", ""), briefing.details.get("서브 키워드", "")):
        for token in re.split(r"[,;\s]+", str(value)):
            token = normalize_keyword(token)
            if len(token) >= 2 and token not in generic:
                anchors.append(token)
    for value in (
        briefing.details.get("출발지", ""),
        briefing.details.get("도착지", ""),
        briefing.details.get("주문 메뉴·가격", ""),
        briefing.details.get("하이라이트", ""),
        briefing.details.get("구매 제품·가격", ""),
        briefing.details.get("주요 브랜드", ""),
        briefing.details.get("매장명/쇼핑 장소", ""),
    ):
        for token in re.split(r"[,;\s·/()_-]+", str(value)):
            token = normalize_keyword(token)
            if len(token) >= 2 and token not in generic:
                anchors.append(token)
    if subject and subject not in generic:
        anchors.append(subject)
    return list(dict.fromkeys(anchors))


def result_for_related(related: dict, base_result: dict) -> dict:
    result = {
        "keyword": related["keyword"],
        "autocomplete_terms": base_result.get("autocomplete_terms", []),
        "searchad": {
            "status": "OK",
            "exact": related.get("searchad_item") or {},
            "keywordList": [],
            "related_keywords": [],
        },
        "naver_search_api": {"status": "SKIPPED", "reason": "related keyword added from parent result; run full check to fetch counts"},
        "mobile_search": {"status": "SKIPPED", "blog_exposure": "UNKNOWN", "influencer_dominance": "UNKNOWN"},
        "memo": "Derived from parent keyword evidence.",
    }
    return result


def write_analysis(paths: Paths, keyword: str, result: dict) -> None:
    stem = safe_filename(keyword)
    analysis_path = paths.serp_dir / f"{stem}_analysis.json"
    analysis_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def build_scoring_basis(candidate: KeywordCandidate, searchad: dict, counts: dict) -> str:
    basis = [f"intent={candidate.intent_fit or 0}"]
    if candidate.monthly_searches:
        basis.append(f"monthly_searches={candidate.monthly_searches}")
    else:
        basis.append(f"searchad={searchad.get('status', 'UNKNOWN')}")
    if candidate.searchad_comp_idx:
        basis.append(f"searchad_comp_idx={candidate.searchad_comp_idx}")
    if candidate.blog_count or candidate.cafe_count:
        basis.append(f"blog={candidate.blog_count or 'UNKNOWN'}")
    else:
        basis.append(f"naver_search_api={counts.get('status', 'UNKNOWN')}")
    basis.append(f"autocomplete={candidate.autocomplete_seen}")
    basis.append(f"blog_exposure={candidate.blog_exposure}")
    basis.append(f"influencer_dominance={candidate.influencer_dominance}")
    if candidate.ai_summary_seen:
        basis.append(f"ai_summary_seen={candidate.ai_summary_seen}")
    if candidate.serp_exclusion_reason:
        basis.append(f"serp_exclusion_reason={candidate.serp_exclusion_reason}")
    if candidate.competition_ratio:
        basis.append(f"blog_competition_ratio={candidate.blog_competition_ratio or candidate.competition_ratio}")
    basis.append(f"analysis_status={candidate.analysis_status or 'UNKNOWN'}")
    if candidate.intent_group:
        basis.append(f"intent_group={candidate.intent_group}")
    return "; ".join(basis)


def search_volume_status(candidate: KeywordCandidate, searchad: dict) -> str:
    if candidate.monthly_searches:
        return "OK"
    status = searchad.get("status", "UNKNOWN")
    reason = searchad.get("reason") or searchad.get("error") or ""
    if status == "SKIPPED" and "NAVER_SEARCHAD_CUSTOMER_ID" in reason:
        return "MISSING_NAVER_SEARCHAD_CUSTOMER_ID"
    return f"UNAVAILABLE: {status}"


def missing_evidence(candidate: KeywordCandidate, searchad: dict, counts: dict) -> list[str]:
    missing: list[str] = []
    if not candidate.monthly_searches:
        missing.append(candidate.search_volume_status or "monthly_searches")
    if not candidate.blog_count:
        missing.append(candidate.blog_count_status or "blog_count")
    if not candidate.blog_competition_ratio:
        missing.append("blog_competition_ratio_requires_monthly_searches")
    return missing


def score_candidate(candidate: KeywordCandidate) -> int:
    # Keyword scoring is opportunity-first: once search volume is usable,
    # low blog/search competition should matter more than small volume gains.
    score = min(int(float(candidate.intent_fit or 0)), 3)
    monthly = parse_count(candidate.monthly_searches)
    if monthly >= 1000:
        score += 3
    elif monthly >= 500:
        score += 2
    elif monthly >= 100:
        score += 1
    elif monthly >= 50:
        score += 0
    elif monthly > 0:
        score -= 2
    else:
        score -= 4

    if candidate.blog_competition_ratio or candidate.competition_ratio:
        ratio = float(candidate.blog_competition_ratio or candidate.competition_ratio)
        if ratio < 10:
            score += 8
        elif ratio < 30:
            score += 6
        elif ratio < 60:
            score += 4
        elif ratio < 100:
            score += 2
        elif ratio < 200:
            score += 0
        elif ratio < 500:
            score -= 2
        else:
            score -= 5

    comp = candidate.searchad_comp_idx
    if comp in {"낮음", "LOW"}:
        score += 2
    elif comp in {"중간", "MEDIUM"}:
        score += 1
    elif comp in {"높음", "HIGH"}:
        score -= 1

    if candidate.autocomplete_seen == "O":
        score += 1
    if candidate.blog_exposure == "O":
        score += 1
    if candidate.influencer_dominance == "X":
        score += 1
    elif candidate.influencer_dominance == "O":
        score -= 5
        candidate.serp_exclusion_reason = "인플루언서 영역 우세: 현재 계정은 인플루언서 미선정이라 우선 제외"
    if candidate.ai_summary_seen == "O":
        score -= 1
    return max(score, 0)


def has_target_intent(candidate: KeywordCandidate) -> bool:
    if candidate.source == "workbook-main":
        return True
    keyword = candidate.keyword
    target_terms = (
        "호텔", "숙소", "후기", "추천", "조식", "객실", "예약", "가격",
        "맛집", "카페", "식당", "레스토랑", "디저트", "파티세리", "베이커리", "메뉴", "웨이팅",
        "관광지", "가볼만한곳", "입장료", "소요시간", "포토존",
        "이동", "가는법",
    )
    return any(term in keyword for term in target_terms)


def normalize_searchad_item(item: dict) -> dict:
    pc = normalize_searchad_count(item.get("monthlyPcQcCnt"))
    mobile = normalize_searchad_count(item.get("monthlyMobileQcCnt"))
    out = dict(item)
    out["monthlySearches"] = pc + mobile if pc is not None and mobile is not None else ""
    return out


def pick_searchad_item(keyword: str, items: list[dict]) -> dict:
    literal = normalize_literal_keyword(keyword)
    for item in items:
        if normalize_literal_keyword(str(item.get("relKeyword") or "")) == literal:
            return item
    normalized = normalize_keyword(keyword)
    for item in items:
        if normalize_keyword(str(item.get("relKeyword") or "")) == normalized:
            return item
    return items[0] if items else {}


def http_json(url: str, headers: dict | None = None) -> dict:
    return json.loads(http_text(url, headers=headers))


def http_text(url: str, headers: dict | None = None) -> str:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    req = Request(url, headers=request_headers)
    with urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8", "ignore")


def searchad_signature(timestamp: str, method: str, path: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{path}".encode("utf-8")
    secret = secret_key.encode("utf-8")
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def normalize_searchad_count(value) -> int | None:
    if isinstance(value, int):
        return value
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    if text.startswith("<"):
        return 0
    if text.isdigit():
        return int(text)
    return None


def parse_count(value: str) -> int:
    text = str(value or "").replace(",", "").strip()
    return int(text) if text.isdigit() else 0


def mark_seen(keyword: str, terms: list[str]) -> str:
    normalized = normalize_keyword(keyword)
    return "O" if any(normalize_keyword(term) == normalized for term in terms) else ("X" if terms else "UNKNOWN")


def summarize_evidence(*term_lists: list[str]) -> str:
    terms: list[str] = []
    for values in term_lists:
        for value in values:
            text = clean_text(str(value))
            if text and text not in terms:
                terms.append(text)
    return ", ".join(terms[:12])


def clean_terms(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if str(value).startswith("ERROR:"):
            continue
        text = clean_text(str(value))
        if text and text not in out:
            out.append(text)
    return out


def classify_blog_exposure(text: str) -> str:
    if re.search(r"블로그\s*(더보기|VIEW|리뷰|글)", text):
        return "O"
    if "블로그" in text or "VIEW" in text:
        return "UNKNOWN"
    return "X"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def string_value(value) -> str:
    return "" if value is None else str(value)


def safe_error_body(exc: HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", "ignore")[:500]
    except Exception:
        return str(exc)
