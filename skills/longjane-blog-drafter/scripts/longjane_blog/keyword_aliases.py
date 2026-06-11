from __future__ import annotations

import re


# Travel keywords often mix official names, Korean nicknames, English names,
# romanization, and Konglish. Keep raw keyword metrics separate, but compare
# final opportunities by this semantic group.
SEMANTIC_ALIASES = {
    "상해": "상하이",
    "샹하이": "상하이",
    "shanghai": "상하이",
    "난징동루": "난징둥루",
    "난징동로": "난징둥루",
    "난징 이스트 로드": "난징둥루",
    "nanjing east road": "난징둥루",
    "와이탄": "외탄",
    "번드": "외탄",
    "the bund": "외탄",
    "인민광장": "런민광장",
    "people's square": "런민광장",
    "peoples square": "런민광장",
    "푸동": "푸둥",
    "pudong": "푸둥",
    "신천지": "신톈디",
    "xintiandi": "신톈디",
}


def keyword_intent_group(keyword: str) -> str:
    text = " ".join(str(keyword or "").split()).lower()
    for alias in sorted(SEMANTIC_ALIASES, key=len, reverse=True):
        text = text.replace(alias, SEMANTIC_ALIASES[alias])
    return text


def normalize_keyword(keyword: str) -> str:
    return keyword_intent_group(keyword).replace(" ", "")


def normalize_literal_keyword(keyword: str) -> str:
    return re.sub(r"\s+", "", str(keyword or "").lower())
