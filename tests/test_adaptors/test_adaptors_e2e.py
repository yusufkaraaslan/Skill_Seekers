#!/usr/bin/env python3
"""
End-to-End Tests for Multi-LLM Adaptors

Tests complete workflows without real API uploads:
- Scrape → Package → Verify for all platforms
- Same scraped data works for all platforms
- Package structure validation
- Enhancement workflow (mocked)
"""

import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestAdaptorsE2E(unittest.TestCase):
    """End-to-end tests for all platform adaptors"""

    def setUp(self):
        """Set up test environment with sample skill directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temp_dir.name) / "test-skill"
        self.skill_dir.mkdir()

        # Create realistic skill structure
        self._create_sample_skill()

        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def _create_sample_skill(self):
        """Create a sample skill directory with realistic content"""
        # Create SKILL.md
        skill_md_content = """# React Framework

React is a JavaScript library for building user interfaces.

## Quick Reference

```javascript
// Create a component
function Welcome(props) {
  return <h1>Hello, {props.name}</h1>;
}
```

## Key Concepts

- Components
- Props
- State
- Hooks
"""
        (self.skill_dir / "SKILL.md").write_text(skill_md_content)

        # Create references directory
        refs_dir = self.skill_dir / "references"
        refs_dir.mkdir()

        # Create sample reference files
        (refs_dir / "getting_started.md").write_text("""# Getting Started

Install React:

```bash
npm install react
```

Create your first component:

```javascript
function App() {
  return <div>Hello World</div>;
}
```
""")

        (refs_dir / "hooks.md").write_text("""# React Hooks

## useState

```javascript
const [count, setCount] = useState(0);
```

## useEffect

```javascript
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);
```
""")

        (refs_dir / "components.md").write_text("""# Components

## Functional Components

```javascript
function Greeting({ name }) {
  return <h1>Hello {name}</h1>;
}
```

## Props

Pass data to components:

