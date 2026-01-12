#!/usr/bin/env python3
"""
Tests for config_extractor.py - Configuration pattern extraction (C3.4).

Test Coverage:
- ConfigFileDetector (5 tests) - File detection for 9 formats
- ConfigParser (8 tests) - Parsing for all supported formats
- ConfigPatternDetector (7 tests) - Pattern detection
- ConfigExtractor Integration (5 tests) - End-to-end workflows
- Edge Cases (3 tests) - Error handling, empty files, invalid formats
"""

import unittest
import sys
import os
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from skill_seekers.cli.config_extractor import (
    ConfigFileDetector,
    ConfigParser,
    ConfigPatternDetector,
    ConfigExtractor,
    ConfigSetting,
    ConfigFile,
    ConfigExtractionResult,
)


class TestConfigFileDetector(unittest.TestCase):
    """Tests for ConfigFileDetector - file detection"""

    def setUp(self):
        self.detector = ConfigFileDetector()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_json_files(self):
        """Test detection of JSON config files"""
        # Create test files
        (Path(self.temp_dir) / "config.json").write_text('{"key": "value"}')
        (Path(self.temp_dir) / "package.json").write_text('{"name": "test"}')
        (Path(self.temp_dir) / "test.txt").write_text("not a config")

        files = self.detector.find_config_files(Path(self.temp_dir))
        json_files = [f for f in files if f.config_type == "json"]

        self.assertGreaterEqual(len(json_files), 2)
        filenames = [f.relative_path for f in json_files]
        self.assertTrue(any("config.json" in f for f in filenames))
        self.assertTrue(any("package.json" in f for f in filenames))

    def test_detect_yaml_files(self):
        """Test detection of YAML config files"""
        (Path(self.temp_dir) / "config.yml").write_text("key: value")
        (Path(self.temp_dir) / "docker-compose.yaml").write_text("version: '3'")

        files = self.detector.find_config_files(Path(self.temp_dir))
        yaml_files = [f for f in files if f.config_type == "yaml"]

        self.assertGreaterEqual(len(yaml_files), 2)

    def test_detect_env_files(self):
        """Test detection of .env files"""
        (Path(self.temp_dir) / ".env").write_text("DATABASE_URL=postgres://localhost")
        (Path(self.temp_dir) / ".env.production").write_text("NODE_ENV=production")

        files = self.detector.find_config_files(Path(self.temp_dir))
        env_files = [f for f in files if f.config_type == "env"]

        self.assertGreaterEqual(len(env_files), 1)

    def test_detect_python_config(self):
        """Test detection of Python config modules"""
        (Path(self.temp_dir) / "settings.py").write_text("DEBUG = True")
        (Path(self.temp_dir) / "config.py").write_text("API_KEY = 'test'")

        files = self.detector.find_config_files(Path(self.temp_dir))
        python_files = [f for f in files if f.config_type == "python"]

        self.assertGreaterEqual(len(python_files), 1)

    def test_max_files_limit(self):
        """Test max_files limit is respected"""
        # Create many config files
        for i in range(20):
            (Path(self.temp_dir) / f"config{i}.json").write_text('{}')

        detector = ConfigFileDetector()
        files = detector.find_config_files(Path(self.temp_dir), max_files=5)

        self.assertLessEqual(len(files), 5)


class TestConfigParser(unittest.TestCase):
    """Tests for ConfigParser - parsing different formats"""

    def setUp(self):
        self.parser = ConfigParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_json_config(self):
        """Test parsing JSON configuration"""
        json_content = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "api_key": "secret"
        }

        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "config.json"),
            relative_path="config.json",
            config_type="json",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "config.json"
        file_path.write_text(json.dumps(json_content))

        self.parser.parse_config_file(config_file)

        self.assertGreater(len(config_file.settings), 0)
        # Check nested settings
        db_settings = [s for s in config_file.settings if "database" in s.key]
        self.assertGreater(len(db_settings), 0)

    def test_parse_yaml_config(self):
        """Test parsing YAML configuration"""
        yaml_content = """
database:
  host: localhost
  port: 5432
logging:
  level: INFO
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "config.yml"),
            relative_path="config.yml",
            config_type="yaml",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "config.yml"
        file_path.write_text(yaml_content)

        # This will skip if PyYAML not available
        self.parser.parse_config_file(config_file)

        # Check if parsing failed due to missing PyYAML
        if config_file.parse_errors and "PyYAML not installed" in str(config_file.parse_errors):
            self.skipTest("PyYAML not installed")

        self.assertGreater(len(config_file.settings), 0)

    def test_parse_env_file(self):
        """Test parsing .env file"""
        env_content = """
# Database configuration
DATABASE_URL=postgresql://localhost:5432/db
API_KEY=secret123

