# DOCX Output Policy

Primary output:

```text
drafts/{ID}/{ID}_draft.docx
```

Also keep:

```text
drafts/{ID}/{ID}_draft.md
drafts/{ID}/{ID}_photo_plan.md
photos/{ID}/ordered_photos/
```

## Structure

The Word file should include:

- Title.
- Section headings.
- Basic info tables where useful.
- Mobile-friendly paragraphs.
- Center-alignment-friendly short line breaks.
- Photo position markers only.
- Captions or nearby context when useful.

## Markdown Input

Renderer accepts simple markdown:

- `# title`
- `## heading`
- paragraphs
- pipe tables
- photo markers: `[PHOTO: 01]`

## Image Behavior

When a photo marker exists, preserve that marker as text in the Word file.

Do not embed actual images in `.docx`, and do not append unused manifest photos at the end.

Photo selection is still required. Create `photos/{ID}/ordered_photos/` with selected images copied from source images. Filenames must be sequential and descriptive, for example:

```text
01_STAY-004_kitchen_living_wide.png
```

The number of files in `photos/{ID}/ordered_photos/` must match the number of `[PHOTO: NN]` markers in the draft.

Photo count targets apply when the source photo set is sufficient: ordinary reviews should normally use 15+ useful photos, lodging/hotel/space reviews around 20, and food/cafe/experience reviews around 18. These are review targets, not forced counts. Do not pad with blurry, duplicate, or low-value images, and do not mention photo shortage in the public draft.

Consecutive photo markers may represent a Naver Blog photo group such as side-by-side, stacked, or grid placement. Use this when multiple related photos strengthen the same paragraph, scene, route, room, menu, detail, or tip.

If source files are `.jpg` or `.jpeg`, copy selected files as-is and do not resize, downscale, or convert them. Never rename or move original photos; apply sequential descriptive filenames only to the copied files in `ordered_photos`. Temporary thumbnails are allowed only for review, not as final ordered photos when full-size JPEGs are available.

Video files such as `.mov`, `.mp4`, and `.m4v` are out of scope for article photo ordering. Leave them untouched and do not include them in `ordered_photos` or `photo_plan.md`.
