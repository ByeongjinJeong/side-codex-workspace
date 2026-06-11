from __future__ import annotations

import csv
from pathlib import Path

from .keyword_aliases import keyword_intent_group
from .models import Briefing, KeywordCandidate
from .paths import Paths


HIGH_INTENT_SUFFIXES = {
    "숙소": ["후기", "추천", "가격", "위치", "조식"],
    "맛집·카페": ["후기", "추천", "메뉴", "가격", "웨이팅"],
    "관광지": ["후기", "입장료", "소요시간", "포토존", "가는법"],
    "교통": ["이동", "가는법", "가격", "예약", "후기"],
    "쇼핑·구매": ["후기", "추천", "가격", "쇼핑리스트", "추천템"],
}

TOPIC_TERMS = {
    "숙소": ("호텔", "숙소", "펜션", "감성숙소", "가성비 숙소"),
    "맛집·카페": ("맛집", "카페", "식당", "레스토랑", "현지인 맛집", "먹거리"),
    "관광지": ("가볼만한곳", "관광지", "여행 코스", "포토존", "명소"),
    "교통": ("이동", "가는 법", "가는법", "교통", "택시", "공항버스", "지하철"),
    "쇼핑·구매": ("쇼핑", "쇼핑리스트", "추천템", "화장품", "기념품", "약국 쇼핑", "가격"),
}

QUESTION_INTENT_PATTERNS = {
    "숙소": (
        "{dest} 어디서 자면 좋을까",
        "{dest} 숙소 어디가 좋을까",
        "{dest} {subject} 예약 전 확인",
        "{dest} {subject} 실제 후기",
    ),
    "맛집·카페": (
        "{dest} 뭐 먹지",
        "{dest} 어디서 먹을까",
        "{dest} 현지인 맛집",
        "{dest} {subject} 맛집",
        "{dest} {subject} 후기",
        "{dest} {subject} 메뉴 추천",
    ),
    "관광지": (
        "{dest} 어디갈까",
        "{dest} 뭐하지",
        "{dest} 하루 코스",
        "{dest} {subject} 가는 법",
        "{dest} {subject} 소요시간",
        "{dest} {subject} 사진",
    ),
    "교통": (
        "{start}에서 {end}",
        "{start}에서 {end} 가는 법",
        "{start}에서 {end} 가는법",
        "{start}에서 {end} 택시",
        "{start}에서 {end} 비용",
        "{start}에서 {end} 시간",
        "{start} {end} 이동",
        "{dest} 공항에서 시내",
        "{dest} 공항에서 시내 가는 법",
        "{dest} 공항에서 시내 택시",
        "{dest} 공항 택시",
        "{dest} 공항 교통",
    ),
    "쇼핑·구매": (
        "{dest} 쇼핑리스트",
        "{dest} 쇼핑 추천",
        "{dest} 약국 쇼핑",
        "{dest} 약국 화장품",
        "{dest} 약국 추천템",
        "{dest} 화장품 쇼핑",
        "{dest} {subject} 후기",
        "{dest} {subject} 쇼핑리스트",
        "{dest} {subject} 가격",
    ),
}