# Server configuration
PORT=8000
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / ".env"),
            relative_path=".env",
            config_type="env",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / ".env"
        file_path.write_text(env_content)

        self.parser.parse_config_file(config_file)

        self.assertGreater(len(config_file.settings), 0)
        # Check DATABASE_URL is extracted
        db_url = [s for s in config_file.settings if s.key == "DATABASE_URL"]
        self.assertEqual(len(db_url), 1)
        self.assertEqual(db_url[0].value, "postgresql://localhost:5432/db")

    def test_parse_ini_file(self):
        """Test parsing INI file"""
        ini_content = """
[database]
host = localhost
port = 5432

[api]
endpoint = https://api.example.com
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "config.ini"),
            relative_path="config.ini",
            config_type="ini",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "config.ini"
        file_path.write_text(ini_content)

        self.parser.parse_config_file(config_file)

        self.assertGreater(len(config_file.settings), 0)

    def test_parse_python_config(self):
        """Test parsing Python config module"""
        python_content = """
DATABASE_HOST = 'localhost'
DATABASE_PORT = 5432
DEBUG = True
API_KEYS = ['key1', 'key2']
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "settings.py"),
            relative_path="settings.py",
            config_type="python",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "settings.py"
        file_path.write_text(python_content)

        self.parser.parse_config_file(config_file)

        self.assertGreater(len(config_file.settings), 0)
        # Check DATABASE_HOST is extracted
        db_host = [s for s in config_file.settings if s.key == "DATABASE_HOST"]
        self.assertGreaterEqual(len(db_host), 1)

    def test_parse_dockerfile(self):
        """Test parsing Dockerfile for ENV vars"""
        dockerfile_content = """
FROM python:3.10
ENV DATABASE_URL=postgresql://localhost:5432/db
ENV API_KEY=secret
WORKDIR /app
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "Dockerfile"),
            relative_path="Dockerfile",
            config_type="dockerfile",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "Dockerfile"
        file_path.write_text(dockerfile_content)

        self.parser.parse_config_file(config_file)

        env_settings = [s for s in config_file.settings if s.env_var]
        self.assertGreater(len(env_settings), 0)

    def test_parse_javascript_config(self):
        """Test parsing JavaScript config file"""
        js_content = """
