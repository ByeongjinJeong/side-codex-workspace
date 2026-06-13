---
name: mailz-figma-detail
description: Build and maintain MAILZ Korean product detail pages in Figma from the local longjane_mailz product folders. Use when working on MAILZ hat 상세페이지, Figma detail-page frames, confirmed Korean product copy, crop photos, specs, care text, or reference designs from the MAILZ Figma files.
---

# MAILZ Figma Detail Page

Use this skill for MAILZ product 상세페이지 work in Figma.

The source project is local and asset-heavy. Do not copy or push product image
outputs into Git unless the user explicitly asks for an asset backup.

```text
/Users/longjane/Desktop/workspace/longjane_mailz
```

The side-codex repo tracks workflow, guides, and reusable skill logic only.

## Core Rules

- Use confirmed product copy from `문안/*_상세페이지_문안_확정본.md`.
- Do not invent specs, care text, material, size, color, origin, components, or measurements.
- Never write placeholder copy such as `상세 이미지 참조`, `입력 필요`, `확인 필요`, or `추후 확인`.
- If confirmed copy is missing, stop and report the missing field instead of filling it casually.
- Use real local product photos from `크롭사진/` or `원본/` as source material, but do not commit those assets to side-codex.
- Keep Figma output as a long-form mobile commerce detail page, not a web app, landing page, or report.

## Local Project Layout

Current product folder pattern:

```text
longjane_mailz/
  모자/
    001. 울프컷 똑딱이 빅챙 모자/
      문안/
      원본/
      크롭사진/
    002. 체크턱끈모자/
      문안/
      원본/
      크롭사진/
```

For each product:

1. Read the confirmed copy markdown first.
2. Inspect `크롭사진/` filenames and choose image slots from actual files.
3. Use `원본/` only when crop photos are insufficient.
4. Keep original photo files untouched.

## Figma Workflow

Use the Figma MCP tools with `figma-use` whenever editing Figma.

1. Read the target Figma file and page/frame structure.
2. If the user references a previous product design, inspect that Figma file first.
3. Create or update a 1500px-wide 상세페이지 frame.
4. Build sections from confirmed copy and local product photo names.
5. Run a text QA pass in Figma:
   - no placeholder phrases
   - product specs present
   - care text present
   - section titles not clipped
   - no text overlap with photos, bars, stamps, or tables
6. Screenshot-check the final frame before reporting completion.

Known Figma files:

```text
001 똑딱이 빅챙 모자 reference:
fileKey xVqwlLPhsf9CqDEytiRyvI

002 체크턱끈모자:
fileKey lxlW0fPQnPXZnGyFFMR1wG
```

Use the rightmost/reference design from 001 when the user asks to apply the
`똑딱이모자 맨 오른쪽 디자인`.

## Design Direction

Reference style from the 001 rightmost design:

- 1500px-wide commerce-detail canvas.
- White base with hot-pink hook bars.
- Large black headline typography.
- `Customer PICK` block with customer concerns.
- Pink `해결` stamps.
- Three benefit cards.
- Real product photos as proof, not decorative placeholders.
- Product information and care information at the end.

Avoid:

- App-like controls or navigation.
- Generic landing-page hero layouts.
- Cards inside cards.
- Overusing pink as the full-page background.
- Tiny legal/spec text that is unreadable at commerce-page scale.

## Typography

Target fonts from the 001 reference:

```text
Gmarket Sans / Bold
NanumSquare / Bold
Griun Myoeun ddobak / Regular
Inter / Semi Bold
```

Important Figma MCP limitation:

- Figma Desktop may show local fonts while `figma.loadFontAsync()` in MCP fails.
- Existing text layers can report fonts that the plugin runtime still cannot load.
- Do not assume a font is usable until `figma.loadFontAsync({ family, style })` succeeds.
- If the three MAILZ fonts fail to load, build with accessible fallback fonts first and report the font blocker clearly.
- The proper fix is uploading those fonts in Figma:
  `File browser > avatar > Settings > Account > Your uploaded fonts > Upload fonts`.

Do not ask the user to manually style the whole page. Manual work should only be
needed for account-level font upload or macOS permissions that the agent cannot
perform.

## Confirmed 002 Copy

For `002. 체크턱끈모자`, use the confirmed markdown in:

```text
/Users/longjane/Desktop/workspace/longjane_mailz/모자/002. 체크턱끈모자/문안/002_상세페이지_문안_확정본.md
```

Essential product information:

```text
상품명: 체크턱끈모자
색상: 핑크, 블랙, 베이지
사이즈: 프리 사이즈
소재: 코튼 60%, 나일론 20%, 폴리 20%
제조국: 중국
구성: 모자 1개
턱끈: 체크 리본끈 겸용
챙 와이어: 있음
챙 길이: 약 9.5cm
뒷챙 길이: 앞챙과 동일
머리 둘레: 약 56.5cm
높이: 약 9.5cm
```

Care summary:

```text
세탁 라벨 기준
손세탁 가능 / 표백 금지 / 드라이클리닝 금지 / 건조기 사용 금지
```

Use the full confirmed caution text from the markdown, not a shortened
placeholder, when building the final care section.

## QA Checklist

Before reporting done:

- Search all Figma text for `상세 이미지 참조`, `입력 필요`, `확인 필요`, `추후`.
- Verify every product spec from the confirmed markdown is represented.
- Verify final care instructions match the confirmed markdown.
- Confirm font load results if exact fonts were requested.
- Confirm the target frame name and node id.
- Mention any Figma account-level blocker separately from design completion.

