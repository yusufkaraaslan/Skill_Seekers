"""Regression tests: data_file parent-dir handling when --output is honored.

PR #409 made ``self.data_file`` follow --output via ``data_file_for()``
(``f"{skill_dir}_extracted.json"``), but several scrapers kept pre-PR
directory handling around the data_file write:

- epub/word/html ran ``os.makedirs(os.path.dirname(self.data_file))``
  unguarded — with a single-component --output (e.g. ``--output docskill``)
  ``dirname()`` is ``""`` and ``os.makedirs("", exist_ok=True)`` raises
  FileNotFoundError, discarding the completed extraction.
- openapi hard-coded ``os.makedirs("output")`` while data_file followed
  --output — FileNotFoundError when the --output parent doesn't exist.
- pdf had no makedirs at all before ``open(self.data_file, "w")``.

Each test exercises the formerly-crashing write with the exact trigger.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# HTML: single-component --output → dirname(data_file) == ""
# ---------------------------------------------------------------------------


def test_html_extract_with_single_component_output(tmp_path, monkeypatch):
    from skill_seekers.cli.html_scraper import HtmlToSkillConverter

    monkeypatch.chdir(tmp_path)
    html_file = tmp_path / "docs.html"
    html_file.write_text(
        "<html><head><title>Docs</title></head>"
        "<body><h1>Intro</h1><p>Hello regression test.</p></body></html>",
        encoding="utf-8",
    )

    converter = HtmlToSkillConverter(
        {"name": "docskill", "html_path": str(html_file), "output_dir": "docskill"}
    )
    assert converter.data_file == "docskill_extracted.json"

    converter.extract()  # formerly: os.makedirs("") → FileNotFoundError

    data = json.loads(Path("docskill_extracted.json").read_text(encoding="utf-8"))
    assert data["pages"]


# ---------------------------------------------------------------------------
# PDF: --output with a non-existent parent dir, no makedirs before open()
# ---------------------------------------------------------------------------


def test_pdf_extract_creates_missing_output_parent(tmp_path, monkeypatch):
    fitz = pytest.importorskip("fitz")
    from skill_seekers.cli.pdf_scraper import PDFToSkillConverter

    monkeypatch.chdir(tmp_path)
    pdf_file = tmp_path / "textonly.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello PDF regression test. Plain text only, no images.")
    doc.save(str(pdf_file))
    doc.close()

    converter = PDFToSkillConverter(
        {
            "name": "mypdf",
            "pdf_path": str(pdf_file),
            "output_dir": "skills/mypdf",
            # The exact trigger: image extraction disabled means nothing else
            # ever creates skills/ before the data_file write.
            "extract_options": {"extract_images": False},
        }
    )
    assert converter.data_file == "skills/mypdf_extracted.json"
    assert not Path("skills").exists()

    converter.extract()  # formerly: open() → FileNotFoundError (skills/ missing)

    assert Path("skills/mypdf_extracted.json").exists()


# ---------------------------------------------------------------------------
# OpenAPI: hard-coded makedirs("output") while data_file follows --output
# ---------------------------------------------------------------------------

MINIMAL_SPEC = """\
openapi: 3.0.0
info:
  title: Ping API
  version: 1.0.0
paths:
  /ping:
    get:
      summary: Ping the service
      responses:
        '200':
          description: OK
"""


def test_openapi_extract_creates_missing_output_parent(tmp_path, monkeypatch):
    from skill_seekers.cli.openapi_scraper import OpenAPIToSkillConverter

    monkeypatch.chdir(tmp_path)
    spec_file = tmp_path / "api.yaml"
    spec_file.write_text(MINIMAL_SPEC, encoding="utf-8")

    converter = OpenAPIToSkillConverter(
        {"name": "myapi", "spec_path": str(spec_file), "output_dir": "skills/myapi"}
    )
    assert converter.data_file == "skills/myapi_extracted.json"
    assert not Path("skills").exists()

    converter.extract()  # formerly: makedirs("output") then open() → FileNotFoundError

    assert Path("skills/myapi_extracted.json").exists()
    # The stray hard-coded directory must no longer be created.
    assert not Path("output").exists()


def test_openapi_extract_with_single_component_output(tmp_path, monkeypatch):
    from skill_seekers.cli.openapi_scraper import OpenAPIToSkillConverter

    monkeypatch.chdir(tmp_path)
    spec_file = tmp_path / "api.yaml"
    spec_file.write_text(MINIMAL_SPEC, encoding="utf-8")

    converter = OpenAPIToSkillConverter(
        {"name": "myapi", "spec_path": str(spec_file), "output_dir": "myapi"}
    )

    converter.extract()

    assert Path("myapi_extracted.json").exists()
    assert not Path("output").exists()


# ---------------------------------------------------------------------------
# Word: single-component --output → dirname(data_file) == ""
# ---------------------------------------------------------------------------


def test_word_extract_with_single_component_output(tmp_path, monkeypatch):
    pytest.importorskip("mammoth")
    python_docx = pytest.importorskip("docx")
    from skill_seekers.cli.word_scraper import WordToSkillConverter

    monkeypatch.chdir(tmp_path)
    docx_file = tmp_path / "report.docx"
    doc = python_docx.Document()
    doc.add_heading("Intro", level=1)
    doc.add_paragraph("Hello Word regression test.")
    doc.save(str(docx_file))

    converter = WordToSkillConverter(
        {"name": "myreport", "docx_path": str(docx_file), "output_dir": "myreport"}
    )
    assert converter.data_file == "myreport_extracted.json"

    converter.extract()  # formerly: os.makedirs("") → FileNotFoundError

    data = json.loads(Path("myreport_extracted.json").read_text(encoding="utf-8"))
    assert data["pages"]


# ---------------------------------------------------------------------------
# EPUB: single-component --output → dirname(data_file) == ""
# (ebooklib may be absent, so the extraction internals are mocked and only
# the real save step at the end of extract_epub() is exercised.)
# ---------------------------------------------------------------------------


def test_epub_save_with_single_component_output(tmp_path, monkeypatch):
    from skill_seekers.cli import epub_scraper
    from skill_seekers.cli.epub_scraper import EpubToSkillConverter

    monkeypatch.chdir(tmp_path)
    epub_file = tmp_path / "book.epub"
    epub_file.write_bytes(b"PK\x03\x04 not a real epub")

    converter = EpubToSkillConverter(
        {"name": "mybook", "epub_path": str(epub_file), "output_dir": "mybook"}
    )
    assert converter.data_file == "mybook_extracted.json"

    mock_book = MagicMock()
    mock_book.spine = []
    mock_epub = MagicMock()
    mock_epub.read_epub.return_value = mock_book

    with (
        patch.object(epub_scraper, "EPUB_AVAILABLE", True),
        patch.object(epub_scraper, "epub", mock_epub, create=True),
        patch.object(converter, "_detect_drm", return_value=False),
        patch.object(converter, "_extract_metadata", return_value={"title": "Book"}),
        patch.object(converter, "_extract_spine_content", return_value=[]),
        patch.object(converter, "_extract_images", return_value=0),
    ):
        converter.extract_epub()  # formerly: os.makedirs("") → FileNotFoundError

    data = json.loads(Path("mybook_extracted.json").read_text(encoding="utf-8"))
    assert data["metadata"] == {"title": "Book"}
