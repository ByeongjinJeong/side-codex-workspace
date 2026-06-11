from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    project: Path
    article_id: str | None = None

    def __post_init__(self) -> None:
        project = self.project.resolve()
        if not (project / "longjane_blog_briefing.xlsx").exists() and not (
            project / "longjane_blog_briefing.xlsm"
        ).exists():
            review_project = project / "후기성"
            if (review_project / "longjane_blog_briefing.xlsx").exists() or (
                review_project / "longjane_blog_briefing.xlsm"
            ).exists():
                project = review_project
        object.__setattr__(self, "project", project)

    @property
    def workbook(self) -> Path:
        xlsx = self.project / "longjane_blog_briefing.xlsx"
        if xlsx.exists():
            return xlsx
        return self.project / "longjane_blog_briefing.xlsm"

    @property
    def persona_html(self) -> Path:
        return self.project / "longjane_persona_v3_flexible.html"

    @property
    def photos_root(self) -> Path:
        return self.project / "photos"

    @property
    def drafts_root(self) -> Path:
        return self.project / "drafts"

    @property
    def photo_dir(self) -> Path:
        self._require_id()
        return self.photos_root / str(self.article_id)

    @property
    def draft_dir(self) -> Path:
        self._require_id()
        return self.drafts_root / str(self.article_id)

    @property
    def serp_dir(self) -> Path:
        return self.draft_dir / "serp"

    def ensure_article_dirs(self) -> None:
        self.draft_dir.mkdir(parents=True, exist_ok=True)
        self.serp_dir.mkdir(parents=True, exist_ok=True)

    def article_file(self, suffix: str) -> Path:
        self._require_id()
        return self.draft_dir / f"{self.article_id}_{suffix}"

    def _require_id(self) -> None:
        if not self.article_id:
            raise ValueError("article_id is required for this path")


def safe_filename(value: str) -> str:
    allowed = []
    for ch in value.strip():
        if ch.isalnum() or ch in ("-", "_"):
            allowed.append(ch)
        elif ch.isspace():
            allowed.append("-")
    out = "".join(allowed).strip("-")
    return out or "keyword"
