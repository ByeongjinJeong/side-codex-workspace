---
name: longjane-blog-drafter
description: Draft and maintain Longjane-style Korean travel blog posts from local XLSX briefings, local photos, keyword/SERP checks, and Word docx outputs. Use when processing longjane_blog_briefing.xlsx, photos/{ID}, drafts/{ID}, Naver keyword checks, or the Longjane blog automation harness.
---

# Longjane Blog Drafter

Use this skill to create a review-ready Longjane travel blog draft from a local workbook and local photo folders. Keep publishing manual; do not automate Naver Blog posting.

When the user asks to write drafts from the briefing sheet, treat rows whose status is `작성 시작` as ready and run the full pipeline. As soon as work begins, set the workbook status to `초안 작성 중` so interrupted work can be recovered. Do not stop at writing prose.

Keep visit-review content and information-roundup content separate inside the project. In `longjane_blog_auto`, the existing visit/photo-based process lives under `후기성/`, and the new information-centered process lives under `정보성/`.

```text
longjane_blog_auto/
  후기성/
    longjane_blog_briefing.xlsx
    photos/
    drafts/
  정보성/
    longjane_info_briefing.xlsx
    drafts/
    cardnews/
    sources/
```

The existing harness is visit-review oriented. It can still be run from the outer `longjane_blog_auto` folder because the path layer falls back to `후기성/` when the workbook is not found at the outer root. Prefer running visit-review commands with `--project 후기성` or from inside `후기성` for clarity. Use `정보성` for separate manual or future automated info-roundup drafting; do not add info-roundup rows to the visit-review workbook.

## Workflow

1. Locate the project root containing `longjane_blog_briefing.xlsx` (`longjane_blog_briefing.xlsm` is accepted as a fallback when no `.xlsx` file exists).
2. Run the harness prepare step:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py prepare --project <project-root> --id <ID>
```

The prepare step updates the workbook row from `작성 시작` to `초안 작성 중`.

3. Read `drafts/{ID}/{ID}_draft_context.md`.
4. Review local photos under `photos/{ID}/`, select article photos, and create `photos/{ID}/ordered_photos/` with sequential, descriptive filenames. Keep original photos untouched. Never rename or move originals; copy selected files into `ordered_photos` and rename only the copies. If the user provides `.jpg`/`.jpeg` files, copy selected JPEGs as-is without resizing or converting. Ignore video files such as `.mov`, `.mp4`, and `.m4v`; do not analyze, convert, thumbnail, rename, copy, or organize them.
5. Write `drafts/{ID}/{ID}_photo_plan.md` mapping every `[PHOTO: NN]` marker to the ordered photo filename.
6. Write the Korean draft in Longjane's voice to `drafts/{ID}/{ID}_draft.md`.
7. Render Word:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py render --project <project-root> --id <ID> --draft drafts/{ID}/{ID}_draft.md
```

8. Verify:
   - The number of `[PHOTO: NN]` markers matches `photos/{ID}/ordered_photos/`.
   - The `.docx` contains no embedded image media.
   - The public draft does not contain internal work notes or sponsorship disclosure wording unless the user explicitly asks for it.
9. Update the workbook row: after Word rendering, `상태` is set to `초안 완료`; fill `메인 키워드`, `서브 키워드`, `키워드 판단 근거`, `이미지 추가 메모`, and `작성 판단 로그` when those columns exist.
10. Report generated `.md`, `.docx`, `photo_plan.md`, and `ordered_photos` paths plus any warnings.

## Info-Roundup Workflow

Use the `정보성` track for search-answer posts that can be written without a direct visit. These posts collect practical information readers need before planning a trip: weather by month, best travel seasons, museum lists, transit-pass choices, packing lists, budget summaries, itinerary comparisons, booking rules, and city-by-city guides.

Examples:

- `파리 9월 날씨`
- `파리 가볼만한 박물관 5곳 정리`
- `파리 교통권 정리`
- `중국 여행가기 좋은 시기`

Use `정보성/longjane_info_briefing.xlsx` as the separate briefing source. Recommended columns are `ID`, `여행지`, `정보 주제`, `상태`, `핵심 질문`, `대상 독자`, `포함할 항목`, `제외할 항목`, `기준 시점`, `참고/출처 메모`, `자유 메모`, and `초안 파일명`. Use IDs such as `INFO-001`.

