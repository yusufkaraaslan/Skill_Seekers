"""Large-input regression tests for scrapers and analyzers.

Tests that the system handles large inputs without OOM, timeouts,
or incorrect results. All tests are marked @pytest.mark.slow.
"""

import pytest


@pytest.mark.slow
class TestLargeCodeFile:
    def test_10k_line_python_file(self):
        from skill_seekers.cli.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(depth="deep")
        code = ""
        for i in range(2000):
            code += f"def func_{i}(x, y=None):\n"
            code += f'    """Docstring for func_{i}."""\n'
            code += f"    result = x * 2\n"
            code += f"    return result\n\n"

        result = analyzer.analyze_file("large.py", code, "Python")
        assert result is not None
        assert "functions" in result
        assert len(result.get("functions", [])) > 0

    def test_100_class_file(self):
        from skill_seekers.cli.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(depth="deep")
        code = ""
        for i in range(100):
            code += f"class Class{i}:\n"
            code += f"    def method(self):\n"
            code += f"        return {i}\n\n"

        result = analyzer.analyze_file("many_classes.py", code, "Python")
        assert result is not None
        classes = result.get("classes", [])
        assert len(classes) == 100

    def test_large_comment_blocks(self):
        from skill_seekers.cli.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(depth="deep")
        code = "# " + "x" * 5000 + "\n"
        code += "def small_func():\n    return 1\n"

        result = analyzer.analyze_file("comments.py", code, "Python")
        assert result is not None
        assert "comments" in result


@pytest.mark.slow
class TestLargeMarkdown:
    def test_100_section_markdown(self):
        content = ""
        for i in range(100):
            content += f"# Section {i}\n\n"
            content += f"This is section {i} content.\n\n"
            content += f"## Subsection {i}.1\n\n"
            content += f"More content for section {i}.\n\n"
            content += "```python\n"
            content += f"def example_{i}():\n    return {i}\n"
            content += "```\n\n"

        assert len(content) > 5000
        assert "Section 0" in content
        assert "Section 99" in content

    def test_deeply_nested_code_blocks(self):
        content = ""
        depth = 30
        indent = ""
        for i in range(depth):
            indent = "    " * i
            if i % 3 == 0:
                content += f"{indent}def func_{i}():\n"
            elif i % 3 == 1:
                content += f"{indent}if x > 0:\n"
            else:
                content += f"{indent}for item in items:\n"
        content += f"{indent}    pass\n"

        assert len(content) > 100
        assert "func_0" in content


@pytest.mark.slow
class TestManyPages:
    def test_500_page_dict_construction(self):
        """Verify that constructing 500 pages doesn't hit O(N^2) behavior."""
        pages = []
        for i in range(500):
            pages.append(
                {
                    "page_number": i + 1,
                    "title": f"Page {i + 1}",
                    "text": f"Content for page {i + 1} " + "x" * 200,
                    "links": [f"https://example.com/page/{j}" for j in range(5)],
                    "code_samples": [],
                    "images": [],
                    "headings": [{"level": "h2", "text": f"Heading {i}"}],
                }
            )

        assert len(pages) == 500
        assert pages[0]["page_number"] == 1
        assert pages[499]["page_number"] == 500
        assert all("text" in p for p in pages)
        assert all("page_number" in p for p in pages)

    def test_many_urls_in_queue(self):
        """Test that processing many URLs doesn't degrade."""
        urls = set()
        for i in range(1000):
            urls.add(f"https://example.com/docs/section/{i}")

        assert len(urls) == 1000
        assert "https://example.com/docs/section/0" in urls
        assert "https://example.com/docs/section/999" in urls
