from __future__ import annotations

import json
from pathlib import Path

from .models import Briefing, KeywordCandidate, PhotoItem
from .paths import Paths
from .persona import load_persona


def build_context(paths: Paths, briefing: Briefing, keywords: list[KeywordCandidate], photos: list[PhotoItem]) -> Path:
    persona = load_persona(paths.persona_html)
    briefing_path = paths.article_file("briefing.json")
    briefing_path.write_text(json.dumps(briefing.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    out = paths.article_file("draft_context.md")
    lines = [
        f"# Draft Context: {briefing.id}",
        "",
        "## Persona",
        "",
        persona["greeting"],
        "",
        *[f"- {rule}" for rule in persona["voice"]],
        "",
        "## Briefing",
        "",
        f"- ID: {briefing.id}",
        f"- Topic: {briefing.topic}",
        f"- Destination: {briefing.destination}",
        f"- Subject: {briefing.subject_name}",
        f"- Target keyword: {briefing.target_keyword or '(not set)'}",
        f"- Status: {briefing.status or '(not set)'}",
        f"- Memo: {briefing.memo or '(none)'}",
        "",
        "### Common Fields",
        "",
    ]
    for key, value in briefing.common.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "### Detail Fields", ""])
    for key, value in briefing.details.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Keyword Candidates", ""])
    for item in keywords:
        selected = " selected" if item.selected == "O" else ""
        lines.append(f"- {item.keyword} ({item.source}){selected}")

    lines.extend(["", "## Photos", ""])
    if photos:
        for photo in photos:
            lines.append(f"- {photo.marker} {photo.filename}")
    else:
        lines.append("- No local photos found. Write a text-centered draft.")

    lines.extend(["", "## Required Draft Output", ""])
    lines.append(f"Write the article markdown to `drafts/{briefing.id}/{briefing.id}_draft.md`.")
    topic_guidance = topic_draft_guidance(briefing.topic)
    if topic_guidance:
        lines.extend(["", "## Topic-Specific Writing Checklist", ""])
        lines.extend([f"- {item}" for item in topic_guidance])
        lines.append("")
    lines.append("After the greeting, include a numbered `목차`, ideally 5 items, and align main section headings to those numbers.")
    lines.append("Use casual polite Korean as the default: prefer `~해요`, `~했어요`, `~좋아요`, `~추천해요` over formal `~습니다` endings. Keep `~습니다` only when it is the fixed greeting or when a sentence truly needs a formal notice tone.")
    lines.append("Use mobile-centered short line breaks: usually one sentence per line, with blank lines between visual paragraphs.")
    lines.append("Use `[PHOTO: 01]` style markers where an image should appear; keep images out of the Word file.")
    lines.append(f"Still select photos and create `photos/{briefing.id}/ordered_photos/` with sequential descriptive filenames.")
    lines.append("Never rename or move original photos. If source photos are JPEG/JPG, copy selected originals as-is without resizing or converting.")
    lines.append("Ignore video files such as MOV/MP4/M4V; leave them untouched and exclude them from photo ordering.")
    lines.append("For sponsored stay reviews, do not publish satisfaction scores or sponsorship/internal workflow notes.")
    lines.append("The renderer will create the Word file afterward.")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def topic_draft_guidance(topic: str) -> list[str]:
    return {
        "맛집·카페": [
            "Lead with the most memorable first bite, ordering moment, wait, seat, or local atmosphere.",
            "Cover ordered menu, price, waiting, value, revisit fit, and who would enjoy it.",
            "Use menu names and price details as practical reader guidance, not just a list.",
        ],
        "관광지": [
            "Lead with the strongest scene: route, view, photo moment, crowd level, weather, or time of day.",
            "Cover entrance fee, actual time spent, visit time, crowd level, highlight, route tips, and photo points.",
            "Frame limitations as timing, route, or audience-fit tips.",
        ],
        "교통": [
            "Lead with the travel tension or relief moment: luggage, family movement, airport arrival, transfer, or cost choice.",
            "Cover start/end point, transport method, actual fare, booking/payment, actual duration, luggage, and where readers may get confused.",
            "Compare alternatives only where it helps explain why this route was chosen.",
        ],
        "쇼핑·구매": [
            "Lead with the shopping decision: why this shop/category was worth visiting and what readers should buy or skip.",
            "Cover store/place, visit time, brands, product names, product use/effect, price, discount/tax refund, and repurchase fit.",
            "Group products by reader need such as sensitive skin, gift, pregnancy-safe check, daily skincare, or value pick when the brief supports it.",
            "Do not overclaim cosmetic effects; phrase benefits as observed use, product positioning, or package/label guidance unless the brief gives stronger evidence.",
        ],
    }.get(topic, [])