When the user says `블로그 정보성으로 가줘`, start with topic discovery unless they already gave a specific topic to draft. Unlike visit-review content, info-roundup content does not require the user to provide photos or a subject first. Codex should proactively analyze the current timing, expected search demand 2-3 months ahead, destination seasonality, holiday calendars, weather/travel planning cycles, and current keyword/SERP signals. Do not depend on Naver Creator Advisor data for this workflow. Then propose a prioritized topic and keyword list before drafting.

Topic discovery workflow:

1. Determine the planning window from today's date. For seasonal searches, prioritize topics readers are likely to search 2-3 months later, plus topics that should be published now to mature before peak demand.
2. Build a seasonal demand map from the planning window: weather, clothing, rain/typhoon/heat/cold, school holidays, public holidays, peak pricing, museum/indoor demand, transport reservations, festivals, and destination-specific best-season concerns.
3. Validate candidates with keyword/SERP checks, current travel rules, official tourism/transport/weather sources, and visible seasonal travel cycles.
4. Build a candidate list grouped by intent: `날씨/옷차림`, `여행가기 좋은 시기`, `교통권/이동`, `입장권/예약`, `코스/일정`, `비용/예산`, `준비물`, `가족/임산부/초행자`.
5. Score each candidate by `시즌 적합도`, `검색 의도 명확성`, `정보 갱신 필요성`, `롱제인 적합도`, `카드뉴스화 가능성`, and `경쟁 회피 가능성`.
6. Return a topic proposal table before writing. Include `우선순위`, `주제`, `메인 키워드`, `서브 키워드`, `추천 발행 시점`, `검색 의도`, `필수 확인 출처`, `카드뉴스 아이디어`, and `선정 이유`.
7. After the user approves a topic or asks to proceed automatically, create the draft row/files under `정보성/`, collect sources, write the draft, create needed cardnews, and render Word when supported.

Use the same keyword selection logic as visit-review content. Follow `references/keyword-policy.md` for info-roundup keyword candidate generation, SERP evidence, scoring, and role selection. Seasonal prediction decides which topics enter the candidate pool; the final `메인 키워드` and `서브 키워드` are still chosen by review-style keyword policy: strong destination/topic relevance, clear search intent, blog-tab exposure, low influencer dominance, manageable blog competition ratio, and evidence from autocomplete, related searches, recommended keywords, or AI-tab questions.

For weather and month-based keywords, do not only write for the current month. In June, for example, consider August-September demand such as late-summer heat, September weather, Chuseok/holiday travel timing, fall museum routes, autumn clothing, and typhoon/rain preparation depending on destination. Always choose the window from the actual current date.

For every info-roundup draft, start from one concrete search intent. The first 5-8 visible lines should answer the main question directly with the destination/topic, recommended choice or conclusion, key conditions, and one caution. Then add a quick summary table, comparison table, checklist, or decision matrix before expanding into sections.

Because these topics often depend on current facts, research before drafting whenever claims involve weather norms, prices, operating hours, admission, transport passes, reservation rules, visa/regulation, holidays, closures, safety, or product availability. Prefer official or primary sources where possible, then reliable recent sources for context. Keep source notes in `정보성/sources/{ID}/` or the working draft notes. In the public draft, write naturally and avoid turning the post into a citation dump.

Do not pretend firsthand experience. If the user did not visit, write as Longjane's planning guide: `제가 여행 준비할 때 기준으로 정리해보면`, `처음 가는 분 기준으로 보면`, `일정 짤 때 먼저 확인할 건`, or `방문 전 체크용으로 정리했어요`. Avoid excessive disclaimers; be transparent once, then focus on usefulness.

Default info-roundup structure:

1. Fixed greeting.
2. Direct answer paragraph.
3. Quick summary table or checklist.
4. Numbered `목차` with compact answer labels.
5. Section pattern: `answer -> current basis/evidence -> decision tip`.
6. Comparison table or decision matrix when the topic has multiple options.
7. `이런 분께 추천`, `선택 기준`, `방문 전 체크`, or `준비물 체크리스트`.
8. Internal-link placement note for adjacent Longjane topics when relevant.

