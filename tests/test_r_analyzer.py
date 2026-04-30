#!/usr/bin/env python3
"""Tests for R language support in skill-seekers.

Node-type reference (tree-sitter-language-pack R grammar):
  - Assignments: binary_operator with operator field "<-" or "="
  - Function body: function_definition with parameters + body fields
  - Library calls: call node (function field = identifier, arguments field)
  - Comments: comment node (text starts with "#'" for roxygen, "#" for inline)
  - No expression_statement wrapper — root.children are direct statement nodes
"""

import unittest

try:
    from skill_seekers.cli.codebase_scraper import LANGUAGE_EXTENSIONS
    from skill_seekers.cli.test_example_extractor import TestExampleExtractor

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

try:
    from skill_seekers.cli.code_analyzer import CodeAnalyzer

    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

try:
    from tree_sitter_language_pack import get_parser as _get_ts_parser

    _R_PARSER = _get_ts_parser("r")
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


def _parse_r(code: str):
    """Parse R code string, return root node."""
    return _R_PARSER.parse(bytes(code, "utf8")).root_node


# ---------------------------------------------------------------------------
# Extension registration
# ---------------------------------------------------------------------------


class TestRExtensionRegistration(unittest.TestCase):
    """R file extensions are registered in both language maps."""

    def setUp(self):
        if not IMPORTS_AVAILABLE:
            self.skipTest("skill_seekers not importable")

    def test_dot_R_registered_in_codebase_scraper(self):
        self.assertEqual(LANGUAGE_EXTENSIONS.get(".R"), "R")

    def test_dot_r_registered_in_codebase_scraper(self):
        self.assertEqual(LANGUAGE_EXTENSIONS.get(".r"), "R")

    def test_Rmd_registered_in_codebase_scraper(self):
        self.assertEqual(LANGUAGE_EXTENSIONS.get(".Rmd"), "R")

    def test_qmd_registered_in_codebase_scraper(self):
        self.assertEqual(LANGUAGE_EXTENSIONS.get(".qmd"), "R")

    def test_dot_R_registered_in_test_extractor(self):
        self.assertEqual(TestExampleExtractor.LANGUAGE_MAP.get(".R"), "R")

    def test_dot_r_registered_in_test_extractor(self):
        self.assertEqual(TestExampleExtractor.LANGUAGE_MAP.get(".r"), "R")

    def test_Rmd_registered_in_test_extractor(self):
        self.assertEqual(TestExampleExtractor.LANGUAGE_MAP.get(".Rmd"), "R")


# ---------------------------------------------------------------------------
# Dispatch routing
# ---------------------------------------------------------------------------


class TestRDispatch(unittest.TestCase):
    """analyze_file() routes language='R' to _analyze_r()."""

    def setUp(self):
        if not ANALYZER_AVAILABLE:
            self.skipTest("CodeAnalyzer not importable")
        self.analyzer = CodeAnalyzer(depth="deep")

    def test_r_language_returns_dict_with_functions_key(self):
        """analyze_file with language='R' must not fall through to empty {}."""
        code = "add <- function(x, y) { x + y }"
        result = self.analyzer.analyze_file("test.R", code, "R")
        self.assertIsInstance(result, dict)
        self.assertIn("functions", result)

    def test_r_language_result_has_all_required_keys(self):
        result = self.analyzer.analyze_file("empty.R", "", "R")
        for key in ("classes", "functions", "comments", "imports"):
            self.assertIn(key, result)


# ---------------------------------------------------------------------------
# Helper method unit tests
# ---------------------------------------------------------------------------


class TestRHelpers(unittest.TestCase):
    """Unit tests for the 5 CodeAnalyzer R helper methods.

    Grammar note: assignments are binary_operator nodes.
    Fields: lhs, rhs, operator (text: '<-', '=', '->')
    No expression_statement wrapper around root children.
    """

    def setUp(self):
        if not ANALYZER_AVAILABLE or not TREE_SITTER_AVAILABLE:
            self.skipTest("CodeAnalyzer or tree-sitter-language-pack not available")
        self.analyzer = CodeAnalyzer(depth="deep")

    # --- _r_assignment_parts ---

    def test_assignment_parts_left_arrow(self):
        root = _parse_r("f <- function(x) x")
        node = root.children[0]  # binary_operator directly, no expression_statement wrapper
        lhs, rhs = self.analyzer._r_assignment_parts(node)
        self.assertEqual(lhs, "f")
        self.assertIsNotNone(rhs)
        self.assertEqual(rhs.type, "function_definition")

    def test_assignment_parts_equals(self):
        root = _parse_r("g = function(y) y")
        node = root.children[0]
        lhs, rhs = self.analyzer._r_assignment_parts(node)
        self.assertEqual(lhs, "g")
        self.assertIsNotNone(rhs)

    def test_assignment_parts_non_assignment_returns_none(self):
        root = _parse_r("x + y")
        node = root.children[0]
        lhs, rhs = self.analyzer._r_assignment_parts(node)
        # x + y is also binary_operator but operator is not an assignment op
        self.assertIsNone(lhs)

    # --- _r_collect_roxygen ---

    def test_roxygen_collected_before_function(self):
        code = "#' @param x numeric input\n#' @return numeric\nfoo <- function(x) x"
        lines = code.splitlines()
        root = _parse_r(code)
        # The assignment is on line 3 (index 2); root.children may have comments + assign
        # Find the binary_operator node
        assign_node = next(n for n in root.children if n.type == "binary_operator")
        doc = self.analyzer._r_collect_roxygen(assign_node, lines)
        self.assertIsNotNone(doc)
        self.assertIn("@param x", doc)
        self.assertIn("@return", doc)

    def test_roxygen_none_when_no_preceding_comments(self):
        code = "bar <- function(x) x"
        lines = code.splitlines()
        root = _parse_r(code)
        node = root.children[0]
        doc = self.analyzer._r_collect_roxygen(node, lines)
        self.assertIsNone(doc)

    # --- _r_extract_function ---

    def test_extract_function_name_and_params(self):
        root = _parse_r("calc <- function(x, n = 20) x + n")
        node = root.children[0]
        lhs, rhs = self.analyzer._r_assignment_parts(node)
        func = self.analyzer._r_extract_function(lhs, rhs, None)
        self.assertIsNotNone(func)
        self.assertEqual(func["name"], "calc")
        self.assertEqual(len(func["parameters"]), 2)
        self.assertEqual(func["parameters"][0]["name"], "x")
        self.assertEqual(func["parameters"][1]["name"], "n")
        self.assertEqual(func["parameters"][1]["default"], "20")

    def test_extract_function_with_dots(self):
        root = _parse_r("wrap <- function(x, ...) x")
        node = root.children[0]
        lhs, rhs = self.analyzer._r_assignment_parts(node)
        func = self.analyzer._r_extract_function(lhs, rhs, None)
        param_names = [p["name"] for p in func["parameters"]]
        self.assertIn("...", param_names)

    # --- _r_extract_import ---

    def test_extract_library_bare_name(self):
        root = _parse_r("library(data.table)")
        node = root.children[0]
        pkg = self.analyzer._r_extract_import(node)
        self.assertEqual(pkg, "data.table")

    def test_extract_require_quoted_name(self):
        root = _parse_r('require("ggplot2")')
        node = root.children[0]
        pkg = self.analyzer._r_extract_import(node)
        self.assertEqual(pkg, "ggplot2")