def generate_keywords(briefing: Briefing) -> list[KeywordCandidate]:
    raw: list[tuple[str, str]] = []
    if briefing.target_keyword:
        raw.append((briefing.target_keyword, "workbook"))
    if briefing.details.get("메인 키워드"):
        raw.append((briefing.details["메인 키워드"], "workbook-main"))
    for keyword in split_keywords(str(briefing.details.get("서브 키워드") or "")):
        raw.append((keyword, "workbook-sub"))

    dest = briefing.destination
    dest_variants = destination_variants(dest)
    subject = briefing.subject_name
    topic = briefing.topic
    sub_keywords = split_keywords(str(briefing.details.get("서브 키워드") or ""))
    raw.extend(topic_keyword_candidates(briefing))

    if dest and subject and subject != dest:
        subject_phrase = subject_without_destination(subject, dest)
        raw.extend([
            (f"{dest} {subject_phrase}", "destination+subject"),
            (f"{subject} 후기", "subject+review"),
            (f"{dest} {subject_phrase} 후기", "destination+subject+review"),
            (f"{dest} {topic} 추천", "destination+topic"),
        ])
        if topic == "숙소":
            for city in dest_variants:
                raw.append((f"{city} 호텔 추천", "article-seed"))
                raw.append((f"{city} 숙소 추천", "article-seed"))
                raw.append((f"{city} 호텔 위치 추천", "article-seed"))
                raw.append((f"{city} 숙소 위치 추천", "article-seed"))
                if any("가성비" in item for item in sub_keywords):
                    raw.append((f"{city} 가성비 호텔", "article-seed"))
                    raw.append((f"{city} 가성비 숙소", "article-seed"))
                    raw.append((f"{city} 가성비 호텔 추천", "article-seed"))
                    raw.append((f"{city} 가성비 숙소 추천", "article-seed"))
                    raw.append((f"{city} 호텔 추천 가성비", "article-seed"))
        if any("난징동루" in item for item in sub_keywords):
            raw.extend([
                ("난징동루 호텔", "article-seed"),
                ("난징동루 숙소", "article-seed"),
                ("난징동루 호텔 추천", "article-seed"),
                ("난징동루 숙소 추천", "article-seed"),
            ])
            for city in dest_variants:
                raw.append((f"{city} 난징동루 호텔", "article-seed"))
                raw.append((f"{city} 난징동루 숙소", "article-seed"))
        for suffix in HIGH_INTENT_SUFFIXES.get(topic, []):
            raw.append((f"{subject} {suffix}", "subject+intent"))
            raw.append((f"{dest} {subject_phrase} {suffix}", "destination+subject+intent"))
    elif dest:
        raw.extend([
            (f"{dest} {topic} 추천", "destination+topic"),
            (f"{dest} 여행 {topic}", "destination+travel+topic"),
        ])
        for suffix in HIGH_INTENT_SUFFIXES.get(topic, []):
            raw.append((f"{dest} {topic} {suffix}", "destination+topic+intent"))

    if topic == "숙소":
        raw.extend([(f"{dest} 호텔 추천", "topic-default"), (f"{dest} 숙소 추천", "topic-default")])
    elif topic == "맛집·카페":
        food_kind = food_article_kind(briefing)
        raw.append((f"{dest} 맛집", "topic-default"))
        if food_kind == "restaurant":
            raw.append((f"{dest} 레스토랑 추천", "topic-default"))
        else:
            raw.append((f"{dest} 카페 추천", "topic-default"))
    elif topic == "관광지":
        raw.extend([(f"{dest} 가볼만한곳", "topic-default"), (f"{dest} 관광지 추천", "topic-default")])
    elif topic == "교통":
        start = briefing.details.get("출발지", "")
        end = briefing.details.get("도착지", "")
        if start and end:
            raw.extend([(f"{start} {end} 이동", "transit-route"), (f"{start}에서 {end}", "transit-route")])
    elif topic == "쇼핑·구매":
        raw.extend([(f"{dest} 쇼핑리스트", "topic-default"), (f"{dest} 쇼핑 추천", "topic-default")])

    seen = set()
    candidates = []
    for keyword, source in raw:
        keyword = " ".join(str(keyword).split())
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        selected = "Y" if source in {"workbook-main", "workbook-sub"} else ("O" if keyword == briefing.target_keyword else "")
        candidate = KeywordCandidate(keyword=keyword, source=source, selected=selected)
        candidate.intent_group = keyword_intent_group(keyword)
        apply_initial_intent_score(candidate, briefing)
        candidates.append(candidate)
    rank_keywords(candidates)
    return candidates