Use cardnews actively for info-roundup posts. If there are no real visit photos, create information-first visuals such as summary cards, comparison cards, weather/packing cards, route-flow cards, checklist cards, and decision trees. These images must not imitate real visit photos. Mark placement in the draft with `[CARDNEWS: NN]` and map every file in a cardnews plan. Word output should preserve markers as text only.

## Responsibilities

Let the harness handle deterministic work: workbook parsing, folder paths, photo manifests, keyword files, SERP evidence capture, and Word creation.

Codex must handle judgment-heavy work: interpreting notes, applying the persona, choosing emphasis, placing photo references naturally, and writing polished Korean prose.

Before drafting, identify the article's main scene: the moment that would make a reader want to book, visit, eat, or try it. Build the intro, TOC, section headings, and photo rhythm around that scene. Do not default to checklist-like structures such as `basic info -> location -> interior -> amenities -> conclusion` unless the photos and brief truly call for it.

Photos are not just placement references. Treat every useful photo as source material for analysis and research. Read the visible details, infer grounded research questions from them, and add reader-useful information that was not explicitly written in the workbook when it can be verified or reasonably supported. For example, food photos should prompt dish identification, signature-menu checks, side composition, texture/flavor explanation, portion/value interpretation, and price comparison against the local restaurant context. Spot photos should prompt place history, route, viewing point, architectural/cultural context, crowd/season cues, and what readers should notice on site. Stay, transit, and shopping photos should likewise produce new practical interpretation rather than only describing what is visible.

Treat receipt, ticket, booking, menu, price-tag, map, sign, and information-board photos as high-value evidence. Extract visit date/time, item names, quantities, prices, address/location, opening or admission details, reservation channel, payment totals, and other factual anchors when visible. Use those anchors to write clearer baseline information, such as `방문일`, `방문 당시 가격`, `2인 총액`, `주문 메뉴`, or `입장료 기준`. If the photo text is partly unreadable, state only what can be confidently read or verify it elsewhere before using it.

When photo-derived interpretation needs current facts, external context, menu information, prices, official descriptions, or place-specific background, research it before drafting and keep claims grounded. If a detail cannot be verified, write it as a careful observation or omit it. Do not invent exact menu names, prices, effects, staff behavior, history, or status from photos alone.

The user's briefing notes are seed material, not the full article. Use them to infer and write a richer first-person review in Longjane's voice. Add subjective judgment, emotional reaction, value assessment, audience fit, and practical hindsight that naturally follows from the notes, photos, and verified context. The draft should not sound like a third-party report summarizing the user's notes.

Avoid distancing phrases that reveal the writer is analyzing someone else's photos, such as `사진 상으로는`, `사진을 보면`, `사용자가 찍은 사진`, or `제공된 사진`. In public drafts, write from the visit perspective: `제가 방문했을 때는`, `제가 봤을 때는`, `이 장면에서 먼저 느낀 건`, `저는 이 구성이 좋았어요`, `다시 간다면`, and `예약/방문 전에 알았으면 좋았겠다 싶은 점은`. Use these only when supported by the briefing, photos, or careful inference; do not invent private events.

Draft for AI-citation-friendly Naver content without losing Longjane's voice. Each substantial section should answer a likely search question in the first 2-3 lines, then develop the scene, photos, interpretation, and practical tip. Make facts and subjective judgment easy to separate: state visit/date/price/menu/location facts clearly, then add first-person evaluation. Include at least two of these in every substantial article when relevant: `다시 간다면`, `이런 분께 추천`, `방문 전 확인할 점`, `가격/시간/동선 기준 판단`.

When writing for Naver Mate-style competitiveness, make the article solve one concrete search intent before it becomes a mood essay. Use direct search-question titles and early answer blocks similar to strong travel Mate posts: `가는 방법`, `입장료`, `소요시간`, `가격 비교`, `예약 방법`, `준비물`, `사진 포인트`, or `추천 코스` should appear in the title or the first section when they are the reader's real question. The first 5-8 visible lines after the greeting should answer the main query with the subject, location, price/free status, time/duration, recommendation fit, and one key caution when relevant.

