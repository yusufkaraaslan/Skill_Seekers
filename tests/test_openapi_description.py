"""Regression tests for OpenAPI skill trigger descriptions."""

from skill_seekers.cli.openapi_scraper import OpenAPIToSkillConverter, infer_description_from_spec


def test_declarative_xquik_summary_stays_grammatical() -> None:
    """Keep a complete API summary separate from its trigger sentence."""
    info = {
        "title": "Xquik API",
        "description": ("Xquik is an independent third-party service. Not affiliated with X Corp."),
    }

    assert infer_description_from_spec(info) == (
        "Xquik is an independent third-party service. Use when working with the Xquik API."
    )


def test_existing_use_when_description_is_not_prefixed_twice() -> None:
    """Preserve source metadata that already supplies a trigger."""
    info = {
        "title": "Example API",
        "description": "Use when searching public posts by keyword.",
    }

    assert infer_description_from_spec(info) == "Use when searching public posts by keyword."


def test_api_suffix_is_not_duplicated() -> None:
    """Avoid output such as 'Example API API' in title fallbacks."""
    assert infer_description_from_spec({"title": "Example API"}) == (
        "Use when working with the Example API."
    )


def test_description_uses_only_first_sentence() -> None:
    """Keep generated frontmatter concise when the source has several sentences."""
    info = {
        "title": "Example",
        "description": "Search public records! This sentence should not appear.",
    }

    assert infer_description_from_spec(info) == (
        "Search public records! Use when working with the Example API."
    )


def test_generated_xquik_skill_has_valid_frontmatter(tmp_path) -> None:
    """Protect the full OpenAPI extraction and skill-generation path."""
    spec_path = tmp_path / "xquik-openapi.yaml"
    spec_path.write_text(
        """\
openapi: 3.1.0
info:
  title: Xquik API
  version: "1.0"
  description: Xquik is an independent third-party service. Not affiliated with X Corp.
paths:
  /x/tweets/search:
    get:
      summary: Search public posts
      responses:
        "200":
          description: Search results
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "xquik-api"
    converter = OpenAPIToSkillConverter(
        {
            "name": "xquik-api",
            "spec_path": str(spec_path),
            "output_dir": str(output_dir),
        }
    )

    assert converter.run() == 0
    skill = (output_dir / "SKILL.md").read_text(encoding="utf-8")
    assert (
        "description: Xquik is an independent third-party service. "
        "Use when working with the Xquik API."
    ) in skill
    assert "Use when working with xquik is" not in skill
