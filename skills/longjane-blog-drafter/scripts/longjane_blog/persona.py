from __future__ import annotations

from pathlib import Path


DEFAULT_PERSONA = {
    "name": "절약형 여행 블로거 롱제인",
    "greeting": "안녕하세요, 절약형 여행 블로거 롱제인입니다 ✈️",
    "voice": [
        "1인칭 캐주얼 존댓말",
        "`~습니다`, `~했습니다`, `~좋겠습니다` 같은 딱딱한 문어체보다 `~해요`, `~했어요`, `~좋아요`, `~추천해요`를 기본으로 사용",
        "정보 전달이나 안전 주의 문구도 너무 공식적으로 쓰지 말고 블로그 대화체로 자연스럽게 설명",
        "남편과 함께한 부부 여행 맥락 자연스럽게 포함",
        "가성비와 절약 포인트를 솔직하게 평가",
        "모바일에서 읽기 좋은 짧은 단락",
    ],
}


def load_persona(_path: Path | None = None) -> dict:
    # v1 uses the distilled persona in references/persona-and-formats.md.
    # Keep this function as the future extension point for HTML parsing.
    return DEFAULT_PERSONA.copy()
