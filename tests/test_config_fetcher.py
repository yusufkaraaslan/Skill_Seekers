"""Tests for config_fetcher module - automatic API config downloading."""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from skill_seekers.cli.config_fetcher import (
    fetch_config_from_api,
    list_available_configs,
    resolve_config_path,
)


class TestFetchConfigFromApi:
    """Tests for fetch_config_from_api function."""

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_successful_fetch(self, mock_client_class, tmp_path):
        """Test successful config download from API."""
        # Mock API responses
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock detail response
        detail_response = Mock()
        detail_response.status_code = 200
        detail_response.json.return_value = {
            "name": "react",
            "download_url": "https://api.skillseekersweb.com/api/configs/react/download",
            "category": "web-frameworks",
            "type": "unified",
        }
        detail_response.raise_for_status = Mock()

        # Mock download response
        download_response = Mock()
        download_response.json.return_value = {
            "name": "react",
            "description": "React documentation skill",
            "base_url": "https://react.dev/",
        }
        download_response.raise_for_status = Mock()

        # Setup mock to return different responses for different URLs
        def get_side_effect(url, *_args, **_kwargs):
            if "download" in url:
                return download_response
            return detail_response

        mock_client.get.side_effect = get_side_effect

        # Test fetch
        destination = str(tmp_path)
        result = fetch_config_from_api("react", destination=destination)

        # Verify
        assert result is not None
        assert result.exists()
        assert result.name == "react.json"

        # Verify file contents
        with open(result) as f:
            config = json.load(f)
        assert config["name"] == "react"
        assert "description" in config

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_config_not_found(self, mock_client_class):
        """Test handling of 404 response."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock 404 response
        detail_response = Mock()
        detail_response.status_code = 404
        mock_client.get.return_value = detail_response

        result = fetch_config_from_api("nonexistent")
        assert result is None

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_no_download_url(self, mock_client_class):
        """Test handling of missing download_url."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock response without download_url
        detail_response = Mock()
        detail_response.status_code = 200
        detail_response.json.return_value = {"name": "test"}
        detail_response.raise_for_status = Mock()
        mock_client.get.return_value = detail_response

        result = fetch_config_from_api("test")
        assert result is None

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_http_error(self, mock_client_class):
        """Test handling of HTTP errors."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock HTTP error
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")

        result = fetch_config_from_api("react")
        assert result is None

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_json_decode_error(self, mock_client_class):
        """Test handling of invalid JSON response."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock response with invalid JSON
        detail_response = Mock()
        detail_response.status_code = 200
        detail_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        detail_response.raise_for_status = Mock()
        mock_client.get.return_value = detail_response

        result = fetch_config_from_api("react")
        assert result is None

    def test_normalize_config_name(self, tmp_path):
        """Test config name normalization (remove .json, remove configs/ prefix)."""
        with patch("skill_seekers.cli.config_fetcher.httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client

            detail_response = Mock()
            detail_response.status_code = 200
            detail_response.json.return_value = {"download_url": "https://api.example.com/download"}
            detail_response.raise_for_status = Mock()

            download_response = Mock()
            download_response.json.return_value = {"name": "test"}
            download_response.raise_for_status = Mock()

            def get_side_effect(url, *_args, **_kwargs):
                if "download" in url:
                    return download_response
                return detail_response

            mock_client.get.side_effect = get_side_effect

            destination = str(tmp_path)

            # Test with .json extension
            result1 = fetch_config_from_api("test.json", destination=destination)
            assert result1 is not None
            assert result1.name == "test.json"

            # Test with configs/ prefix
            result2 = fetch_config_from_api("configs/test", destination=destination)
            assert result2 is not None


class TestListAvailableConfigs:
    """Tests for list_available_configs function."""

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_successful_list(self, mock_client_class):
        """Test successful config listing."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock API response
        response = Mock()
        response.json.return_value = {
            "configs": [
                {"name": "react"},
                {"name": "vue"},
                {"name": "godot"},
            ],
            "total": 3,
        }
        response.raise_for_status = Mock()
        mock_client.get.return_value = response

        result = list_available_configs()
        assert len(result) == 3
        assert "react" in result
        assert "vue" in result
        assert "godot" in result

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_category_filter(self, mock_client_class):
        """Test listing with category filter."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        response = Mock()
        response.json.return_value = {
            "configs": [{"name": "react"}, {"name": "vue"}],
            "total": 2,
        }
        response.raise_for_status = Mock()
        mock_client.get.return_value = response

        result = list_available_configs(category="web-frameworks")
        assert len(result) == 2

        # Verify category parameter was passed
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "params" in call_args.kwargs
        assert call_args.kwargs["params"]["category"] == "web-frameworks"

    @patch("skill_seekers.cli.config_fetcher.httpx.Client")
    def test_api_error(self, mock_client_class):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock error
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")

        result = list_available_configs()
        assert result == []


class TestResolveConfigPath:
    """Tests for resolve_config_path function."""

    def test_exact_path_exists(self, tmp_path):
        """Test resolution when exact path exists."""
        # Create test config file
        config_file = tmp_path / "test.json"
        config_file.write_text('{"name": "test"}')

        result = resolve_config_path(str(config_file), auto_fetch=False)
        assert result is not None
        assert result.exists()
        assert result.name == "test.json"

    def test_with_configs_prefix(self, tmp_path):
        """Test resolution with configs/ prefix."""
        # Create configs directory and file
        configs_dir = tmp_path / "configs"
        configs_dir.mkdir()
        config_file = configs_dir / "test.json"
        config_file.write_text('{"name": "test"}')

        # Change to tmp_path for relative path testing
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = resolve_config_path("test.json", auto_fetch=False)
            assert result is not None
            assert result.exists()
            assert result.name == "test.json"
        finally:
            os.chdir(original_cwd)

    def test_auto_fetch_disabled(self):
        """Test that auto-fetch doesn't run when disabled."""
        result = resolve_config_path("nonexistent.json", auto_fetch=False)
        assert result is None

    @patch("skill_seekers.cli.config_fetcher.fetch_config_from_api")
    def test_auto_fetch_enabled(self, mock_fetch, tmp_path):
        """Test that auto-fetch runs when enabled."""
        # Mock fetch to return a path
        mock_config = tmp_path / "configs" / "react.json"
        mock_config.parent.mkdir(exist_ok=True)
        mock_config.write_text('{"name": "react"}')
        mock_fetch.return_value = mock_config

        result = resolve_config_path("react.json", auto_fetch=True)

        # Verify fetch was called
        mock_fetch.assert_called_once_with("react", destination="configs")
        assert result is not None
        assert result.exists()

    @patch("skill_seekers.cli.config_fetcher.fetch_config_from_api")
    def test_auto_fetch_failed(self, mock_fetch):
        """Test handling when auto-fetch fails."""
        # Mock fetch to return None (failed)
        mock_fetch.return_value = None

        result = resolve_config_path("nonexistent.json", auto_fetch=True)
        assert result is None

    def test_config_name_normalization(self, tmp_path):
        """Test various config name formats."""
        configs_dir = tmp_path / "configs"
        configs_dir.mkdir()
        config_file = configs_dir / "react.json"
        config_file.write_text('{"name": "react"}')

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # All of these should resolve to the same file
            test_cases = ["react.json", "configs/react.json"]

            for config_name in test_cases:
                result = resolve_config_path(config_name, auto_fetch=False)
                assert result is not None, f"Failed for {config_name}"
                assert result.exists()
                assert result.name == "react.json"
        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
class TestConfigFetcherIntegration:
    """Integration tests that hit real API (marked as integration)."""

    def test_fetch_real_config(self, tmp_path):
        """Test fetching a real config from API."""
        destination = str(tmp_path)
        result = fetch_config_from_api("godot", destination=destination, timeout=10.0)

        if result:  # Only assert if fetch succeeded (API might be down)
            assert result.exists()
            assert result.name == "godot.json"

            with open(result) as f:
                config = json.load(f)
            assert config["name"] == "godot"
            assert "description" in config

    def test_list_real_configs(self):
        """Test listing real configs from API."""
        result = list_available_configs(timeout=10.0)

        if result:  # Only assert if API is available
            assert len(result) > 0
            assert isinstance(result, list)
            assert all(isinstance(cfg, str) for cfg in result)
