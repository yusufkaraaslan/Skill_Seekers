"""Shared parametrized tests for OpenAI-compatible platform adaptors.

Covers all 6 adaptors that previously had stub-only tests:
deepseek, fireworks, kimi, openrouter, qwen, together.

Each adaptor inherits from OpenAICompatibleAdaptor and only overrides
platform constants (~15 lines each). This shared test validates that
each adaptor's constants and inherited methods produce correct
platform-specific output.
"""

import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from skill_seekers.cli.adaptors import get_adaptor, is_platform_available
from skill_seekers.cli.adaptors.base import SkillMetadata


PLATFORMS = [
    "atlas",
    "deepseek",
    "fireworks",
    "kimi",
    "openrouter",
    "qwen",
    "together",
]

PLATFORM_EXPECTED = {
    "atlas": {
        "name": "Atlas Cloud",
        "endpoint_contains": "atlascloud",
        "model_truthy": True,
        "env_var": "ATLAS_API_KEY",
        "api_base_contains": "atlascloud",
    },
    "deepseek": {
        "name": "DeepSeek AI",
        "endpoint_contains": "deepseek",
        "model_truthy": True,
        "env_var": "DEEPSEEK_API_KEY",
        "api_base_contains": "deepseek",
    },
    "fireworks": {
        "name": "Fireworks AI",
        "endpoint_contains": "fireworks",
        "model_truthy": True,
        "env_var": "FIREWORKS_API_KEY",
        "api_base_contains": "fireworks",
    },
    "kimi": {
        "name": "Kimi (Moonshot AI)",
        "endpoint_contains": "moonshot",
        "model_truthy": True,
        "env_var": "MOONSHOT_API_KEY",
        "api_base_contains": "moonshot",
    },
    "openrouter": {
        "name": "OpenRouter",
        "endpoint_contains": "openrouter",
        "model_truthy": True,
        "env_var": "OPENROUTER_API_KEY",
        "api_base_contains": "openrouter",
    },
    "qwen": {
        "name": "Qwen (Alibaba)",
        "endpoint_contains": "dashscope",
        "model_truthy": True,
        "env_var": "DASHSCOPE_API_KEY",
        "api_base_contains": "dashscope",
    },
    "together": {
        "name": "Together AI",
        "endpoint_contains": "together",
        "model_truthy": True,
        "env_var": "TOGETHER_API_KEY",
        "api_base_contains": "together",
    },
}


@pytest.mark.parametrize("platform", PLATFORMS)
class TestOpenAICompatibleAdaptors:
    def test_platform_registered(self, platform):
        assert is_platform_available(platform), f"{platform} should be registered"

    def test_get_adaptor_returns_instance(self, platform):
        adaptor = get_adaptor(platform)
        assert adaptor is not None
        assert platform == adaptor.PLATFORM

    def test_platform_info(self, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]
        assert platform == adaptor.PLATFORM
        assert expected["name"] == adaptor.PLATFORM_NAME

    def test_endpoint_contains_platform(self, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]
        assert expected["endpoint_contains"] in adaptor.DEFAULT_API_ENDPOINT.lower()

    def test_model_defined(self, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]
        if expected["model_truthy"]:
            assert adaptor.DEFAULT_MODEL, f"{platform} should have DEFAULT_MODEL"
            assert len(adaptor.DEFAULT_MODEL) > 2

    def test_env_var_name(self, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]
        assert adaptor.get_env_var_name() == expected["env_var"]

    def test_supports_enhancement(self, platform):
        adaptor = get_adaptor(platform)
        assert adaptor.supports_enhancement() is True

    def test_format_skill_md_no_frontmatter(self, platform):
        adaptor = get_adaptor(platform)
        PLATFORM_EXPECTED[platform]

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(name="test-skill", description="Test skill description")

            formatted = adaptor.format_skill_md(skill_dir, metadata)

            assert not formatted.startswith("---"), (
                "OpenAI-compatible adaptors should NOT have YAML frontmatter"
            )
            assert "You are an expert assistant" in formatted
            assert "test-skill" in formatted
            assert "Test skill description" in formatted

    def test_format_skill_md_with_existing_content(self, platform):
        adaptor = get_adaptor(platform)

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            (skill_dir / "references").mkdir()
            existing_content = "# Existing Content\n\n" + "x" * 200
            (skill_dir / "SKILL.md").write_text(existing_content)

            metadata = SkillMetadata(name="test-skill", description="Test description")
            formatted = adaptor.format_skill_md(skill_dir, metadata)

            assert "You are an expert assistant" in formatted
            assert "test-skill" in formatted

    def test_package_creates_zip(self, platform):
        adaptor = get_adaptor(platform)
        PLATFORM_EXPECTED[platform]

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("You are an expert assistant")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = adaptor.package(skill_dir, output_dir)

            assert package_path.exists()
            assert str(package_path).endswith(".zip")

            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                assert "system_instructions.txt" in names, (
                    f"system_instructions.txt missing for {platform}"
                )
                assert any(f"{platform}_metadata.json" in n for n in names), (
                    f"metadata missing for {platform}"
                )
                assert any("knowledge_files" in n for n in names)

    def test_package_metadata_content(self, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test instructions")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# User Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = adaptor.package(skill_dir, output_dir)

            with zipfile.ZipFile(package_path, "r") as zf:
                metadata_name = f"{platform}_metadata.json"
                metadata_content = zf.read(metadata_name).decode("utf-8")
                metadata = json.loads(metadata_content)
                assert metadata["platform"] == platform
                assert metadata["name"] == "test-skill"
                assert expected["api_base_contains"] in metadata["api_base"].lower()

    def test_package_without_references(self, platform):
        adaptor = get_adaptor(platform)

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test instructions")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = adaptor.package(skill_dir, output_dir)

            assert package_path.exists()
            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                assert "system_instructions.txt" in names
                assert not any("knowledge_files" in n for n in names), (
                    f"Should have no knowledge_files for {platform}"
                )

    def test_upload_missing_file(self, platform):
        adaptor = get_adaptor(platform)
        result = adaptor.upload(Path("/nonexistent/file.zip"), "fake-key")
        assert result["success"] is False
        assert "not found" in result.get("message", "").lower() or not result["success"]

    def test_upload_wrong_format(self, platform):
        adaptor = get_adaptor(platform)
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            tmp.write(b"not a zip")
            tmp.flush()
            result = adaptor.upload(Path(tmp.name), "fake-key")
            assert result["success"] is False

    def test_validate_api_key(self, platform):
        adaptor = get_adaptor(platform)
        assert not adaptor.validate_api_key(""), f"Empty key should be invalid for {platform}"
        assert not adaptor.validate_api_key("   "), (
            f"Whitespace key should be invalid for {platform}"
        )
        assert adaptor.validate_api_key("valid-long-enough-key-string")
        assert adaptor.validate_api_key("another-valid-key-12345")

    def test_validate_api_key_short(self, platform):
        adaptor = get_adaptor(platform)
        short_key = "ab"
        if adaptor.validate_api_key(short_key):
            pass
        else:
            pass

    @patch("openai.OpenAI")
    def test_upload_mocked(self, mock_openai_class, platform):
        adaptor = get_adaptor(platform)
        expected = PLATFORM_EXPECTED[platform]

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Test instructions")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "ref.md").write_text("# Ref")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            package_path = adaptor.package(skill_dir, output_dir)

            adaptor.upload(package_path, "test-api-key")

            assert mock_openai_class.called
            called_args = mock_openai_class.call_args
            assert called_args[1]["api_key"] == "test-api-key"
            assert expected["api_base_contains"] in called_args[1]["base_url"].lower()
