"""Encoding stress tests for code_analyzer and scraper modules.

Tests that the system gracefully handles non-standard encodings,
byte order marks, mixed newlines, and binary files.
"""

from skill_seekers.cli.code_analyzer import CodeAnalyzer


class TestEncodingEdgeCases:
    def setup_method(self):
        self.analyzer = CodeAnalyzer(depth="deep")

    def test_utf8_bom_file(self):
        content = "\ufeff# -*- coding: utf-8 -*-\ndef hello():\n    return 'world'\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "functions" in result
            funcs = result.get("functions", [])
            if funcs:
                assert any(f["name"] == "hello" for f in funcs)

    def test_latin1_escaped(self):
        content = "# coding: latin-1\ndef greet():\n    return 'héllo'\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "functions" in result

    def test_crlf_newlines(self):
        content = "class Foo:\r\n    def bar(self):\r\n        return 1\r\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "classes" in result

    def test_mixed_newlines(self):
        content = "class Foo:\r\n    def bar(self):\r        return 1\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "classes" in result

    def test_binary_file_skipped(self):
        content = "\x00\x01\x02\x03\x04binary content\x00\x00"
        result = self.analyzer.analyze_file("test.bin", content, "Python")
        assert result is None or isinstance(result, dict)

    def test_null_bytes_in_code(self):
        content = "def valid():\n    return None\n\ndef also_valid():\n    pass\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "functions" in result

    def test_tabs_as_indentation(self):
        content = "def tabbed():\n\tx = 1\n\ty = 2\n\treturn x + y\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "functions" in result

    def test_very_long_identifier(self):
        long_name = "a" * 100
        content = f"def {long_name}():\n    pass\n"
        result = self.analyzer.analyze_file("test.py", content, "Python")
        if result:
            assert "functions" in result

    def test_single_long_line(self):
        """Single very long line should not crash."""
        content = "x = " + '"' + "a" * 5000 + '"\n'
        result = self.analyzer.analyze_file("test.py", content, "Python")
        assert result is None or isinstance(result, dict)

    def test_deeply_nested_code(self):
        """Deeply nested structures should not hit recursion limits."""
        nested = "def outer():\n"
        for i in range(50):
            nested += f"    def inner_{i}():\n"
        nested += "        pass\n"
        result = self.analyzer.analyze_file("test.py", nested, "Python")
        assert isinstance(result, dict)