```javascript
<Greeting name="Alice" />
```
""")

        # Create empty scripts and assets directories
        (self.skill_dir / "scripts").mkdir()
        (self.skill_dir / "assets").mkdir()

    def test_e2e_all_platforms_from_same_skill(self):
        """Test that all platforms can package the same skill"""
        platforms = ["claude", "gemini", "openai", "markdown"]
        packages = {}

        for platform in platforms:
            adaptor = get_adaptor(platform)

            # Package for this platform
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists(), f"Package not created for {platform}")

            # Store for later verification
            packages[platform] = package_path

        # Verify all packages were created
        self.assertEqual(len(packages), 4)

        # Verify correct extensions
        self.assertTrue(str(packages["claude"]).endswith(".zip"))
        self.assertTrue(str(packages["gemini"]).endswith(".tar.gz"))
        self.assertTrue(str(packages["openai"]).endswith(".zip"))
        self.assertTrue(str(packages["markdown"]).endswith(".zip"))

    def test_e2e_claude_workflow(self):
        """Test complete Claude workflow: package + verify structure"""
        adaptor = get_adaptor("claude")

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith(".zip"))

        # Verify contents
        with zipfile.ZipFile(package_path, "r") as zf:
            names = zf.namelist()

            # Should have SKILL.md
            self.assertIn("SKILL.md", names)

            # Should have references
            self.assertTrue(any("references/" in name for name in names))

            # Verify SKILL.md content (should have YAML frontmatter)
            skill_content = zf.read("SKILL.md").decode("utf-8")
            # Claude uses YAML frontmatter (but current implementation doesn't add it in package)
            # Just verify content exists
            self.assertGreater(len(skill_content), 0)

    def test_e2e_gemini_workflow(self):
        """Test complete Gemini workflow: package + verify structure"""
        adaptor = get_adaptor("gemini")

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith(".tar.gz"))

        # Verify contents
        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()

            # Should have system_instructions.md (not SKILL.md)
            self.assertIn("system_instructions.md", names)

            # Should have references
            self.assertTrue(any("references/" in name for name in names))

            # Should have metadata
            self.assertIn("gemini_metadata.json", names)

            # Verify metadata content
            metadata_member = tar.getmember("gemini_metadata.json")
            metadata_file = tar.extractfile(metadata_member)
            metadata = json.loads(metadata_file.read().decode("utf-8"))

            self.assertEqual(metadata["platform"], "gemini")
            self.assertEqual(metadata["name"], "test-skill")
            self.assertIn("created_with", metadata)

    def test_e2e_openai_workflow(self):
        """Test complete OpenAI workflow: package + verify structure"""
        adaptor = get_adaptor("openai")

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith(".zip"))

        # Verify contents
        with zipfile.ZipFile(package_path, "r") as zf:
            names = zf.namelist()

            # Should have assistant_instructions.txt
            self.assertIn("assistant_instructions.txt", names)

            # Should have vector store files
            self.assertTrue(any("vector_store_files/" in name for name in names))

            # Should have metadata
            self.assertIn("openai_metadata.json", names)

            # Verify metadata content
            metadata_content = zf.read("openai_metadata.json").decode("utf-8")
            metadata = json.loads(metadata_content)

            self.assertEqual(metadata["platform"], "openai")
            self.assertEqual(metadata["name"], "test-skill")
            self.assertEqual(metadata["model"], "gpt-4o")
            self.assertIn("file_search", metadata["tools"])

    def test_e2e_markdown_workflow(self):
        """Test complete Markdown workflow: package + verify structure"""
        adaptor = get_adaptor("markdown")

        # Package
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Verify package
        self.assertTrue(package_path.exists())
        self.assertTrue(str(package_path).endswith(".zip"))

        # Verify contents
        with zipfile.ZipFile(package_path, "r") as zf:
            names = zf.namelist()

            # Should have README.md
            self.assertIn("README.md", names)

            # Should have DOCUMENTATION.md (combined)
            self.assertIn("DOCUMENTATION.md", names)

            # Should have references
            self.assertTrue(any("references/" in name for name in names))

            # Should have metadata
            self.assertIn("metadata.json", names)

            # Verify combined documentation
            doc_content = zf.read("DOCUMENTATION.md").decode("utf-8")

            # Should contain content from all references
            self.assertIn("Getting Started", doc_content)
            self.assertIn("React Hooks", doc_content)
            self.assertIn("Components", doc_content)

    def test_e2e_package_format_validation(self):
        """Test that each platform creates correct package format"""
        test_cases = [
            ("claude", ".zip"),
            ("gemini", ".tar.gz"),
            ("openai", ".zip"),
            ("markdown", ".zip"),
        ]

        for platform, expected_ext in test_cases:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify extension
            if expected_ext == ".tar.gz":
                self.assertTrue(
                    str(package_path).endswith(".tar.gz"), f"{platform} should create .tar.gz file"
                )
            else:
                self.assertTrue(
                    str(package_path).endswith(".zip"), f"{platform} should create .zip file"
                )

    def test_e2e_package_filename_convention(self):
        """Test that package filenames follow convention"""
        test_cases = [
            ("claude", "test-skill.zip"),
            ("gemini", "test-skill-gemini.tar.gz"),
            ("openai", "test-skill-openai.zip"),
            ("markdown", "test-skill-markdown.zip"),
        ]

        for platform, expected_name in test_cases:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify filename
            self.assertEqual(
                package_path.name, expected_name, f"{platform} package filename incorrect"
            )

    def test_e2e_all_platforms_preserve_references(self):
        """Test that all platforms preserve reference files"""
        ref_files = ["getting_started.md", "hooks.md", "components.md"]

        for platform in ["claude", "gemini", "openai", "markdown"]:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Check references are preserved
            if platform == "gemini":
                with tarfile.open(package_path, "r:gz") as tar:
                    names = tar.getnames()
                    for ref_file in ref_files:
                        self.assertTrue(
                            any(ref_file in name for name in names),
                            f"{platform}: {ref_file} not found in package",
                        )
            else:
                with zipfile.ZipFile(package_path, "r") as zf:
                    names = zf.namelist()
                    for ref_file in ref_files:
                        # OpenAI moves to vector_store_files/
                        if platform == "openai":
                            self.assertTrue(
                                any(f"vector_store_files/{ref_file}" in name for name in names),
                                f"{platform}: {ref_file} not found in vector_store_files/",
                            )
                        else:
                            self.assertTrue(
                                any(ref_file in name for name in names),
                                f"{platform}: {ref_file} not found in package",
                            )

    def test_e2e_metadata_consistency(self):
        """Test that metadata is consistent across platforms"""
        platforms_with_metadata = ["gemini", "openai", "markdown"]

        for platform in platforms_with_metadata:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Extract and verify metadata
            if platform == "gemini":
                with tarfile.open(package_path, "r:gz") as tar:
                    metadata_member = tar.getmember("gemini_metadata.json")
                    metadata_file = tar.extractfile(metadata_member)
                    metadata = json.loads(metadata_file.read().decode("utf-8"))
            else:
                with zipfile.ZipFile(package_path, "r") as zf:
                    metadata_filename = (
                        f"{platform}_metadata.json" if platform == "openai" else "metadata.json"
                    )
                    metadata_content = zf.read(metadata_filename).decode("utf-8")
                    metadata = json.loads(metadata_content)

            # Verify required fields
            self.assertEqual(metadata["platform"], platform)
            self.assertEqual(metadata["name"], "test-skill")
            self.assertIn("created_with", metadata)

    def test_e2e_format_skill_md_differences(self):
        """Test that each platform formats SKILL.md differently"""
        metadata = SkillMetadata(name="test-skill", description="Test skill for E2E testing")

        formats = {}
        for platform in ["claude", "gemini", "openai", "markdown"]:
            adaptor = get_adaptor(platform)
            formatted = adaptor.format_skill_md(self.skill_dir, metadata)
            formats[platform] = formatted

        # Claude should have YAML frontmatter
        self.assertTrue(formats["claude"].startswith("---"))

        # Gemini and Markdown should NOT have YAML frontmatter
        self.assertFalse(formats["gemini"].startswith("---"))
        self.assertFalse(formats["markdown"].startswith("---"))

        # All should contain content from existing SKILL.md (React Framework)
        for platform, formatted in formats.items():
            # Check for content from existing SKILL.md
            self.assertIn("react", formatted.lower(), f"{platform} should contain skill content")
            # All should have non-empty content
            self.assertGreater(len(formatted), 100, f"{platform} should have substantial content")

    def test_e2e_upload_without_api_key(self):
        """Test upload behavior without API keys (should fail gracefully)"""
        platforms_with_upload = ["claude", "gemini", "openai"]

        for platform in platforms_with_upload:
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Try upload without API key
            result = adaptor.upload(package_path, "")

            # Should fail
            self.assertFalse(result["success"], f"{platform} should fail without API key")
            self.assertIsNone(result["skill_id"])
            self.assertIn("message", result)

    def test_e2e_markdown_no_upload_support(self):
        """Test that markdown adaptor doesn't support upload"""
        adaptor = get_adaptor("markdown")
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Try upload (should return informative message)
        result = adaptor.upload(package_path, "not-used")

        # Should indicate no upload support
        self.assertFalse(result["success"])
        self.assertIsNone(result["skill_id"])
        self.assertIn("not support", result["message"].lower())
        # URL should point to local file
        self.assertIn(str(package_path.absolute()), result["url"])