# ---------------------------------------------------------------------------
# Full _analyze_r() integration tests
# ---------------------------------------------------------------------------


class TestRAnalyzerIntegration(unittest.TestCase):
    """Full _analyze_r() integration tests with realistic R code."""

    FEATURES_R = """
#' Calculate Order Flow Imbalance
#'
#' @param bid_volume numeric bid volume
#' @param ask_volume numeric ask volume
#' @return numeric OFI value
calculate_ofi <- function(bid_volume, ask_volume) {
  (bid_volume - ask_volume) / (bid_volume + ask_volume)
}

#' Calculate EMA-based OFI
#'
#' @param ofi numeric OFI series
#' @param n integer window length
#' @return numeric EMA of OFI
calculate_ema_ofi <- function(ofi, n = 20) {
  TTR::EMA(ofi, n = n)
}

library(data.table)
require(TTR)

# internal helper
.normalize <- function(x) (x - mean(x)) / sd(x)
"""

    def setUp(self):
        if not ANALYZER_AVAILABLE or not TREE_SITTER_AVAILABLE:
            self.skipTest("CodeAnalyzer or tree-sitter-language-pack not available")
        self.analyzer = CodeAnalyzer(depth="deep")

    def test_functions_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        names = [f["name"] for f in result["functions"]]
        self.assertIn("calculate_ofi", names)
        self.assertIn("calculate_ema_ofi", names)
        self.assertIn(".normalize", names)

    def test_function_parameters_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        ema_func = next(f for f in result["functions"] if f["name"] == "calculate_ema_ofi")
        param_names = [p["name"] for p in ema_func["parameters"]]
        self.assertIn("ofi", param_names)
        self.assertIn("n", param_names)

    def test_default_parameter_value_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        ema_func = next(f for f in result["functions"] if f["name"] == "calculate_ema_ofi")
        n_param = next(p for p in ema_func["parameters"] if p["name"] == "n")
        self.assertEqual(n_param["default"], "20")

    def test_roxygen_docstring_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        ofi_func = next(f for f in result["functions"] if f["name"] == "calculate_ofi")
        self.assertIsNotNone(ofi_func["docstring"])
        self.assertIn("@param", ofi_func["docstring"])

    def test_imports_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        self.assertIn("data.table", result["imports"])
        self.assertIn("TTR", result["imports"])

    def test_imports_deduplicated(self):
        code = "library(data.table)\nlibrary(data.table)"
        result = self.analyzer.analyze_file("dup.R", code, "R")
        self.assertEqual(result["imports"].count("data.table"), 1)

    def test_inline_comments_extracted(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        inline = [c for c in result["comments"] if c["type"] == "inline"]
        self.assertTrue(any("internal helper" in c["text"] for c in inline))

    def test_roxygen_comments_typed_as_doc(self):
        result = self.analyzer.analyze_file("features.R", self.FEATURES_R, "R")
        doc_comments = [c for c in result["comments"] if c["type"] == "doc"]
        self.assertTrue(len(doc_comments) > 0)

    def test_r6class_extracted(self):
        code = """
MyEnv <- R6Class("MyEnv",
  public = list(
    initialize = function(data) {
      self$data <- data
    },
    step = function(action) {
      invisible(NULL)
    }
  )
)
"""
        result = self.analyzer.analyze_file("env.R", code, "R")
        class_names = [c["name"] for c in result["classes"]]
        self.assertIn("MyEnv", class_names)
        env_class = next(c for c in result["classes"] if c["name"] == "MyEnv")
        method_names = [m["name"] for m in env_class["methods"]]
        self.assertIn("initialize", method_names)
        self.assertIn("step", method_names)

    def test_result_has_required_keys(self):
        result = self.analyzer.analyze_file("empty.R", "", "R")
        for key in ("classes", "functions", "comments", "imports"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
