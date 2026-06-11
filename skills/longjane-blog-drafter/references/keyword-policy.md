# Keyword Policy

The workflow must run without Naver API credentials.

## Candidate Generation

Generate candidates from:

- destination
- topic
- place or business name
- topic-specific fields
- free memo
- Naver autocomplete terms
- Naver related search terms
- Naver search-result recommended keywords
- AI tab / AI answer question prompts when visible

Do not rely only on Naver SearchAd keyword-tool suggestions. Those tend to favor already obvious head terms and can miss niche phrasing that is better for a smaller blog.

## Optional API Enrichment

If configured later, use Naver APIs for:

- Search volume.
- Blog result counts.
- Cafe result counts only as optional supporting context, not default scoring.

Keep API behavior optional. Respect rate limits and cache results.

## SERP Checks

Automate the originally manual mobile checks when `--check-serp` is passed.

Collect and classify:

- `블로그탭 노출`: `O`, `X`, `UNKNOWN`.
- `인플루언서 점유`: `O`, `X`, `UNKNOWN`.
- Autocomplete evidence: terms suggested while typing.
- Related-search evidence: bottom or inline related terms.
- Recommended-keyword evidence: keyword chips/blocks shown on the result page.
- AI-tab/question evidence: visible AI answer prompts or question-style suggestions.

Save evidence under `drafts/{ID}/serp/`:

- screenshot
- HTML snapshot
- analysis JSON

Conservative policy:

- Use `UNKNOWN` on UI changes, CAPTCHA, blocked access, or ambiguity.
- Do not bypass login, CAPTCHA, or rate limits.

## Scoring

Goal: pick one main keyword and at least two sub keywords that a non-large blog can realistically expose on Naver.

Do not optimize for raw monthly search volume alone. Prefer keywords with:

- Strong destination/place relevance.
- Clear review/search intent such as `후기`, `추천`, `가격`, `웨이팅`, `입장료`, `가는법`, or a route/place-specific phrase.
- Blog exposure `O`.
- Influencer dominance `X`.
- Search volume high enough to matter but not necessarily large.
- Low competition relative to search volume.
- Evidence from autocomplete, related searches, result-page recommended keywords, or AI-tab questions.

Competition formula:

```text
competition_total = blog_count
competition_ratio = blog_count / monthly_searches
blog_competition_ratio = blog_count / monthly_searches
```

Lower `competition_ratio` is better. Because the output is a Naver Blog article, default competition scoring uses blog result counts only. A keyword with modest search volume and very low blog competition can beat a high-volume keyword saturated by existing blog posts. Cafe counts may be recorded as optional context, but do not mix them into the default blog competition ratio.

Recommended role selection:

- `메인 키워드`: best combined score from intent fit, manageable competition ratio, blog-tab exposure, influencer non-dominance, and SERP evidence.
- `서브 키워드`: at least two supporting terms from autocomplete/related/recommended/AI questions, or long-tail intent variants that fit the article naturally.
- Avoid selecting only generic head terms such as `{도시} 맛집` or `{도시} 호텔 추천` unless the competition ratio and SERP evidence are still favorable.
