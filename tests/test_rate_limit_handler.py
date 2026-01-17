"""
Tests for Rate Limit Handler

Tests the smart rate limit detection and handling system.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from skill_seekers.cli.config_manager import ConfigManager
from skill_seekers.cli.rate_limit_handler import (
    RateLimitError,
    RateLimitHandler,
    create_github_headers,
)


class TestRateLimitHandler:
    """Test RateLimitHandler functionality."""

    def test_create_headers_no_token(self):
        """Test header creation without token."""
        headers = create_github_headers(None)
        assert headers == {}

    def test_create_headers_with_token(self):
        """Test header creation with token."""
        token = "ghp_test123"
        headers = create_github_headers(token)
        assert headers == {"Authorization": "token ghp_test123"}

    def test_init_without_token(self):
        """Test initialization without token."""
        handler = RateLimitHandler(token=None, interactive=True)
        assert handler.token is None
        assert handler.interactive is True
        assert handler.strategy == "prompt"

    def test_init_with_token(self):
        """Test initialization with token."""
        handler = RateLimitHandler(token="ghp_test", interactive=False)
        assert handler.token == "ghp_test"
        assert handler.interactive is False

    @patch("skill_seekers.cli.rate_limit_handler.get_config_manager")
    def test_init_with_config_strategy(self, mock_get_config):
        """Test initialization pulls strategy from config."""
        mock_config = Mock()
        mock_config.config = {
            "rate_limit": {
                "auto_switch_profiles": True,
                "show_countdown": True,
                "default_timeout_minutes": 30,
            }
        }
        mock_config.get_rate_limit_strategy.return_value = "wait"
        mock_config.get_timeout_minutes.return_value = 45
        mock_get_config.return_value = mock_config

        handler = RateLimitHandler(token="ghp_test", interactive=True)

        assert handler.strategy == "wait"
        assert handler.timeout_minutes == 45

    def test_extract_rate_limit_info(self):
        """Test extracting rate limit info from response headers."""
        handler = RateLimitHandler()

        # Create mock response
        mock_response = Mock()
        reset_time = int((datetime.now() + timedelta(minutes=30)).timestamp())
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Reset": str(reset_time),
        }

        info = handler.extract_rate_limit_info(mock_response)

        assert info["limit"] == 5000
        assert info["remaining"] == 100
        assert info["reset_timestamp"] == reset_time
        assert isinstance(info["reset_time"], datetime)

    @patch("builtins.input", return_value="n")
    def test_check_upfront_no_token_declined(self, mock_input):
        """Test upfront check with no token, user declines."""
        handler = RateLimitHandler(token=None, interactive=True)

        result = handler.check_upfront()

        assert result is False
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="y")
    def test_check_upfront_no_token_accepted(self, mock_input):
        """Test upfront check with no token, user accepts."""
        handler = RateLimitHandler(token=None, interactive=True)

        result = handler.check_upfront()

        assert result is True
        mock_input.assert_called_once()

    def test_check_upfront_no_token_non_interactive(self):
        """Test upfront check with no token in non-interactive mode."""
        handler = RateLimitHandler(token=None, interactive=False)

        result = handler.check_upfront()

        # Should proceed without prompting
        assert result is True

    @patch("requests.get")
    @patch("skill_seekers.cli.rate_limit_handler.get_config_manager")
    def test_check_upfront_with_token_good_status(self, mock_get_config, mock_get):
        """Test upfront check with token and good rate limit status."""
        # Mock config
        mock_config = Mock()
        mock_config.config = {
            "rate_limit": {
                "auto_switch_profiles": False,
                "show_countdown": True,
                "default_timeout_minutes": 30,
            }
        }
        mock_config.get_rate_limit_strategy.return_value = "prompt"
        mock_config.get_timeout_minutes.return_value = 30
        mock_get_config.return_value = mock_config

        # Mock rate limit check
        reset_time = int((datetime.now() + timedelta(minutes=60)).timestamp())
        mock_response = Mock()
        mock_response.json.return_value = {
            "rate": {"limit": 5000, "remaining": 4500, "reset": reset_time}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        handler = RateLimitHandler(token="ghp_test", interactive=True)
        result = handler.check_upfront()

        assert result is True

    def test_check_response_not_rate_limited(self):
        """Test check_response with normal 200 response."""
        handler = RateLimitHandler(interactive=True)

        mock_response = Mock()
        mock_response.status_code = 200

        result = handler.check_response(mock_response)

        assert result is True

    def test_check_response_other_403(self):
        """Test check_response with 403 but not rate limit."""
        handler = RateLimitHandler(interactive=True)

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"message": "Forbidden - not rate limit"}

        result = handler.check_response(mock_response)

        assert result is True

    @patch("skill_seekers.cli.rate_limit_handler.get_config_manager")
    def test_non_interactive_fail_strategy(self, mock_get_config):
        """Test non-interactive mode with fail strategy raises error."""
        mock_config = Mock()
        mock_config.config = {
            "rate_limit": {
                "auto_switch_profiles": False,
                "show_countdown": True,
                "default_timeout_minutes": 30,
            }
        }
        mock_config.get_rate_limit_strategy.return_value = "fail"
        mock_config.get_timeout_minutes.return_value = 30
        mock_get_config.return_value = mock_config

        handler = RateLimitHandler(token="ghp_test", interactive=False)

        reset_time = datetime.now() + timedelta(minutes=30)
        rate_info = {"limit": 5000, "remaining": 0, "reset_time": reset_time}

        with pytest.raises(RateLimitError):
            handler.handle_rate_limit(rate_info)


class TestConfigManagerIntegration:
    """Test ConfigManager integration with rate limit handler."""

    def test_config_manager_creates_default_config(self, tmp_path, monkeypatch):
        """Test that ConfigManager creates default config structure."""
        # Override config paths for testing
        config_dir = tmp_path / ".config" / "skill-seekers"
        progress_dir = tmp_path / ".local" / "share" / "skill-seekers" / "progress"

        # Monkey patch the class variables
        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_dir / "config.json")
        monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", progress_dir)

        config = ConfigManager()

        # Check directories created
        assert config.config_dir.exists()
        assert config.progress_dir.exists()

        # Check default config structure
        assert "github" in config.config
        assert "rate_limit" in config.config
        assert "resume" in config.config
        assert "api_keys" in config.config

        # Check rate limit defaults
        assert config.config["rate_limit"]["default_timeout_minutes"] == 30
        assert config.config["rate_limit"]["auto_switch_profiles"] is True

    def test_add_and_retrieve_github_profile(self, tmp_path, monkeypatch):
        """Test adding and retrieving GitHub profiles."""
        config_dir = tmp_path / ".config" / "skill-seekers"
        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_dir / "config.json")
        monkeypatch.setattr(
            ConfigManager,
            "PROGRESS_DIR",
            tmp_path / ".local" / "share" / "skill-seekers" / "progress",
        )

        config = ConfigManager()

        # Add a profile
        config.add_github_profile(
            name="test-profile",
            token="ghp_test123",
            description="Test profile",
            rate_limit_strategy="wait",
            timeout_minutes=45,
            set_as_default=True,
        )

        # Retrieve token
        token = config.get_github_token(profile_name="test-profile")
        assert token == "ghp_test123"

        # Check it's default
        profiles = config.list_github_profiles()
        assert len(profiles) == 1
        assert profiles[0]["is_default"] is True
        assert profiles[0]["name"] == "test-profile"

    def test_get_next_profile(self, tmp_path, monkeypatch):
        """Test profile switching."""
        # Use separate tmp directory for this test
        test_dir = tmp_path / "test_switching"
        config_dir = test_dir / ".config" / "skill-seekers"
        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_dir / "config.json")
        monkeypatch.setattr(
            ConfigManager,
            "PROGRESS_DIR",
            test_dir / ".local" / "share" / "skill-seekers" / "progress",
        )
        monkeypatch.setattr(ConfigManager, "WELCOME_FLAG", config_dir / ".welcomed")

        config = ConfigManager()

        # Ensure clean state
        config.config["github"]["profiles"] = {}

        # Add two profiles
        config.add_github_profile("profile1", "ghp_token1", set_as_default=True)
        config.add_github_profile("profile2", "ghp_token2", set_as_default=False)

        # Verify we have exactly 2 profiles
        profiles = config.list_github_profiles()
        assert len(profiles) == 2

        # Get next profile after profile1
        next_data = config.get_next_profile("ghp_token1")
        assert next_data is not None
        name, token = next_data
        assert name == "profile2"
        assert token == "ghp_token2"

        # Get next profile after profile2 (should wrap to profile1)
        next_data = config.get_next_profile("ghp_token2")
        assert next_data is not None
        name, token = next_data
        assert name == "profile1"
        assert token == "ghp_token1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