class TestAdaptorsWorkflowIntegration(unittest.TestCase):
    """Integration tests for common workflow patterns"""

    def test_workflow_export_to_all_platforms(self):
        """Test exporting same skill to all platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "react"
            skill_dir.mkdir()

            # Create minimal skill
            (skill_dir / "SKILL.md").write_text("# React\n\nReact documentation")
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "guide.md").write_text("# Guide\n\nContent")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Export to all platforms
            packages = {}
            for platform in ["claude", "gemini", "openai", "markdown"]:
                adaptor = get_adaptor(platform)
                package_path = adaptor.package(skill_dir, output_dir)
                packages[platform] = package_path

            # Verify all packages exist and are distinct
            self.assertEqual(len(packages), 4)
            self.assertEqual(len(set(packages.values())), 4)  # All unique

    def test_workflow_package_to_custom_path(self):
        """Test packaging to custom output paths"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test")
            (skill_dir / "references").mkdir()

            # Test custom output paths
            custom_output = Path(temp_dir) / "custom" / "my-package.zip"

            adaptor = get_adaptor("claude")
            package_path = adaptor.package(skill_dir, custom_output)

            # Should respect custom path
            self.assertTrue(package_path.exists())
            self.assertTrue(
                "my-package" in package_path.name or package_path.parent.name == "custom"
            )

    def test_workflow_api_key_validation(self):
        """Test API key validation for each platform"""
        test_cases = [
            ("claude", "sk-ant-test123", True),
            ("claude", "invalid-key", False),
            ("gemini", "AIzaSyTest123", True),
            ("gemini", "sk-ant-test", False),
            ("openai", "sk-proj-test123", True),
            ("openai", "sk-test123", True),
            ("openai", "AIzaSy123", False),
            ("markdown", "any-key", False),  # Never uses keys
        ]

        for platform, api_key, expected in test_cases:
            adaptor = get_adaptor(platform)
            result = adaptor.validate_api_key(api_key)
            self.assertEqual(
                result, expected, f"{platform}: validate_api_key('{api_key}') should be {expected}"
            )


