#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from longjane_blog.drafting import build_context
from longjane_blog.config import load_config
from longjane_blog.keywords import generate_keywords, write_keywords_csv
from longjane_blog.paths import Paths
from longjane_blog.photos import build_photo_manifest, write_photo_manifest
from longjane_blog.serp_checker import check_keywords
from longjane_blog.workbook import WorkbookReader, sync_workbook, update_article_fields, update_article_status
from longjane_blog.docx_writer import render_docx


def cmd_list(args: argparse.Namespace) -> int:
    paths = Paths(Path(args.project))
    sync_workbook(paths.workbook)
    reader = WorkbookReader(paths.workbook)
    for item in reader.list_briefings():
        print(f"{item['id']}\t{item['topic']}\t{item.get('status','')}\t{item.get('title','')}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    paths = Paths(Path(args.project))
    changed = sync_workbook(paths.workbook)
    print("updated" if changed else "already up to date")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    paths = Paths(Path(args.project), args.id)
    paths.ensure_article_dirs()

    sync_workbook(paths.workbook)
    reader = WorkbookReader(paths.workbook)
    briefing = reader.get_briefing(args.id)
    update_article_status(paths.workbook, args.id, "초안 작성 중")

    photos = build_photo_manifest(paths)
    write_photo_manifest(paths, photos)

    keywords = generate_keywords(briefing)
    if args.check_serp or (not args.skip_keyword_evidence and keyword_evidence_configured()):
        check_keywords(paths, keywords, briefing)
    elif not args.skip_keyword_evidence:
        print(
            "warning: keyword evidence not checked because Naver SearchAd credentials are not configured",
            file=sys.stderr,
        )
    write_keywords_csv(paths, keywords)

    context_path = build_context(paths, briefing, keywords, photos)
    print(context_path)
    return 0


def keyword_evidence_configured() -> bool:
    config = load_config()
    return bool(
        config.naver_searchad_access_license
        and config.naver_searchad_secret_key
        and config.naver_searchad_customer_id
    )


def cmd_render(args: argparse.Namespace) -> int:
    paths = Paths(Path(args.project), args.id)
    draft_path = Path(args.draft)
    if not draft_path.is_absolute():
        draft_path = paths.project / draft_path
    output = render_docx(paths, draft_path)
    update_article_status(paths.workbook, args.id, "초안 완료")
    update_article_fields(paths.workbook, args.id, {"초안 파일명": str(output.relative_to(paths.project))})
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Longjane blog drafting harness")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List briefing IDs")
    p_list.add_argument("--project", default=".", help="Project root")
    p_list.set_defaults(func=cmd_list)

    p_sync = sub.add_parser("sync", help="Write generated IDs and refresh publication overview")
    p_sync.add_argument("--project", default=".", help="Project root")
    p_sync.set_defaults(func=cmd_sync)

    p_prepare = sub.add_parser("prepare", help="Prepare context for one ID")
    p_prepare.add_argument("--project", default=".", help="Project root")
    p_prepare.add_argument("--id", required=True, help="Article ID")
    p_prepare.add_argument("--check-serp", action="store_true", help="Run conservative Naver mobile SERP checks")
    p_prepare.add_argument("--skip-keyword-evidence", action="store_true", help="Skip SearchAd/search-volume enrichment")
    p_prepare.set_defaults(func=cmd_prepare)

    p_render = sub.add_parser("render", help="Render markdown draft to docx")
    p_render.add_argument("--project", default=".", help="Project root")
    p_render.add_argument("--id", required=True, help="Article ID")
    p_render.add_argument("--draft", required=True, help="Markdown draft path")
    p_render.set_defaults(func=cmd_render)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
