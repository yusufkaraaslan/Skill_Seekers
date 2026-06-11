"""Phase 2.1 hook tests — DocumentSkillBuilder variation points.

The golden trees (tests/golden/phase2/*) prove whole-tree byte-identity;
these tests pin the individual hooks added in Phase 2.1 so a future edit
to one hook fails with a precise message instead of a tree-wide diff:

- LOAD_TOTAL_KEY / UNIT_LABEL drive load_extracted_data (pdf/man collapse)
- category_stem + the trailing cat_key parameter of _reference_filename
  (chat names multi-category files by category key, single → main.md)
- PATTERN_KEYWORDS / DOC_NOUN drive _format_patterns_from_content
- DOC_NOUN / RANGE_LABEL drive the index.md title and category ranges
- _frontmatter_value quotes SKILL.md frontmatter only for YAML-special
  values (safe values stay unquoted so the golden trees hold)
"""

import json

from skill_seekers.cli.chat_scraper import ChatToSkillConverter
from skill_seekers.cli.document_skill_builder import DocumentSkillBuilder
from skill_seekers.cli.html_scraper import HtmlToSkillConverter
from skill_seekers.cli.jupyter_scraper import JupyterToSkillConverter
from skill_seekers.cli.man_scraper import ManPageToSkillConverter
from skill_seekers.cli.pdf_scraper import PDFToSkillConverter
from skill_seekers.cli.pptx_scraper import PptxToSkillConverter


def _chat(tmp_path):
    return ChatToSkillConverter(
        {"name": "team", "export_path": str(tmp_path), "output_dir": str(tmp_path)}
    )


class TestLoadTotalKey:
    def test_pdf_loader_reports_total_pages(self, tmp_path, capsys):
        json_path = tmp_path / "extracted.json"
        json_path.write_text(json.dumps({"pages": [{"page_number": 1}], "total_pages": 7}))
        converter = PDFToSkillConverter(
            {"name": "guide", "pdf_path": "guide.pdf", "output_dir": str(tmp_path)}
        )
        assert converter.load_extracted_data(str(json_path)) is True
        assert "Loaded 7 pages" in capsys.readouterr().out

    def test_man_loader_reports_man_pages(self, tmp_path, capsys):
        json_path = tmp_path / "extracted.json"
        json_path.write_text(json.dumps({"pages": [], "total_pages": 2}))
        converter = ManPageToSkillConverter(
            {"name": "tools", "man_names": ["git"], "output_dir": str(tmp_path)}
        )
        assert converter.load_extracted_data(str(json_path)) is True
        assert "Loaded 2 man page(s)" in capsys.readouterr().out


class TestCategoryStemHook:
    def test_base_ignores_cat_key_and_uses_source_stem(self, tmp_path):
        converter = PDFToSkillConverter(
            {"name": "guide", "pdf_path": "guide.pdf", "output_dir": str(tmp_path)}
        )
        cat = {"title": "Intro", "pages": [{"page_number": 3}, {"page_number": 7}]}
        assert converter._reference_filename(cat, 1, 2, "ignored_key") == "guide_p3-p7.md"

    def test_chat_multi_category_uses_cat_key(self, tmp_path):
        converter = _chat(tmp_path)
        cat = {"title": "#eng", "pages": [{"section_number": 1}, {"section_number": 4}]}
        assert converter._reference_filename(cat, 1, 3, "eng") == "eng_s1-s4.md"

    def test_chat_single_category_collapses_to_main(self, tmp_path):
        converter = _chat(tmp_path)
        cat = {"title": "#eng", "pages": [{"section_number": 1}]}
        # NOT "eng.md" — the single-category export is always main.md.
        assert converter._reference_filename(cat, 1, 1, "eng") == "main.md"

    def test_chat_empty_category_falls_back_to_section_number(self, tmp_path):
        converter = _chat(tmp_path)
        assert converter._reference_filename({"title": "x", "pages": []}, 2, 3, "x") == (
            "section_02.md"
        )


