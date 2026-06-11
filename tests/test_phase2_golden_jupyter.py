"""Golden-output tests for the Jupyter scraper (Phase 2 port).

The golden trees under tests/golden/phase2/jupyter*/ were captured from the
PRE-DocumentSkillBuilder code; these tests prove the port is byte-identical.
The fixtures exercise every build path: markdown/code/raw cells, execution
counts (present and None), output text/errors/rich display, cell tags,
tables with and without headers, sub-headings, >500-char code, imports,
kernelspec/language_info metadata, language stats, and all three
categorization branches (single notebook file, keyword categories incl. an
empty category, topic auto-bucketing with an "other" fallback) plus the
directory-source path (notebook_path set but not a file).
"""

import copy

from tests.phase2_golden_utils import assert_matches_golden, build_snapshot

LONG_CODE = "def long_example():\n" + "\n".join(f"    x{i} = {i}" for i in range(60))

SECTIONS = [
    {
        # Markdown cell with sub-heading, tags, and a code fence sample
        "section_number": 1,
        "heading": "Getting Started",
        "heading_level": "h1",
        "text": "Welcome to the analysis notebook. Installation and setup steps.",
        "headings": [{"level": "h3", "text": "Verify Setup"}],
        "code_samples": [
            {"code": "pip install pandas", "language": "bash", "quality_score": 5.0},
        ],
        "tables": [],
        "images": [],
        "cell_type": "markdown",
        "cell_index": 0,
        "tags": ["intro", "setup"],
        "source_notebook": "analysis.ipynb",
    },
    {
        # Code cell with execution count, output text, and rich display
        "section_number": 2,
        "heading": "Assign: df",
        "heading_level": "h3",
        "text": "   col1  col2\n0     1     3",
        "headings": [],
        "code_samples": [
            {
                "code": "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf.head()",
                "language": "python",
                "quality_score": 7.5,
                "execution_count": 2,
            },
        ],
        "tables": [],
        "images": [],
        "cell_type": "code",
        "cell_index": 1,
        "tags": [],
        "source_notebook": "analysis.ipynb",
        "execution_count": 2,
        "output_text": "   col1  col2\n0     1     3",
        "output_errors": [],
        "output_display": [{"mime_type": "text/html", "has_data": True}],
    },
    {
        # Code cell WITHOUT execution count, with an error output
        "section_number": 3,
        "heading": "Magic: %timeit",
        "heading_level": "h3",
        "text": "",
        "headings": [],
        "code_samples": [
            {
                "code": "%timeit broken()",
                "language": "python",
                "quality_score": 2.0,
                "execution_count": None,
            },
        ],
        "tables": [],
        "images": [],
        "cell_type": "code",
        "cell_index": 2,
        "tags": ["raises-exception"],
        "source_notebook": "analysis.ipynb",
        "execution_count": None,
        "output_text": "",
        "output_errors": ["NameError: name 'broken' is not defined\nTraceback line 1"],
        "output_display": [],
    },
    {
        # Raw cell
        "section_number": 4,
        "heading": "",
        "heading_level": "h3",
        "text": "raw front-matter content",
        "headings": [],
        "code_samples": [],
        "tables": [],
        "images": [],
        "cell_type": "raw",
        "cell_index": 3,
        "tags": [],
        "source_notebook": "analysis.ipynb",
    },
    {
        # Markdown cell with long code (>500 chars) and both table shapes
        "section_number": 5,
        "heading": "Modeling Results",
        "heading_level": "h2",
        "text": "Model evaluation summary with accuracy and recall metrics.",
        "headings": [{"level": "h4", "text": "Confusion Matrix"}],
        "code_samples": [
            {"code": LONG_CODE, "language": "python", "quality_score": 9.5},
        ],
        "tables": [
            {"headers": ["Metric", "Value"], "rows": [["accuracy", "0.95"], ["recall", "0.91"]]},
            # Headerless table exercises the no-headers rendering path
            {"headers": [], "rows": [["a", "b"], ["c", "d"]]},
        ],
        "images": [],
        "cell_type": "markdown",
        "cell_index": 4,
        "tags": [],
        "source_notebook": "analysis.ipynb",
    },
]


def _extracted_data(metadata: dict) -> dict:
    return {
        "source_file": "analysis.ipynb",
        "metadata": metadata,
        "total_sections": 5,
        "total_code_blocks": 2,
        "total_markdown_cells": 2,
        "total_raw_cells": 1,
        "total_notebooks": 1,
        "languages_detected": {"python": 3, "bash": 1},
        "imports": ["numpy", "pandas", "sklearn"],
        "pages": copy.deepcopy(SECTIONS),
    }


FULL_METADATA = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.4"},
}


def _make_converter(tmp_path, name, **overrides):
    from skill_seekers.cli.jupyter_scraper import JupyterToSkillConverter

    config = {
        "name": name,
        "description": f"Use when testing the {name} golden build",
        "output_dir": str(tmp_path / "skill"),
    }
    config.update(overrides)
    return JupyterToSkillConverter(config)


def test_jupyter_single_notebook_matches_golden(tmp_path):
    """notebook_path is a real file → single-category (notebook stem) branch."""
    nb_file = tmp_path / "analysis.ipynb"
    nb_file.write_text("{}", encoding="utf-8")

    converter = _make_converter(tmp_path, "golden_jupyter", notebook_path=str(nb_file))
    converter.extracted_data = _extracted_data(FULL_METADATA)
    assert_matches_golden(build_snapshot(converter), "jupyter")


def test_jupyter_keyword_categorization_matches_golden(tmp_path):
    """Explicit categories → keyword scoring over text+heading+code, plus an
    empty category (section_NN.md fallback + N/A range) and 'other' bucket."""
    converter = _make_converter(
        tmp_path,
        "golden_jupyter_kw",
        categories={
            "setup": ["install", "setup"],
            "modeling": ["accuracy", "recall", "model"],
            "loading": ["read_csv"],  # matches only inside code samples
            "empty_cat": ["zzz-no-match"],
        },
    )
    converter.extracted_data = _extracted_data({})
    assert_matches_golden(build_snapshot(converter), "jupyter_kw")


def test_jupyter_topic_autocategorization_matches_golden(tmp_path):
    """No path, no categories → _TOPIC_KEYWORDS auto-bucketing (score >= 2)
    with uncategorized sections falling through to 'other'."""
    converter = _make_converter(tmp_path, "golden_jupyter_topics")
    converter.extracted_data = _extracted_data(FULL_METADATA)
    assert_matches_golden(build_snapshot(converter), "jupyter_topics")


def test_jupyter_directory_source_matches_golden(tmp_path):
    """notebook_path is a DIRECTORY → not the single-file branch, and the
    reference-filename stem stays '' (section_*.md naming, not the dir name)."""
    nb_dir = tmp_path / "notebooks"
    nb_dir.mkdir()

    converter = _make_converter(tmp_path, "golden_jupyter_dir", notebook_path=str(nb_dir))
    converter.extracted_data = _extracted_data(FULL_METADATA)
    assert_matches_golden(build_snapshot(converter), "jupyter_dir")
