from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Briefing:
    id: str
    topic: str
    sheet: str
    common: dict[str, Any]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def destination(self) -> str:
        return str(self.common.get("여행지") or "")

    @property
    def target_keyword(self) -> str:
        return str(self.common.get("목표 키워드") or "")

    @property
    def status(self) -> str:
        return str(self.common.get("상태") or "")

    @property
    def memo(self) -> str:
        return str(self.common.get("자유 메모") or "")

    @property
    def subject_name(self) -> str:
        for key in ("숙소명", "식당/카페명", "관광지명", "이용 수단", "매장명/쇼핑 장소"):
            if self.details.get(key):
                return str(self.details[key])
        if self.details.get("출발지") and self.details.get("도착지"):
            return f"{self.details['출발지']} to {self.details['도착지']}"
        return self.destination


@dataclass
class KeywordCandidate:
    keyword: str
    source: str
    intent_group: str = ""
    monthly_pc_searches: str = ""
    monthly_mobile_searches: str = ""
    monthly_searches: str = ""
    blog_count: str = ""
    cafe_count: str = ""
    competition_total: str = ""
    competition_ratio: str = ""
    blog_competition_ratio: str = ""
    searchad_comp_idx: str = ""
    monthly_pc_ctr: str = ""
    monthly_mobile_ctr: str = ""
    pl_avg_depth: str = ""
    blog_exposure: str = ""
    influencer_dominance: str = ""
    ai_summary_seen: str = ""
    autocomplete_seen: str = ""
    related_seen: str = ""
    recommended_seen: str = ""
    ai_question_seen: str = ""
    intent_fit: str = ""
    provisional_score: str = ""
    score: str = ""
    recommended: str = ""
    selected: str = ""
    role: str = ""
    analysis_status: str = ""
    search_volume_status: str = ""
    blog_count_status: str = ""
    missing_evidence: str = ""
    serp_exclusion_reason: str = ""
    evidence_summary: str = ""
    scoring_basis: str = ""
    memo: str = ""


@dataclass
class PhotoItem:
    index: int
    path: Path
    filename: str
    marker: str
    caption: str = ""
    status: str = "ready"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data


@dataclass
class SerpCheckResult:
    keyword: str
    blog_exposure: str = "UNKNOWN"
    influencer_dominance: str = "UNKNOWN"
    screenshot: str = ""
    html: str = ""
    memo: str = ""