def topic_keyword_candidates(briefing: Briefing) -> list[tuple[str, str]]:
    dest = briefing.destination
    subject = briefing.subject_name
    topic = briefing.topic
    start = str(briefing.details.get("출발지") or "")
    end = str(briefing.details.get("도착지") or "")
    memo = briefing.memo
    details_text = " ".join(str(value) for value in briefing.details.values())
    seeds = extract_user_keyword_phrases(" ".join([memo, details_text]))

    raw: list[tuple[str, str]] = []
    for keyword in seeds:
        raw.append((keyword, "memo-seed"))

    for city in destination_variants(dest):
        for term in topic_terms_for_briefing(briefing):
            raw.append((f"{city} {term}", "topic-term"))
            if term not in {"추천템", "가격"}:
                raw.append((f"{city} {term} 추천", "topic-term+recommend"))

    for pattern in QUESTION_INTENT_PATTERNS.get(topic, ()):
        if "{subject}" in pattern and (not subject or subject == dest):
            continue
        if ("{start}" in pattern or "{end}" in pattern) and (not start or not end):
            continue
        keyword = pattern.format(
            dest=dest,
            subject=subject_without_destination(subject, dest),
            start=start,
            end=end,
        )
        raw.append((keyword, "question-intent"))

    if topic == "교통":
        for route_start, route_end in transit_route_variants(dest, start, end):
            raw.extend([
                (f"{route_start}에서 {route_end}", "transit-natural"),
                (f"{route_start}에서 {route_end} 가는 법", "transit-natural"),
                (f"{route_start}에서 {route_end} 택시", "transit-natural"),
                (f"{route_start}에서 {route_end} 교통", "transit-natural"),
                (f"{route_start} {route_end} 이동", "transit-route"),
            ])

    if topic == "관광지" and subject and subject != dest:
        raw.extend([
            (f"{subject} 가는 법", "spot-natural"),
            (f"{subject} 입장료", "spot-natural"),
            (f"{subject} 소요시간", "spot-natural"),
            (f"{dest} {subject} 코스", "spot-natural"),
        ])

    if topic == "맛집·카페":
        menu_terms = extract_food_terms(details_text)
        for menu in menu_terms:
            for city in destination_variants(dest):
                raw.extend([
                    (f"{city} {menu}", "food-menu"),
                    (f"{city} {menu} 맛집", "food-menu"),
                    (f"{city} {menu} 추천", "food-menu"),
                ])
        if subject and subject != dest:
            raw.extend([
                (f"{subject} 메뉴", "food-subject"),
                (f"{subject} 웨이팅", "food-subject"),
                (f"{subject} 가격", "food-subject"),
            ])

    if topic == "쇼핑·구매":
        shopping_terms = extract_shopping_terms(details_text)
        for term in shopping_terms:
            for city in destination_variants(dest):
                raw.extend([
                    (f"{city} {term}", "shopping-term"),
                    (f"{city} {term} 추천", "shopping-term"),
                    (f"{city} {term} 가격", "shopping-term"),
                ])
        if subject and subject != dest:
            raw.extend([
                (f"{subject} 쇼핑", "shopping-subject"),
                (f"{subject} 추천템", "shopping-subject"),
                (f"{subject} 가격", "shopping-subject"),
            ])

    return raw


def topic_terms_for_briefing(briefing: Briefing) -> tuple[str, ...]:
    if briefing.topic != "맛집·카페":
        return TOPIC_TERMS.get(briefing.topic, ())
    kind = food_article_kind(briefing)
    if kind == "restaurant":
        return ("맛집", "식당", "레스토랑", "현지인 맛집", "먹거리")
    if kind == "dessert":
        return ("맛집", "카페", "디저트 맛집", "파티세리", "베이커리", "먹거리")
    return TOPIC_TERMS["맛집·카페"]


def food_article_kind(briefing: Briefing) -> str:
    ignored_fields = {
        "메인 키워드", "서브 키워드", "키워드 판단 근거", "키워드 실험 방향",
        "이미지 추가 메모", "작성 판단 로그", "초안 파일명",
    }
    detail_values = [
        value for key, value in briefing.details.items()
        if key not in ignored_fields
    ]
    text = " ".join(str(value) for value in [briefing.subject_name, briefing.memo, *detail_values]).lower()
    dessert_terms = ("카페", "디저트", "파티세리", "베이커리", "에끌레어", "케이크", "빵", "과일 디저트")
    restaurant_terms = ("레스토랑", "식당", "저녁", "코스", "코스요리", "스테이크", "문어", "와인", "에피타이저", "메인")
    if any(term in text for term in restaurant_terms):
        return "restaurant"
    if any(term in text for term in dessert_terms):
        return "dessert"
    return "mixed"


