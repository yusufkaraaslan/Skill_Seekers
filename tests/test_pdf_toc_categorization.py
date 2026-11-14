"""TOC-based categorization for PDF skills (Issue #485, item 3).

Real-world case: a 112-page exchange-rule PDF exposes a 65-entry outline
via PyMuPDF get_toc(), yet everything landed in ONE reference file. These
tests lock in: use the TOC when it is rich enough, subdivide large
chapters by level-2 entries, and keep the conservative single category
when the TOC is missing or too thin (so existing goldens are untouched).
"""

from pathlib import Path

import pytest

from skill_seekers.cli.pdf_scraper import PDFToSkillConverter


def _page(n: int) -> dict:
    return {"page_number": n, "text": f"page {n}", "code_samples": [], "images": []}


TOC = [
    [1, "一、说明", 5],
    [1, "二、变更范围汇总", 5],
    [1, "三、业务简介", 6],
    [1, "四、技术实现", 8],
    [1, "五、参考信息", 13],
    [1, "六、交易接口", 14],
    [2, "6.1匹配成交", 17],
    [2, "6.2协商成交", 20],
    [2, "6.3点击成交", 28],
    [2, "6.4询价成交", 40],
    [2, "6.5竞买成交", 58],
    [1, "七、行情接口", 108],
]


@pytest.fixture
def converter(tmp_path) -> PDFToSkillConverter:
    config = {"name": "toc_test", "pdf_path": str(tmp_path / "doc.pdf")}
    conv = PDFToSkillConverter(config)
    conv.extracted_data = {
        "pages": [_page(n) for n in range(1, 113)],
        "total_pages": 112,
        "toc": [list(e) for e in TOC],
    }
    return conv


class TestTOCCategorization:

    def test_uses_toc_when_rich(self, converter):
        cats = converter.categorize_content()
        # 六、交易接口 (P14-107, 94 pages) must be subdivided by its
        # level-2 children instead of staying one giant category.
        titles = [c["title"] for c in cats.values()]
        assert "6.1匹配成交" in titles and "6.4询价成交" in titles
        assert not any("交易接口" == c["title"] for c in cats.values())
        assert len(cats) >= 8

    def test_page_ranges_assigned(self, converter):
        cats = converter.categorize_content()
        by_title = {c["title"]: c for c in cats.values()}
        sub = by_title["6.4询价成交"]
        numbers = [p["page_number"] for p in sub["pages"]]
        assert numbers[0] == 40 and numbers[-1] == 57
        # front matter (P1-4) captured
        fm = [c for c in cats.values() if c["title"] == "Front Matter"]
        assert fm and [p["page_number"] for p in fm[0]["pages"]] == [1, 2, 3, 4]

    def test_last_chapter_runs_to_end(self, converter):
        cats = converter.categorize_content()
        by_title = {c["title"]: c for c in cats.values()}
        numbers = [p["page_number"] for p in by_title["七、行情接口"]["pages"]]
        assert numbers[0] == 108 and numbers[-1] == 112

    def test_thin_toc_keeps_single_category(self, converter):
        converter.extracted_data["toc"] = [[1, "一、说明", 5], [1, "二、附则", 100]]
        cats = converter.categorize_content()
        assert len(cats) == 1

    def test_missing_toc_keeps_single_category(self, converter):
        del converter.extracted_data["toc"]
        cats = converter.categorize_content()
        assert len(cats) == 1
        first = next(iter(cats.values()))
        assert len(first["pages"]) == 112

    def test_out_of_range_toc_pages_ignored(self, converter):
        converter.extracted_data["toc"] = TOC + [[1, "坏章节", 999]]
        cats = converter.categorize_content()
        assert all("坏章节" != c["title"] for c in cats.values())

    def test_duplicate_titles_sanitized(self, converter):
        dup = [[1, "说明", 5], [1, "说明", 50], [1, "附则", 80]]
        converter.extracted_data["toc"] = dup
        cats = converter.categorize_content()
        keys = list(cats.keys())
        assert len(keys) == len(set(keys))  # no silent overwrite

    def test_extractor_embeds_toc(self, tmp_path, monkeypatch):
        """extract_all() must embed doc.get_toc() so the scraper sees it."""
        import fitz

        pdf = tmp_path / "tiny.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "toc fixture")
        doc.set_toc([[1, "Alpha", 1], [1, "Beta", 1], [1, "Gamma", 1]])
        doc.save(str(pdf))
        doc.close()

        from skill_seekers.cli.pdf_extractor_poc import PDFExtractor

        ex = PDFExtractor(str(pdf), verbose=False, extract_images=False, use_cache=False)
        result = ex.extract_all()
        assert isinstance(result.get("toc"), list)
        assert any(e[1] == "Alpha" for e in result["toc"])


class TestFilenameCollisionSafety:
    """Two chapters starting on the same page (same page range) must not
    silently overwrite each other's reference file."""

    def test_same_range_two_names(self, converter):
        a = {"title": "一、说明", "pages": [_page(5)]}
        b = {"title": "二、汇总", "pages": [_page(5)]}
        f1 = converter._reference_filename(a, 1, 2, "one")
        f2 = converter._reference_filename(b, 2, 2, "two")
        assert f1 != f2

    def test_memo_stable_across_call_sites(self, converter):
        a = {"title": "一、说明", "pages": [_page(5)]}
        f1 = converter._reference_filename(a, 1, 2, "one")
        f2 = converter._reference_filename(a, 1, 2, "one")  # nav link call site
        assert f1 == f2

    def test_build_no_overwrite(self, tmp_path, converter):
        converter.skill_dir = str(tmp_path / "skill")
        converter.build_skill()
        refs = list((Path(converter.skill_dir) / "references").glob("*.md")) 
        cats = converter._categories_from_toc()
        # one file per category (plus index.md)
        assert len(refs) == len(cats) + 1