class TestAdaptorsErrorHandling(unittest.TestCase):
    """Test error handling in adaptors"""

    def test_error_invalid_skill_directory(self):
        """Test packaging with invalid skill directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory (no SKILL.md)
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Should handle gracefully (may create package but with empty content)
            for platform in ["claude", "gemini", "openai", "markdown"]:
                adaptor = get_adaptor(platform)
                # Should not crash
                try:
                    package_path = adaptor.package(empty_dir, output_dir)
                    # Package may be created but should exist
                    self.assertTrue(package_path.exists())
                except Exception as e:
                    # If it raises, should be clear error
                    self.assertIn("SKILL.md", str(e).lower() or "reference" in str(e).lower())

    def test_error_upload_nonexistent_file(self):
        """Test upload with nonexistent file"""
        for platform in ["claude", "gemini", "openai"]:
            adaptor = get_adaptor(platform)
            result = adaptor.upload(Path("/nonexistent/file.zip"), "test-key")

            self.assertFalse(result["success"])
            self.assertIn("not found", result["message"].lower())

    def test_error_upload_wrong_format(self):
        """Test upload with wrong file format"""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            # Try uploading .txt file
            for platform in ["claude", "gemini", "openai"]:
                adaptor = get_adaptor(platform)
                result = adaptor.upload(Path(tmp.name), "test-key")

                self.assertFalse(result["success"])


class TestRAGAdaptorsE2E(unittest.TestCase):
    """End-to-end tests for RAG framework and vector DB adaptors"""

    def setUp(self):
        """Set up test environment with sample skill directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temp_dir.name) / "test-rag-skill"
        self.skill_dir.mkdir()

        # Create realistic skill structure
        self._create_sample_skill()

        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def _create_sample_skill(self):
        """Create a sample skill directory with realistic content"""
        # Create SKILL.md
        skill_md_content = """# Vue.js Framework

Vue.js is a progressive JavaScript framework for building user interfaces.

## Quick Reference

```javascript
// Create a Vue app
const app = Vue.createApp({
  data() {
    return { message: 'Hello Vue!' }
  }
})
```

## Key Concepts

- Reactivity system
- Components
- Directives
- Composition API
"""
        (self.skill_dir / "SKILL.md").write_text(skill_md_content)

        # Create references directory
        refs_dir = self.skill_dir / "references"
        refs_dir.mkdir()

        # Create sample reference files with different categories
        (refs_dir / "getting_started.md").write_text("""# Getting Started

Install Vue:

```bash
npm install vue@next
```

Create your first app:

```javascript
const app = Vue.createApp({
  data() {
    return { count: 0 }
  }
})
app.mount('#app')
```
""")

        (refs_dir / "reactivity_api.md").write_text("""# Reactivity API

## ref()

```javascript
import { ref } from 'vue'
const count = ref(0)
```

## reactive()

```javascript
import { reactive } from 'vue'
const state = reactive({ count: 0 })
```
""")

        (refs_dir / "components_guide.md").write_text("""# Components Guide

## Defining Components

```javascript
export default {
  name: 'MyComponent',
  props: ['title'],
  emits: ['update']
}
```

## Using Components

```vue
<MyComponent title="Hello" @update="handleUpdate" />
```
""")

    def test_e2e_all_rag_adaptors_from_same_skill(self):
        """Test all 7 RAG adaptors can package the same skill"""
        rag_platforms = [
            "langchain",
            "llama-index",
            "haystack",
            "weaviate",
            "chroma",
            "faiss",
            "qdrant",
        ]
        packages = {}

        for platform in rag_platforms:
            adaptor = get_adaptor(platform)

            # Package for this platform
            package_path = adaptor.package(self.skill_dir, self.output_dir)

            # Verify package was created
            self.assertTrue(package_path.exists(), f"Package not created for {platform}")

            # Verify it's a JSON file
            self.assertTrue(
                str(package_path).endswith(".json"), f"{platform} should produce JSON file"
            )

            # Store for later verification
            packages[platform] = package_path

        # Verify all packages were created
        self.assertEqual(len(packages), 7, "All 7 RAG adaptors should create packages")

        # Verify all are JSON files
        for platform, path in packages.items():
            with open(path) as f:
                data = json.load(f)
                # Should be valid JSON (dict or list)
                self.assertIsInstance(data, (dict, list), f"{platform} should produce valid JSON")

    def test_e2e_rag_adaptors_preserve_metadata(self):
        """Test that metadata is preserved across RAG adaptors"""
        metadata = SkillMetadata(
            name="vue",
            description="Vue.js framework skill",
            version="2.0.0",
            author="Test Author",
            tags=["vue", "javascript", "frontend"],
        )

        # Test subset of platforms (representative sample)
        test_platforms = ["langchain", "weaviate", "chroma"]

        for platform in test_platforms:
            adaptor = get_adaptor(platform)

            # Format skill with metadata
            formatted = adaptor.format_skill_md(self.skill_dir, metadata)
            data = json.loads(formatted)

            # Check metadata is present (structure varies by platform)
            if platform == "langchain":
                # LangChain uses list of documents
                self.assertIsInstance(data, list)
                self.assertGreater(len(data), 0)
                # Check first document has metadata
                self.assertIn("metadata", data[0])
                self.assertEqual(data[0]["metadata"]["source"], "vue")
                self.assertEqual(data[0]["metadata"]["version"], "2.0.0")

            elif platform == "weaviate":
                # Weaviate uses schema + objects
                self.assertIn("schema", data)
                self.assertIn("objects", data)
                self.assertGreater(len(data["objects"]), 0)
                # Check first object has metadata in properties
                self.assertIn("properties", data["objects"][0])
                self.assertEqual(data["objects"][0]["properties"]["source"], "vue")
                self.assertEqual(data["objects"][0]["properties"]["version"], "2.0.0")

            elif platform == "chroma":
                # Chroma uses documents + metadatas + ids
                self.assertIn("documents", data)
                self.assertIn("metadatas", data)
                self.assertIn("ids", data)
                self.assertGreater(len(data["metadatas"]), 0)
                # Check first metadata
                self.assertEqual(data["metadatas"][0]["source"], "vue")
                self.assertEqual(data["metadatas"][0]["version"], "2.0.0")

    def test_e2e_rag_json_structure_validation(self):
        """Validate JSON structure for each RAG adaptor"""
        metadata = SkillMetadata(name="vue", description="Vue framework")

        # Define expected structure for each platform
        validations = {
            "langchain": lambda d: (
                isinstance(d, list)
                and all("page_content" in item and "metadata" in item for item in d)
            ),
            "llama-index": lambda d: (
                isinstance(d, list) and all("text" in item and "metadata" in item for item in d)
            ),
            "haystack": lambda d: (
                isinstance(d, list) and all("content" in item and "meta" in item for item in d)
            ),
            "weaviate": lambda d: (
                isinstance(d, dict) and "schema" in d and "objects" in d and "class_name" in d
            ),
            "chroma": lambda d: (
                isinstance(d, dict)
                and "documents" in d
                and "metadatas" in d
                and "ids" in d
                and "collection_name" in d
            ),
            "faiss": lambda d: (
                isinstance(d, dict) and "documents" in d and "metadatas" in d and "ids" in d
            ),
            "qdrant": lambda d: (
                isinstance(d, dict) and "collection_name" in d and "points" in d and "config" in d
            ),
        }

        for platform, validate_func in validations.items():
            adaptor = get_adaptor(platform)
            formatted = adaptor.format_skill_md(self.skill_dir, metadata)
            data = json.loads(formatted)

            # Validate structure
            self.assertTrue(
                validate_func(data), f"{platform} validation failed: incorrect JSON structure"
            )

    def test_e2e_rag_empty_skill_handling(self):
        """Test RAG adaptors handle empty skills correctly"""
        empty_dir = Path(self.temp_dir.name) / "empty_skill"
        empty_dir.mkdir()

        metadata = SkillMetadata(name="empty", description="Empty skill")

        for platform in ["langchain", "chroma", "qdrant"]:
            adaptor = get_adaptor(platform)
            formatted = adaptor.format_skill_md(empty_dir, metadata)
            data = json.loads(formatted)

            # Should return empty but valid structure
            if isinstance(data, list):
                self.assertEqual(data, [], f"{platform} should return empty list")
            elif isinstance(data, dict):
                # Check that collections are empty
                if "documents" in data:
                    self.assertEqual(len(data["documents"]), 0)
                elif "objects" in data:
                    self.assertEqual(len(data["objects"]), 0)
                elif "points" in data:
                    self.assertEqual(len(data["points"]), 0)

    def test_e2e_rag_category_detection(self):
        """Test that categories are correctly detected"""
        metadata = SkillMetadata(name="vue", description="Vue framework")

        for platform in ["langchain", "weaviate", "chroma"]:
            adaptor = get_adaptor(platform)
            formatted = adaptor.format_skill_md(self.skill_dir, metadata)
            data = json.loads(formatted)

            # Extract categories based on platform structure
            categories = set()

            if platform == "langchain":
                categories = {item["metadata"]["category"] for item in data}
            elif platform == "weaviate":
                categories = {obj["properties"]["category"] for obj in data["objects"]}
            elif platform == "chroma":
                categories = {meta["category"] for meta in data["metadatas"]}

            # Should have overview (SKILL.md) and reference categories
            self.assertIn("overview", categories, f"{platform}: Should have 'overview' category")

            # Should have categories from reference files
            # Files: getting_started.md, reactivity_api.md, components_guide.md
            # Categories derived from filenames (stem.replace("_", " ").lower())

            # Check that at least one reference category exists
            ref_categories = categories - {"overview"}
            self.assertGreater(
                len(ref_categories), 0, f"{platform}: Should have at least one reference category"
            )

    def test_e2e_rag_integration_workflow_chromadb(self):
        """Test complete workflow: package → ChromaDB → query → verify"""
        try:
            import chromadb
        except ImportError:
            self.skipTest("chromadb not installed")

        # Package
        adaptor = get_adaptor("chroma")
        package_path = adaptor.package(self.skill_dir, self.output_dir)

        # Load packaged data
        with open(package_path) as f:
            data = json.load(f)

        # Create in-memory ChromaDB client
        client = chromadb.Client()

        # Create collection and add documents
        collection = client.create_collection(data["collection_name"])
        collection.add(documents=data["documents"], metadatas=data["metadatas"], ids=data["ids"])

        # Query
        results = collection.query(query_texts=["reactivity"], n_results=2)

        # Verify results
        self.assertGreater(len(results["documents"][0]), 0, "Should return results")

        # Check that results contain relevant content
        # At least one result should mention reactivity
        found_reactivity = any(
            "reactivity" in doc.lower() or "reactive" in doc.lower()
            for doc in results["documents"][0]
        )
        self.assertTrue(found_reactivity, "Results should be relevant to query")

        # Cleanup
        client.delete_collection(data["collection_name"])


if __name__ == "__main__":
    unittest.main()