class TestPatternKeywords:
    def test_html_extends_shared_keywords(self):
        for kw in DocumentSkillBuilder.PATTERN_KEYWORDS:
            assert kw in HtmlToSkillConverter.PATTERN_KEYWORDS
        assert "changelog" in HtmlToSkillConverter.PATTERN_KEYWORDS
        assert "reference" in HtmlToSkillConverter.PATTERN_KEYWORDS

    def test_jupyter_extends_shared_keywords(self):
        assert "modeling" in JupyterToSkillConverter.PATTERN_KEYWORDS
        assert "getting started" in JupyterToSkillConverter.PATTERN_KEYWORDS

    def test_keywords_and_noun_shape_the_output(self, tmp_path):
        converter = PptxToSkillConverter(
            {"name": "deck", "pptx_path": "deck.pptx", "output_dir": str(tmp_path)}
        )
        converter.extracted_data = {"pages": [{"section_number": 1, "heading": "Agenda for today"}]}
        out = converter._format_patterns_from_content()
        assert "*Common presentation patterns found:*" in out
        assert "**Agenda** (1 sections):" in out


class TestDocNounIndexTitle:
    def test_pptx_index_title_and_pdf_range_label(self):
        assert PptxToSkillConverter.DOC_NOUN == "presentation"
        assert PDFToSkillConverter.RANGE_LABEL == "Pages"
        assert DocumentSkillBuilder.RANGE_LABEL == "Sections"
        assert DocumentSkillBuilder.DOC_NOUN == "documentation"


class TestFrontmatterQuoting:
    def test_safe_values_stay_unquoted(self):
        # Byte-identity with the golden trees depends on this.
        assert DocumentSkillBuilder._frontmatter_value("golden-word") == "golden-word"
        assert (
            DocumentSkillBuilder._frontmatter_value("Use when testing the word golden build")
            == "Use when testing the word golden build"
        )

    def test_yaml_special_values_are_json_quoted(self):
        assert DocumentSkillBuilder._frontmatter_value("godot: engine") == '"godot: engine"'
        assert DocumentSkillBuilder._frontmatter_value("c# basics") == '"c# basics"'
        assert DocumentSkillBuilder._frontmatter_value('say "hi"') == '"say \\"hi\\""'
        assert DocumentSkillBuilder._frontmatter_value("rock'n'roll") == "\"rock'n'roll\""
        assert DocumentSkillBuilder._frontmatter_value(" padded ") == '" padded "'
        assert DocumentSkillBuilder._frontmatter_value("two\nlines") == '"two\\nlines"'

    def test_skill_md_frontmatter_quotes_hostile_name(self, tmp_path):
        converter = HtmlToSkillConverter(
            {
                "name": "godot: engine",
                "html_path": "docs.html",
                "description": "Engine docs: 3D and scripting",
                "output_dir": str(tmp_path),
            }
        )
        converter.skill_dir = str(tmp_path)
        converter.extracted_data = {"pages": [], "metadata": {}}
        converter._generate_skill_md({})

        lines = (tmp_path / "SKILL.md").read_text(encoding="utf-8").splitlines()
        assert lines[0] == "---"
        assert lines[1] == 'name: "godot:-engine"'
        assert lines[2] == 'description: "Engine docs: 3D and scripting"'
        assert lines[3] == "---"

    def test_skill_md_frontmatter_keeps_safe_name_unquoted(self, tmp_path):
        converter = HtmlToSkillConverter(
            {
                "name": "godot engine",
                "html_path": "docs.html",
                "description": "Engine docs",
                "output_dir": str(tmp_path),
            }
        )
        converter.skill_dir = str(tmp_path)
        converter.extracted_data = {"pages": [], "metadata": {}}
        converter._generate_skill_md({})

        lines = (tmp_path / "SKILL.md").read_text(encoding="utf-8").splitlines()
        assert lines[1] == "name: godot-engine"
        assert lines[2] == "description: Engine docs"
