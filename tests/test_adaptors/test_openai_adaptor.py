#!/usr/bin/env python3
"""
Tests for OpenAI adaptor
"""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestOpenAIAdaptor(unittest.TestCase):
    """Test OpenAI adaptor functionality"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor("openai")

    def test_platform_info(self):
        """Test platform identifiers"""
        self.assertEqual(self.adaptor.PLATFORM, "openai")
        self.assertEqual(self.adaptor.PLATFORM_NAME, "OpenAI ChatGPT")
        self.assertIsNotNone(self.adaptor.DEFAULT_API_ENDPOINT)

    def test_validate_api_key_valid(self):
        """Test valid OpenAI API keys"""
        self.assertTrue(self.adaptor.validate_api_key("sk-proj-abc123"))
        self.assertTrue(self.adaptor.validate_api_key("sk-abc123"))
        self.assertTrue(self.adaptor.validate_api_key("  sk-test  "))  # with whitespace

    def test_validate_api_key_invalid(self):
        """Test invalid API keys"""
        self.assertFalse(self.adaptor.validate_api_key("AIzaSyABC123"))  # Gemini key
        # Note: Can't distinguish Claude keys (sk-ant-*) from OpenAI keys (sk-*)
        self.assertFalse(self.adaptor.validate_api_key("invalid"))
        self.assertFalse(self.adaptor.validate_api_key(""))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        self.assertEqual(self.adaptor.get_env_var_name(), "OPENAI_API_KEY")

    def test_supports_enhancement(self):
        """Test enhancement support"""
        self.assertTrue(self.adaptor.supports_enhancement())

    def test_format_skill_md_no_frontmatter(self):
        """Test that OpenAI format has no YAML frontmatter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            # Create minimal skill structure
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Test content")

            metadata = SkillMetadata(name="test-skill", description="Test skill description")

            formatted = self.adaptor.format_skill_md(skill_dir, metadata)

            # Should NOT start with YAML frontmatter
            self.assertFalse(formatted.startswith("---"))
            # Should contain assistant-style instructions
            self.assertIn("You are an expert assistant", formatted)
            self.assertIn("test-skill", formatted)
            self.assertIn("Test skill description", formatted)

    def test_package_creates_zip(self):
        """Test that package creates ZIP file with correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create minimal skill structure
            (skill_dir / "SKILL.md").write_text("You are an expert assistant")
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "test.md").write_text("# Reference")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package skill
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists())
            self.assertTrue(str(package_path).endswith(".zip"))
            self.assertIn("openai", package_path.name)

            # Verify package contents
            with zipfile.ZipFile(package_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("assistant_instructions.txt", names)
                self.assertIn("openai_metadata.json", names)
                # Should have vector store files
                self.assertTrue(any("vector_store_files" in name for name in names))

    def test_upload_missing_library(self):
        """Test upload when openai library is not installed"""
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            # Simulate missing library by patching sys.modules
            with patch.dict(sys.modules, {"openai": None}):
                result = self.adaptor.upload(Path(tmp.name), "sk-test123")

            self.assertFalse(result["success"])
            self.assertIn("openai", result["message"])
            self.assertIn("not installed", result["message"])

    def test_package_preserves_nested_reference_paths_and_selected_model(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "manual"
            for topic in ("cli", "api"):
                folder = skill / "references" / topic
                folder.mkdir(parents=True)
                (folder / "index.md").write_text(topic)
            (skill / "SKILL.md").write_text("# Manual")
            adaptor = get_adaptor("openai", {"custom_model": "my-model"})
            with zipfile.ZipFile(adaptor.package(skill, root)) as archive:
                for topic in ("cli", "api"):
                    self.assertEqual(
                        archive.read(f"vector_store_files/{topic}/index.md"), topic.encode()
                    )
                self.assertEqual(
                    json.loads(archive.read("openai_metadata.json"))["model"], "my-model"
                )

    def test_upload_invalid_file(self):
        """Test upload with invalid file"""
        result = self.adaptor.upload(Path("/nonexistent/file.zip"), "sk-test123")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())

    def test_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp:
            result = self.adaptor.upload(Path(tmp.name), "sk-test123")

            self.assertFalse(result["success"])
            self.assertIn("not a zip", result["message"].lower())

    def test_enhance_success(self):
        """Test successful enhancement - skipped (needs real API for integration test)"""
        pass

    def test_enhance_missing_library(self):
        """Test enhance when openai library is not installed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "test.md").write_text("Test")

            with patch.dict(sys.modules, {"openai": None}):
                success = self.adaptor.enhance(skill_dir, "sk-test123")

            self.assertFalse(success)

    def test_package_includes_instructions(self):
        """Test that packaged ZIP includes assistant instructions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "test-skill"
            skill_dir.mkdir()

            # Create SKILL.md
            skill_md_content = "You are an expert assistant for testing."
            (skill_dir / "SKILL.md").write_text(skill_md_content)

            # Create references
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "guide.md").write_text("# User Guide")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Package
            package_path = self.adaptor.package(skill_dir, output_dir)

            # Verify contents
            with zipfile.ZipFile(package_path, "r") as zf:
                # Read instructions
                instructions = zf.read("assistant_instructions.txt").decode("utf-8")
                self.assertEqual(instructions, skill_md_content)

                # Verify vector store file
                self.assertIn("vector_store_files/guide.md", zf.namelist())

                # Verify metadata
                metadata_content = zf.read("openai_metadata.json").decode("utf-8")
                import json

                metadata = json.loads(metadata_content)
                self.assertEqual(metadata["platform"], "openai")
                self.assertEqual(metadata["name"], "test-skill")
                self.assertIn("file_search", metadata["tools"])


@pytest.fixture
def upload_client(monkeypatch):
    client = MagicMock()
    sdk = MagicMock()
    sdk.NotFoundError = FileNotFoundError
    sdk.OpenAI.return_value.__enter__.return_value = client
    monkeypatch.setitem(sys.modules, "openai", sdk)
    client.vector_stores.create.return_value.id = "vs_123"
    return client


def upload_package(tmp_path, ref_count=2):
    package = tmp_path / "test-openai.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("assistant_instructions.txt", "Use these references.")
        archive.writestr(
            "openai_metadata.json", json.dumps({"name": "test", "model": "chosen-model"})
        )
        for i in range(ref_count):
            archive.writestr(f"vector_store_files/{i}/index.md", f"Reference {i}")
    return package


@pytest.mark.parametrize("ref_count", [0, 2, 501])
def test_publish_responses_knowledge_base(tmp_path, upload_client, ref_count):
    client = upload_client
    client.files.create.side_effect = [
        SimpleNamespace(id=f"file_{i}") for i in range(ref_count + 1)
    ]
    batches = client.vector_stores.file_batches.create_and_poll
    batches.side_effect = lambda file_ids, **_kwargs: SimpleNamespace(
        status="completed", file_counts=SimpleNamespace(completed=len(file_ids))
    )
    result = get_adaptor("openai").upload(upload_package(tmp_path, ref_count), "sk-test")
    assert result["success"], result["message"]
    assert result["skill_id"] == result["vector_store_id"] == "vs_123"
    assert result["model"] == "chosen-model"
    assert result["instructions_file_id"] == "file_0"
    client.vector_stores.create.assert_called_once_with(
        name="test Documentation",
        metadata={"instructions_file_id": "file_0", "model": "chosen-model"},
    )
    assert client.files.create.call_args_list[0] == call(
        file=("assistant_instructions.txt", b"Use these references."), purpose="user_data"
    )
    ids = [f"file_{i + 1}" for i in range(ref_count)]
    assert batches.call_args_list == [
        call(vector_store_id="vs_123", file_ids=ids[i : i + 500]) for i in range(0, ref_count, 500)
    ]
    client.files.delete.assert_not_called()
    client.vector_stores.delete.assert_not_called()


@pytest.mark.parametrize("status, completed", [("failed", 0), ("cancelled", 0), ("completed", 1)])
def test_partial_indexing_rolls_back(tmp_path, upload_client, status, completed):
    client = upload_client
    client.files.create.side_effect = [
        SimpleNamespace(id=x) for x in ("instructions", "ref1", "ref2")
    ]
    client.vector_stores.file_batches.create_and_poll.return_value = SimpleNamespace(
        id="batch_123", status=status, file_counts=SimpleNamespace(completed=completed)
    )
    result = get_adaptor("openai").upload(upload_package(tmp_path), "sk-test")
    assert not result["success"] and result["skill_id"] is None
    assert "batch_123" in result["message"]
    client.vector_stores.delete.assert_called_once_with("vs_123")
    assert client.files.delete.call_args_list == [call("ref2"), call("ref1"), call("instructions")]


def test_upload_failure_reports_cleanup_ids_and_continues(tmp_path, upload_client):
    client = upload_client
    client.files.create.side_effect = [
        SimpleNamespace(id="instructions"),
        SimpleNamespace(id="ref1"),
        RuntimeError("upload rejected"),
    ]
    client.files.delete.side_effect = [RuntimeError("permission denied"), None]
    result = get_adaptor("openai").upload(upload_package(tmp_path), "sk-test")
    assert not result["success"]
    assert "upload rejected" in result["message"]
    assert "ref1 (permission denied)" in result["message"]
    client.vector_stores.delete.assert_called_once_with("vs_123")
    assert client.files.delete.call_args_list == [call("ref1"), call("instructions")]


def test_invalid_package_creates_no_resources(tmp_path, upload_client):
    package = tmp_path / "invalid.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("vector_store_files/test.md", "# Example")
    result = get_adaptor("openai").upload(package, "sk-test")
    assert not result["success"] and "assistant_instructions.txt" in result["message"]
    upload_client.files.create.assert_not_called()
    upload_client.vector_stores.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
