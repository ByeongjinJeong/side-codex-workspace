from __future__ import annotations

import json
import re
import zipfile
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from .paths import Paths

EMU_PER_INCH = 914400
MAX_IMAGE_WIDTH_EMU = int(5.8 * EMU_PER_INCH)


def render_docx(paths: Paths, draft_path: Path) -> Path:
    if not draft_path.exists():
        raise FileNotFoundError(draft_path)
    manifest = read_manifest(paths)
    markdown = draft_path.read_text(encoding="utf-8")
    output = paths.article_file("draft.docx")
    package = DocxPackage(manifest)
    package.write(output, markdown)
    return output


def read_manifest(paths: Paths) -> list[dict]:
    path = paths.article_file("photo_manifest.json")
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


class DocxPackage:
    def __init__(self, manifest: list[dict]):
        self.manifest = manifest
        self.used: set[int] = set()
        self.media: list[tuple[str, Path, str]] = []
        self.rels: list[tuple[str, str]] = []

    def write(self, output: Path, markdown: str) -> None:
        body = self.markdown_to_body(markdown)
        document_xml = DOCUMENT_XML.format(body=body)
        rels_xml = self.document_rels_xml()
        content_types = self.content_types_xml()

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types)
            z.writestr("_rels/.rels", ROOT_RELS)
            z.writestr("word/document.xml", document_xml)
            z.writestr("word/_rels/document.xml.rels", rels_xml)
            z.writestr("word/styles.xml", STYLES_XML)
            for target, path, _content_type in self.media:
                z.write(path, f"word/{target}")

    def markdown_to_body(self, markdown: str) -> str:
        lines = markdown.splitlines()
        body: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            if not line:
                i += 1
                continue
            if line.startswith("# "):
                body.append(paragraph(line[2:].strip(), style="Title"))
            elif line.startswith("## "):
                body.append(paragraph(line[3:].strip(), style="Heading1"))
            elif line.startswith("### "):
                body.append(paragraph(line[4:].strip(), style="Heading2"))
            elif is_photo_marker(line):
                body.append(self.image_for_marker(line))
            elif is_table_line(line):
                table_lines = []
                while i < len(lines) and is_table_line(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                body.append(table(table_lines))
                continue
            else:
                body.append(paragraph(line))
            i += 1
        return "".join(body)

    def image_for_marker(self, line: str) -> str:
        match = re.search(r"\[PHOTO:\s*(\d+)\]", line)
        if not match:
            return paragraph(line)
        index = int(match.group(1))
        self.used.add(index)
        return paragraph(f"[PHOTO: {index:02d}]")

    def append_unused_images(self) -> str:
        unused = [p for p in self.manifest if int(p.get("index", 0)) not in self.used]
        if not unused:
            return ""
        out = [paragraph("사진", style="Heading1")]
        for item in unused:
            path = Path(item["path"])
            if path.exists():
                out.append(self.add_image(path, item.get("caption") or f"사진 {int(item.get('index', 0)):02d}"))
        return "".join(out)

    def add_image(self, path: Path, caption: str) -> str:
        ext = path.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            content_type = "image/jpeg"
        elif ext == ".png":
            content_type = "image/png"
        else:
            return paragraph(f"[사진 삽입 실패: 지원하지 않는 형식 {path.name}]")

        rid = f"rId{len(self.rels) + 1}"
        target = f"media/image{len(self.media) + 1}{'.jpg' if content_type == 'image/jpeg' else '.png'}"
        self.media.append((target, path, content_type))
        self.rels.append((rid, target))
        cx, cy = image_size_emu(path)
        if cx > MAX_IMAGE_WIDTH_EMU:
            ratio = MAX_IMAGE_WIDTH_EMU / cx
            cx = MAX_IMAGE_WIDTH_EMU
            cy = int(cy * ratio)
        return DRAWING_XML.format(rid=rid, cx=cx, cy=cy, name=xml_escape(path.name)) + paragraph(caption, italic=True)

    def document_rels_xml(self) -> str:
        rels = [
            '<Relationship Id="rStyle" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        ]
        for rid, target in self.rels:
            rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{xml_escape(target)}"/>')
        return RELS_XML.format(rels="".join(rels))

    def content_types_xml(self) -> str:
        defaults = {
            "rels": "application/vnd.openxmlformats-package.relationships+xml",
            "xml": "application/xml",
        }
        if any(t == "image/jpeg" for _target, _path, t in self.media):
            defaults["jpg"] = "image/jpeg"
            defaults["jpeg"] = "image/jpeg"
        if any(t == "image/png" for _target, _path, t in self.media):
            defaults["png"] = "image/png"
        default_xml = "".join(f'<Default Extension="{ext}" ContentType="{ctype}"/>' for ext, ctype in defaults.items())
        return CONTENT_TYPES_XML.format(defaults=default_xml)


def paragraph(text: str, style: str | None = None, italic: bool = False) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    rpr = "<w:rPr><w:i/></w:rPr>" if italic else ""
    return f"<w:p>{ppr}<w:r>{rpr}<w:t xml:space=\"preserve\">{xml_escape(text)}</w:t></w:r></w:p>"


def table(lines: list[str]) -> str:
    rows = []
    cleaned = [split_table_line(line) for line in lines]
    if len(cleaned) > 1 and all(set(cell.strip()) <= {"-", ":"} for cell in cleaned[1]):
        cleaned.pop(1)
    for cells in cleaned:
        row = "".join(f"<w:tc><w:p><w:r><w:t>{xml_escape(cell.strip())}</w:t></w:r></w:p></w:tc>" for cell in cells)
        rows.append(f"<w:tr>{row}</w:tr>")
    return f"<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/><w:tblBorders><w:top w:val=\"single\" w:sz=\"4\"/><w:left w:val=\"single\" w:sz=\"4\"/><w:bottom w:val=\"single\" w:sz=\"4\"/><w:right w:val=\"single\" w:sz=\"4\"/><w:insideH w:val=\"single\" w:sz=\"4\"/><w:insideV w:val=\"single\" w:sz=\"4\"/></w:tblBorders></w:tblPr>{''.join(rows)}</w:tbl>"


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def split_table_line(line: str) -> list[str]:
    return line.strip().strip("|").split("|")


def is_photo_marker(line: str) -> bool:
    return bool(re.search(r"\[PHOTO:\s*\d+\]", line))


def image_size_emu(path: Path) -> tuple[int, int]:
    size = image_pixel_size(path)
    if not size:
        return int(4.5 * EMU_PER_INCH), int(3.0 * EMU_PER_INCH)
    width, height = size
    # Assume 96 DPI for display sizing.
    return int(width / 96 * EMU_PER_INCH), int(height / 96 * EMU_PER_INCH)


def image_pixel_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            length = int.from_bytes(data[i:i + 2], "big")
            if 0xC0 <= marker <= 0xC3:
                height = int.from_bytes(data[i + 3:i + 5], "big")
                width = int.from_bytes(data[i + 5:i + 7], "big")
                return width, height
            i += length
    return None


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{defaults}<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>"""

DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:sz w:val="22"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style></w:styles>"""

DRAWING_XML = """<w:p><w:r><w:drawing><wp:inline><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="{name}"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"""