def transit_route_variants(destination: str, start: str, end: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if start and end:
        pairs.append((start, end))
    if destination:
        airport_terms = [term for term in (start, end) if "공항" in term]
        if airport_terms:
            for airport in airport_terms:
                pairs.append((airport, "시내"))
                pairs.append((airport, f"{destination} 시내"))
        else:
            pairs.append((f"{destination} 공항", "시내"))
    return list(dict.fromkeys(pairs))


def subject_without_destination(subject: str, destination: str) -> str:
    subject = " ".join(str(subject or "").split())
    destination = " ".join(str(destination or "").split())
    if destination and subject.startswith(destination + " "):
        return subject[len(destination):].strip()
    return subject


def extract_user_keyword_phrases(text: str) -> list[str]:
    phrases: list[str] = []
    for quoted in text.replace("'", '"').split('"')[1::2]:
        phrase = " ".join(quoted.split())
        if 2 <= len(phrase) <= 30:
            phrases.append(phrase)
    for marker in ("키워드:", "검색어:", "후보:"):
        if marker in text:
            tail = text.split(marker, 1)[1]
            for token in split_keywords(tail.split("/")[0]):
                if 2 <= len(token) <= 30:
                    phrases.append(token)
    return list(dict.fromkeys(phrases))


def extract_food_terms(text: str) -> list[str]:
    common_food_terms = [
        "마라탕", "훠궈", "딤섬", "샤오롱바오", "양꼬치", "우육면",
        "커피", "디저트", "브런치", "베이커리", "케이크",
    ]
    return [term for term in common_food_terms if term in text]


def extract_shopping_terms(text: str) -> list[str]:
    common_terms = [
        "약국", "화장품", "몽쥬약국", "시티파르마", "라로슈포제", "유리아쥬",
        "눅스", "꼬달리", "비오더마", "아벤느", "비쉬", "달팡", "기념품",
        "택스리펀", "할인", "쇼핑리스트", "추천템",
    ]
    return [term for term in common_terms if term.lower() in text.lower()]


def apply_initial_intent_score(candidate: KeywordCandidate, briefing: Briefing) -> None:
    score = 0
    keyword = candidate.keyword
    dest_variants = destination_variants(briefing.destination)
    if any(dest and dest in keyword for dest in dest_variants):
        score += 2

    if any(term in keyword for term in TOPIC_TERMS.get(briefing.topic, ())):
        score += 2
    if any(term in keyword for term in ("가는 법", "가는법", "어디", "뭐", "시내", "비용", "시간")):
        score += 1

    if briefing.subject_name and briefing.subject_name != briefing.destination and briefing.subject_name in keyword:
        score += 1

    user_modifiers = split_keywords(str(briefing.details.get("서브 키워드") or ""))
    if any(modifier and modifier in keyword for modifier in user_modifiers):
        score += 1

    if any(term in keyword for term in HIGH_INTENT_SUFFIXES.get(briefing.topic, [])):
        score += 1
    candidate.intent_fit = str(score)
    candidate.provisional_score = str(score)
    candidate.score = ""
    candidate.analysis_status = "NEEDS_EVIDENCE"
    candidate.recommended = "근거 확인 필요" if score >= 4 else ""
    candidate.scoring_basis = f"initial intent score={score}; evidence enrichment not run yet"


def rank_keywords(candidates: list[KeywordCandidate]) -> None:
    for candidate in candidates:
        if candidate.source == "workbook-main":
            if user_keyword_has_search_basis(candidate):
                candidate.role = "메인(사용자 지정)"
            else:
                candidate.role = "메인(사용자 지정·검색량 재검토)"
        elif candidate.source == "workbook-sub":
            candidate.role = "서브(사용자 지정)"

    has_user_main = any(
        item.source == "workbook-main" and user_keyword_has_search_basis(item)
        for item in candidates
    )
    has_user_sub = any(item.source == "workbook-sub" for item in candidates)
    ranked = [
        item for item in candidates
        if item.source not in {"workbook-main", "workbook-sub"}
        and item.analysis_status == "COMPLETE"
    ]
    ranked.sort(key=lambda item: numeric(item.score), reverse=True)
    for idx, candidate in enumerate(ranked):
        if idx == 0 and not candidate.role and not has_user_main:
            candidate.role = "메인 후보"
        elif idx <= 2 and not candidate.role and not has_user_sub:
            candidate.role = "서브 후보"


def user_keyword_has_search_basis(candidate: KeywordCandidate) -> bool:
    if candidate.analysis_status != "COMPLETE":
        return False
    monthly = numeric(candidate.monthly_searches)
    return monthly >= 50


def numeric(value: str) -> float:
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0


def split_keywords(value: str) -> list[str]:
    out: list[str] = []
    for token in value.replace(";", ",").split(","):
        keyword = " ".join(token.split())
        if keyword:
            out.append(keyword)
    return out


def destination_variants(destination: str) -> list[str]:
    base = " ".join(str(destination or "").split())
    variants = []
    if base:
        variants.append(base)
    if base == "상하이":
        variants.append("상해")
    elif base == "상해":
        variants.append("상하이")
    return list(dict.fromkeys(variants))


def write_keywords_csv(paths: Paths, keywords: list[KeywordCandidate]) -> Path:
    out = paths.article_file("keywords.csv")
    fields = [
        "keyword", "source", "intent_group", "monthly_pc_searches", "monthly_mobile_searches", "monthly_searches",
        "blog_count", "cafe_count", "competition_total", "competition_ratio", "blog_competition_ratio", "searchad_comp_idx",
        "monthly_pc_ctr", "monthly_mobile_ctr", "pl_avg_depth", "blog_exposure", "influencer_dominance", "ai_summary_seen", "autocomplete_seen",
        "related_seen", "recommended_seen", "ai_question_seen", "intent_fit", "provisional_score", "score",
        "recommended", "selected", "role", "analysis_status", "search_volume_status", "blog_count_status",
        "missing_evidence", "serp_exclusion_reason", "evidence_summary", "scoring_basis", "memo",
    ]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in keywords:
            writer.writerow(item.__dict__)
    return out