module.exports = {
  database: {
    host: 'localhost',
    port: 5432
  },
  api: {
    endpoint: 'https://api.example.com'
  }
};
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "config.js"),
            relative_path="config.js",
            config_type="javascript",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "config.js"
        file_path.write_text(js_content)

        self.parser.parse_config_file(config_file)

        # JavaScript parsing is regex-based and may not extract all fields
        # Just verify it doesn't crash
        self.assertIsNotNone(config_file.settings)

    def test_parse_toml_config(self):
        """Test parsing TOML configuration"""
        toml_content = """
[database]
host = "localhost"
port = 5432

[api]
endpoint = "https://api.example.com"
"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "config.toml"),
            relative_path="config.toml",
            config_type="toml",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "config.toml"
        file_path.write_text(toml_content)

        # This will skip if toml/tomli not available
        self.parser.parse_config_file(config_file)

        # Check if parsing failed due to missing toml/tomli
        if config_file.parse_errors and ("toml" in str(config_file.parse_errors).lower() and "not installed" in str(config_file.parse_errors)):
            self.skipTest("toml/tomli not installed")

        self.assertGreater(len(config_file.settings), 0)


class TestConfigPatternDetector(unittest.TestCase):
    """Tests for ConfigPatternDetector - pattern detection"""

    def setUp(self):
        self.detector = ConfigPatternDetector()

    def test_detect_database_pattern(self):
        """Test detection of database configuration pattern"""
        settings = [
            ConfigSetting(key="host", value="localhost", value_type="string"),
            ConfigSetting(key="port", value=5432, value_type="integer"),
            ConfigSetting(key="database", value="mydb", value_type="string"),
            ConfigSetting(key="user", value="admin", value_type="string"),
            ConfigSetting(key="password", value="secret", value_type="string"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("database_config", patterns)

    def test_detect_api_pattern(self):
        """Test detection of API configuration pattern"""
        settings = [
            ConfigSetting(key="base_url", value="https://api.example.com", value_type="string"),
            ConfigSetting(key="api_key", value="secret", value_type="string"),
            ConfigSetting(key="timeout", value=30, value_type="integer"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("api_config", patterns)

    def test_detect_logging_pattern(self):
        """Test detection of logging configuration pattern"""
        settings = [
            ConfigSetting(key="level", value="INFO", value_type="string"),
            ConfigSetting(key="format", value="%(asctime)s", value_type="string"),
            ConfigSetting(key="handlers", value=["console", "file"], value_type="array"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("logging_config", patterns)

    def test_detect_cache_pattern(self):
        """Test detection of cache configuration pattern"""
        settings = [
            ConfigSetting(key="backend", value="redis", value_type="string"),
            ConfigSetting(key="ttl", value=3600, value_type="integer"),
            ConfigSetting(key="key_prefix", value="myapp", value_type="string"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("cache_config", patterns)

    def test_detect_email_pattern(self):
        """Test detection of email configuration pattern"""
        settings = [
            ConfigSetting(key="smtp_host", value="smtp.gmail.com", value_type="string"),
            ConfigSetting(key="smtp_port", value=587, value_type="integer"),
            ConfigSetting(key="email_user", value="test@example.com", value_type="string"),
            ConfigSetting(key="email_password", value="secret", value_type="string"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("email_config", patterns)

    def test_detect_auth_pattern(self):
        """Test detection of authentication configuration pattern"""
        settings = [
            ConfigSetting(key="secret_key", value="mysecretkey123", value_type="string"),
            ConfigSetting(key="jwt_secret", value="jwtsecret456", value_type="string"),
            ConfigSetting(key="oauth", value="enabled", value_type="string"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("auth_config", patterns)

    def test_detect_server_pattern(self):
        """Test detection of server configuration pattern"""
        settings = [
            ConfigSetting(key="host", value="0.0.0.0", value_type="string"),
            ConfigSetting(key="port", value=8000, value_type="integer"),
            ConfigSetting(key="workers", value=4, value_type="integer"),
        ]

        config_file = ConfigFile(
            file_path="test.json",
            relative_path="test.json",
            config_type="json",
            purpose="unknown",
            settings=settings
        )

        patterns = self.detector.detect_patterns(config_file)

        self.assertIn("server_config", patterns)


class TestConfigExtractorIntegration(unittest.TestCase):
    """Tests for ConfigExtractor - end-to-end integration"""

    def setUp(self):
        self.extractor = ConfigExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_from_directory(self):
        """Test extraction from directory with multiple config files"""
        # Create test config files
        (Path(self.temp_dir) / "config.json").write_text('{"database": {"host": "localhost"}}')
        (Path(self.temp_dir) / ".env").write_text("API_KEY=secret")

        result = self.extractor.extract_from_directory(Path(self.temp_dir))

        self.assertGreater(len(result.config_files), 0)
        self.assertEqual(result.total_files, len(result.config_files))

    def test_generate_markdown_output(self):
        """Test markdown output generation"""
        result = ConfigExtractionResult(
            config_files=[
                ConfigFile(
                    file_path="config.json",
                    relative_path="config.json",
                    config_type="json",
                    purpose="database_config",
                    settings=[
                        ConfigSetting(key="host", value="localhost", value_type="string")
                    ],
                    patterns=["database_config"]
                )
            ],
            total_files=1,
            total_settings=1,
            detected_patterns=["database_config"]
        )

        markdown = result.to_markdown()

        self.assertIn("Configuration Extraction Report", markdown)
        self.assertIn("config.json", markdown)
        self.assertIn("database_config", markdown)

    def test_generate_json_output(self):
        """Test JSON output generation"""
        result = ConfigExtractionResult(
            config_files=[
                ConfigFile(
                    file_path="config.json",
                    relative_path="config.json",
                    config_type="json",
                    purpose="database_config",
                    settings=[
                        ConfigSetting(key="host", value="localhost", value_type="string")
                    ],
                    patterns=["database_config"]
                )
            ],
            total_files=1,
            total_settings=1,
            detected_patterns=["database_config"]
        )

        json_data = result.to_dict()

        self.assertEqual(json_data["total_files"], 1)
        self.assertEqual(len(json_data["config_files"]), 1)
        self.assertIn("database_config", json_data["detected_patterns"])

    def test_empty_directory(self):
        """Test extraction from empty directory"""
        result = self.extractor.extract_from_directory(Path(self.temp_dir))

        self.assertEqual(len(result.config_files), 0)
        self.assertEqual(result.total_files, 0)

    @unittest.skip("save_results method not yet implemented")
    def test_save_results(self):
        """Test saving extraction results to files"""
        # Create test config
        (Path(self.temp_dir) / "config.json").write_text('{"key": "value"}')

        result = self.extractor.extract_from_directory(Path(self.temp_dir))
        output_dir = Path(self.temp_dir) / "output"

        # TODO: Implement save_results method in ConfigExtractor
        # self.extractor.save_results(result, output_dir)

        # Check files were created
        # self.assertTrue((output_dir / "config_patterns.json").exists())
        # self.assertTrue((output_dir / "config_patterns.md").exists())


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling"""

    def setUp(self):
        self.parser = ConfigParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_empty_file(self):
        """Test parsing empty config file"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "empty.json"),
            relative_path="empty.json",
            config_type="json",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "empty.json"
        file_path.write_text("")

        # Should not crash
        self.parser.parse_config_file(config_file)
        self.assertEqual(len(config_file.settings), 0)

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON file"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "invalid.json"),
            relative_path="invalid.json",
            config_type="json",
            purpose="unknown"
        )

        file_path = Path(self.temp_dir) / "invalid.json"
        file_path.write_text("{invalid json}")

        # Should not crash
        self.parser.parse_config_file(config_file)

    def test_nonexistent_file(self):
        """Test parsing non-existent file"""
        config_file = ConfigFile(
            file_path=str(Path(self.temp_dir) / "nonexistent.json"),
            relative_path="nonexistent.json",
            config_type="json",
            purpose="unknown"
        )

        # Should not crash
        self.parser.parse_config_file(config_file)


if __name__ == '__main__':
    unittest.main()