For travel spots, transit, stays, shopping, and restaurants, add a compact answer block near the top when facts are available. Prefer a simple Markdown table for scan-critical information:
`장소/위치`, `방문일`, `입장료/가격`, `소요시간`, `예약/이동 방법`, `추천 상황`, `주의할 점`. For comparison-heavy topics, include a comparison table such as `교통수단/가격/소요시간/장점/단점`, `숙소/가격/위치/청결/추천 대상`, or `제품/현장가/추천 대상/재구매 여부`. These tables should support the article, not replace the first-person review.

Keep Longjane's emotional hook, but do not let it delay the answer. The default opening order for Mate-style drafts is: `greeting -> direct answer paragraph -> factual quick table or bullet block -> personal reason this mattered -> 목차`. In each major section, start with a citation-ready sentence that could stand alone in AI briefing, then follow with visit texture, photos, and subjective judgment.

Build topic clusters inside the draft. When the project already has related posts, add a natural internal-link placement note or paragraph near the end that connects the current article to adjacent Longjane posts, such as `파리 무료 실내 코스 -> 파리 약국 쇼핑 -> 파리 동네 레스토랑`, `후쿠오카 교통 -> 호텔 -> 당일치기 코스`, or `상하이 숙소 -> 주변 관광지 -> 맛집`. Do not overstuff unrelated links; connect only posts that would help the same trip plan.

TOC items should be short, high-impact answer labels, not long sentences. Prefer 5 compact items of roughly 8-18 Korean characters when possible. Each item should reveal the section's search intent or decision point with a noun phrase or compressed phrase, such as `위치와 예약`, `추천 메뉴`, `2인 주문 조합`, `가격 판단`, `방문 전 체크`. Avoid full-sentence TOC items like `Le Jéroboam은 파리 여행 동선에서 일부러 갈 만할까?` unless the article format explicitly calls for Q&A.

Do not make TOC items short at the expense of meaning. Each TOC item must cover the full scope of its section. For example, if one section explains both octopus and duck mains, use `메인 메뉴 2가지` rather than `문어 메인 추천`. If one section explains dessert choices plus why ordering less is better, use `디저트 주문 조절` rather than a label that only names one dessert.

## References

Read only what the task needs:

- `references/workbook-schema.md`: workbook sheets, columns, required fields.
- `references/persona-and-formats.md`: Longjane persona and topic section formats.
- `references/keyword-policy.md`: keyword scoring and Naver SERP automation rules.
- `references/docx-output-policy.md`: Word formatting, image insertion, fallback behavior.

## Commands

Prepare one article:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py prepare --project . --id STAY-001
```

Prepare with SERP checks:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py prepare --project . --id STAY-001 --check-serp
```

Render from markdown:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py render --project . --id STAY-001 --draft drafts/STAY-001/STAY-001_draft.md
```

Inspect workbook IDs:

```bash
python ~/.codex/skills/longjane-blog-drafter/scripts/blog_auto.py list --project .
```

## Safety Rules

- Do not auto-publish to Naver Blog.
- Do not automate Naver login or posting.
- Do not bypass CAPTCHA, login walls, or rate limits.
- Do not mutate the source workbook in v1.
- Exception: after starting or completing a requested draft pipeline, update workflow/status fields in the source workbook as described above. To avoid clutter, the harness does not keep workbook backups by default; set `LONGJANE_KEEP_WORKBOOK_BACKUP=1` when a timestamped backup is required.
- Do not rename, delete, or overwrite original photos in v1.
- Keep API credentials in environment variables or `.env`, never in source files.
- Prefer `UNKNOWN` over overconfident SERP classification.

## Drafting Rules

Use the fixed greeting from the persona. Write in casual conversational Korean polite style, first person, with natural husband references where supported by the brief. Prefer `~해요`, `~했어요`, `~좋아요`, and `~추천해요` endings over formal `~습니다` endings. Keep `~습니다` mostly for the fixed greeting or rare notice-like sentences that genuinely need formality. Keep paragraphs mobile-friendly. Include honest value-for-money judgments and savings tips when relevant. Keep the tone a little brighter and more lively than a plain factual review: add natural reactions, light rhythm, and friendly transitions without becoming childish or salesy.

Write public drafts in Longjane's mobile-centered line-break style: use short lines and frequent blank lines so the text can be center-aligned in Naver Blog. This is a formatting requirement, not a request to shorten substance. Keep the article rich, researched, and useful while only changing the line breaks. Prefer one sentence per line, or split long sentences into 2-3 natural short lines. Keep each visual paragraph to roughly 2-5 short lines separated by a blank line.

After the fixed greeting, write a fuller emotional intro before the numbered `목차`. Use personal hooks from the brief, such as pregnancy, husband, family, or season, when they help readers care. Prefer 5 table-of-contents items. Combine related topics instead of making many small sections. Make TOC labels and matching numbered headings search-friendly but emotionally phrased, e.g. `제주 감성을 느낄 수 있는 숙소 외관` instead of dry labels like `외관과 위치`.

The numbered `목차` is required for substantial drafts, but its labels must be compact, scene-led, and search-intent-aware. Avoid both dry fact labels such as `객실 내부`, `욕실과 어메니티`, `메뉴`, `위치`, `이용 방법`, or `총평` and overly long sentence labels. Use short impact labels that make the topic obvious, such as `방 보고 안심한 순간`, `문어 메인 추천`, `2인 주문 조합`, `짐 편한 탑승 흐름`, or `바다 산책 동선`.

For all topics, use the default flow `scene/feeling -> concrete detail -> reader-useful tip`. Avoid writing as `fact -> explanation -> recommendation` because it makes all drafts feel similar and does not create desire.

For every article, write with confident, positive, specific language. Avoid weak hedging and lukewarm modifiers such as `꽤`, `무난`, `괜찮`, `나쁘지 않다`, and `생각보다`. Replace them with concrete positive details, sensory impressions, or useful fit guidance. If the experience has a limitation, frame it as a practical tip or audience-fit note after explaining what works well.

Use emojis when they fit the paragraph mood. Prefer a light touch: section headings, short transition lines, travel tips, food/coffee moments, and emotional hooks may use one emoji. Do not use emojis in every paragraph, do not stack many emojis, and avoid making factual info tables visually noisy.

When photos exist, use the photo manifest and insert photo position markers like:

```text
[PHOTO: 01]
```

The renderer keeps these markers as text in the Word file. Do not embed actual images in `.docx`; only indicate where photos should go. Still complete the photo selection step and create `photos/{ID}/ordered_photos/`.

Place photos before the text that explains them. For photo-supported sections, use the rhythm `heading -> [PHOTO: NN] -> explanation`, then alternate `[PHOTO: NN] -> explanation` through the section. Do not put a photo marker after the paragraph it belongs to. If a section has photos or cardnews, the first visible block after the heading should normally be `[PHOTO: NN]`, `[CARDNEWS: NN]`, or another visual marker; avoid `heading -> intro paragraph -> photo -> explanation` in visit-review drafts.

When using photos, infer why the user likely took the photo and start from that reaction. It is fine to write grounded inferences from visible content, such as `이런 사진은 예약 전에 보고 싶잖아요`, `이 장면에서 먼저 안심했어요`, or `이런 작은 구성이 실제로 편했어요`. Do not invent unsupported conversations, staff actions, exact emotions, or events.

Each selected photo or photo group should answer: "What new thing can this image help the reader understand?" Add that interpretation near the marker. Avoid generic captions such as `메뉴가 나왔어요`, `외관이에요`, or `내부 모습이에요` unless they are followed by concrete analysis, context, or a practical takeaway.

After adding factual context, translate it into a first-person review judgment. Explain what felt satisfying, what made the visit easier, what made the price feel worthwhile, who would enjoy it, what to order/book/check next time, or what the user would do differently. Keep this subjective layer present across all themes: stays, food/cafes, spots, transit, and shopping.

For AI-citation-friendly structure, create at least one concise "citation candidate" sentence in each major section: a standalone sentence that combines the subject, condition, and judgment. Example: `Le Jéroboam은 파리 중심 관광지와는 거리가 있지만, 조용한 저녁 레스토랑과 문어 메인을 원한다면 일부러 찾아갈 만한 곳이에요.`

Photo count should preserve the feeling of a real visit. When enough useful photos are provided, do not over-minimize the selection. As a practical target, review ordinary travel reviews for at least 15 photos, lodging/hotel/space reviews around 20 photos, and food/cafe/experience reviews around 18 photos. These are targets, not hard minimums: skip blurry, near-duplicate, or low-value photos, and do not force extra photos when the source set is sparse.

For every new draft, select photos from the original source photo folder based on article usefulness, not based on a preset count or a previous `ordered_photos` count. Review the full source set or contact sheet against the planned article structure. Keep distinct photos that provide new evidence, atmosphere, price/menu/signage detail, route context, visual proof, product comparison, room/facility detail, or decision value. Remove or skip true duplicates, blurry/low-value photos, and repetitive near-identical frames. If a source set has many useful, distinct photos, use them; if it is visually repetitive, use fewer real photos and strengthen the article with answer blocks, tables, and information-first cardnews.

Multiple photos may support one paragraph or scene. Naver Blog can place photos side by side, stacked, or in grid layouts, so related photos should often be grouped with consecutive markers instead of forcing one photo per paragraph. Use consecutive `[PHOTO: NN]` markers for the same exterior, entrance, menu, room, bathroom, route, view, amenity, detail, or food moment when the group improves realism or usefulness. After a photo group, explain the shared scene and practical takeaway rather than describing every image mechanically.

If fewer than the target number of useful photos are available, do not mention the shortage in the public draft. Use the best available photos, then increase the text's practical value with route, reservation, price, menu, facility, timing, crowd, parking, packing, or usage tips supported by the brief.

When provided photos are too sparse to carry the article visually, consider supplemental images. Supplemental images must not pretend to be real visit photos. Do not generate fake rooms, food, storefronts, landscapes, people, menus, facilities, or experience scenes that readers could mistake for photos taken by the author. Prefer information-first images: annotated versions of existing photos, text cards, checklist cards, route or flow cards, reservation tips, menu/price summary cards, feature callouts, or simple section-divider graphics.

When supplemental images would help, write an "추가 제작 이미지 메모" in the photo plan or final report. Include the proposed position, purpose, format, copy text, source photo to reference if any, and production method. Example fields: `위치`, `목적`, `추천 형식`, `문구`, `참고 사진`, `제작 방식`. Only create supplemental images after the user approves or explicitly asks for image generation/editing.

When supplemental images are actually created, mark their placement in the public draft with explicit text markers such as `[CARDNEWS: 01]`, `[CARDNEWS: 02]`, or `[INFOCARD: 01]` before the paragraph they support, the same way photo markers are placed before explanatory text. The Word renderer preserves these markers as text, so the `.docx` must show where each cardnews image should be inserted manually in Naver Blog. Update the photo plan with a mapping for every card marker, for example `[CARDNEWS: 01] cardnews/<filename>.png - purpose/position`, plus the editable source file when one exists. Do not count cardnews markers as `[PHOTO: NN]` markers, and do not embed the cardnews images into `.docx`.

For photo ordering, preserve quality and preserve originals. Do not downscale user-provided JPEGs. Only create temporary thumbnails for review if needed, and never use those thumbnails as final `ordered_photos` when full-size JPEGs are available. Sequential filenames must be applied to copied files only.

When revising an older draft after new writing or cardnews guidance has changed, re-apply the same full source-photo review used for new drafts. Do not simply match the existing `[PHOTO: NN]` marker count or the current `ordered_photos` count. Re-review the original source photo folder and contact sheets against the updated article structure, add back useful distinct photos, and remove only true duplicates or low-value repetitive frames. If the real photo set is still sparse or visually repetitive after this review, then add information-first cardnews markers and files as supplemental material.

If videos are present in `photos/{ID}/`, leave them untouched and exclude them from photo manifests, photo plans, and `ordered_photos`.

## Sponsorship-Sensitive Drafting

- Do not write `협찬`, `체험단`, `제공받아`, or `직접 결제하지 않았다` in the public draft unless the user explicitly asks for disclosure wording.
- Do not imply the user paid out of pocket. Use neutral price phrasing such as `네이버 예약 기준`, `참고 가격`, and `예약 전 날짜별 요금 확인`.
- Do not include `만족도`, numeric scores, or `4 / 5` style rating rows in public tables for sponsored stay reviews. Treat workbook satisfaction scores as internal guidance only.
- Avoid negative-sounding wording such as `아쉽다`, `불편`, `부담`, `기대하기보다는`, and `반대로` where a practical tip can do the job. Reframe as usage tips, audience fit, or reservation-check points.
- Keep public drafts free of internal notes such as `키워드 메모`, `협찬 키워드 후보`, or `작성 판단`.
