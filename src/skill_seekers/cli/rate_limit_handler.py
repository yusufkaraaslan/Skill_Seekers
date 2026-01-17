"""
Rate Limit Handler for GitHub API

Handles GitHub API rate limits with smart strategies:
- Upfront warnings about token status
- Real-time countdown timers
- Profile switching for multi-token setups
- Progress auto-save on interruption
- Non-interactive mode for CI/CD
"""

import sys
import time
from datetime import datetime
from typing import Any

import requests

from .config_manager import get_config_manager


class RateLimitError(Exception):
    """Raised when rate limit is exceeded and cannot be handled."""

    pass


class RateLimitHandler:
    """
    Handles GitHub API rate limits with multiple strategies.

    Usage:
        handler = RateLimitHandler(
            token=github_token,
            interactive=True,
            profile_name="personal"
        )

        # Before starting
        handler.check_upfront()

        # Around requests
        response = requests.get(url, headers=headers)
        handler.check_response(response)
    """

    def __init__(
        self,
        token: str | None = None,
        interactive: bool = True,
        profile_name: str | None = None,
        auto_switch: bool = True,
    ):
        """
        Initialize rate limit handler.

        Args:
            token: GitHub token (or None for unauthenticated)
            interactive: Whether to show prompts (False for CI/CD)
            profile_name: Name of the profile being used
            auto_switch: Whether to auto-switch profiles when rate limited
        """
        self.token = token
        self.interactive = interactive
        self.profile_name = profile_name
        self.config = get_config_manager()

        # Get settings from config
        self.auto_switch = auto_switch and self.config.config["rate_limit"]["auto_switch_profiles"]
        self.show_countdown = self.config.config["rate_limit"]["show_countdown"]
        self.default_timeout = self.config.config["rate_limit"]["default_timeout_minutes"]

        # Get profile-specific settings if available
        if token:
            self.strategy = self.config.get_rate_limit_strategy(token)
            self.timeout_minutes = self.config.get_timeout_minutes(token)
        else:
            self.strategy = "prompt"
            self.timeout_minutes = self.default_timeout

    def check_upfront(self) -> bool:
        """
        Check rate limit status before starting.
        Shows non-intrusive warning if no token configured.

        Returns:
            True if check passed, False if should abort
        """
        if not self.token:
            print("\n💡 Tip: GitHub API limit is 60 requests/hour without a token.")
            print("   Set up a GitHub token for 5000 requests/hour:")
            print("   $ skill-seekers config --github")
            print()

            if self.interactive:
                response = input("Continue without token? [Y/n]: ").strip().lower()
                if response in ["n", "no"]:
                    print("\n✅ Run 'skill-seekers config --github' to set up a token.\n")
                    return False

            return True

        # Check current rate limit status
        try:
            rate_info = self.get_rate_limit_info()
            remaining = rate_info.get("remaining", 0)
            limit = rate_info.get("limit", 5000)

            if remaining == 0:
                print(f"\n⚠️  Warning: GitHub rate limit already exhausted (0/{limit})")
                reset_time = rate_info.get("reset_time")
                if reset_time:
                    wait_minutes = (reset_time - datetime.now()).total_seconds() / 60
                    print(f"   Resets in {int(wait_minutes)} minutes")

                if self.interactive:
                    return self.handle_rate_limit(rate_info)
                else:
                    print("\n❌ Cannot proceed: Rate limit exhausted (non-interactive mode)\n")
                    return False

            # Show friendly status
            if remaining < 100:
                print(f"⚠️  GitHub API: {remaining}/{limit} requests remaining")
            else:
                print(f"✅ GitHub API: {remaining}/{limit} requests available")

            return True

        except Exception as e:
            print(f"⚠️  Could not check rate limit status: {e}")
            print("   Proceeding anyway...")
            return True

    def check_response(self, response: requests.Response) -> bool:
        """
        Check if response indicates rate limit and handle it.

        Args:
            response: requests.Response object

        Returns:
            True if handled successfully, False if should abort

        Raises:
            RateLimitError: If rate limit cannot be handled
        """
        # Check for rate limit (403 with specific message)
        if response.status_code == 403:
            try:
                error_data = response.json()
                message = error_data.get("message", "")

                if "rate limit" in message.lower() or "api rate limit exceeded" in message.lower():
                    # Extract rate limit info from headers
                    rate_info = self.extract_rate_limit_info(response)
                    return self.handle_rate_limit(rate_info)

            except Exception:
                pass  # Not a rate limit error

        return True

    def extract_rate_limit_info(self, response: requests.Response) -> dict[str, Any]:
        """
        Extract rate limit information from response headers.

        Args:
            response: requests.Response with rate limit headers

        Returns:
            Dict with rate limit info
        """
        headers = response.headers

        limit = int(headers.get("X-RateLimit-Limit", 0))
        remaining = int(headers.get("X-RateLimit-Remaining", 0))
        reset_timestamp = int(headers.get("X-RateLimit-Reset", 0))

        reset_time = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else None

        return {
            "limit": limit,
            "remaining": remaining,
            "reset_timestamp": reset_timestamp,
            "reset_time": reset_time,
        }

    def get_rate_limit_info(self) -> dict[str, Any]:
        """
        Get current rate limit status from GitHub API.

        Returns:
            Dict with rate limit info
        """
        url = "https://api.github.com/rate_limit"
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()
        core = data.get("rate", {})

        reset_timestamp = core.get("reset", 0)
        reset_time = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else None

        return {
            "limit": core.get("limit", 0),
            "remaining": core.get("remaining", 0),
            "reset_timestamp": reset_timestamp,
            "reset_time": reset_time,
        }

    def handle_rate_limit(self, rate_info: dict[str, Any]) -> bool:
        """
        Handle rate limit based on strategy.

        Args:
            rate_info: Dict with rate limit information

        Returns:
            True if handled (can continue), False if should abort

        Raises:
            RateLimitError: If cannot handle in non-interactive mode
        """
        reset_time = rate_info.get("reset_time")
        remaining = rate_info.get("remaining", 0)
        limit = rate_info.get("limit", 0)

        print("\n⚠️  GitHub Rate Limit Reached")
        print(f"   Profile: {self.profile_name or 'default'}")
        print(f"   Limit: {remaining}/{limit} requests")

        if reset_time:
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            wait_minutes = int(wait_seconds / 60)
            print(f"   Resets at: {reset_time.strftime('%H:%M:%S')} ({wait_minutes} minutes)")
        else:
            wait_seconds = 0
            wait_minutes = 0

        print()

        # Strategy-based handling
        if self.strategy == "fail":
            print("❌ Strategy: fail - Aborting immediately")
            if not self.interactive:
                raise RateLimitError("Rate limit exceeded (fail strategy)")
            return False

        if self.strategy == "switch" and self.auto_switch:
            # Try switching to another profile
            new_profile = self.try_switch_profile()
            if new_profile:
                return True
            else:
                print("⚠️  No alternative profiles available")
                # Fall through to other strategies

        if self.strategy == "wait":
            # Auto-wait with countdown
            return self.wait_for_reset(wait_seconds, wait_minutes)

        # Default: prompt user (if interactive)
        if self.interactive:
            return self.prompt_user_action(wait_seconds, wait_minutes)
        else:
            # Non-interactive mode: fail
            raise RateLimitError("Rate limit exceeded (non-interactive mode)")

    def try_switch_profile(self) -> bool:
        """
        Try to switch to another GitHub profile.

        Returns:
            True if switched successfully, False otherwise
        """
        if not self.token:
            return False

        next_profile_data = self.config.get_next_profile(self.token)

        if not next_profile_data:
            return False

        next_name, next_token = next_profile_data

        print(f"🔄 Switching to profile: {next_name}")

        # Check if new profile has quota
        try:
            old_token = self.token
            self.token = next_token

            rate_info = self.get_rate_limit_info()
            remaining = rate_info.get("remaining", 0)
            limit = rate_info.get("limit", 0)

            if remaining > 0:
                print(f"✅ Profile '{next_name}' has {remaining}/{limit} requests available")
                self.profile_name = next_name
                return True
            else:
                print(f"⚠️  Profile '{next_name}' also exhausted ({remaining}/{limit})")
                self.token = old_token  # Restore old token
                return False

        except Exception as e:
            print(f"❌ Failed to switch profiles: {e}")
            self.token = old_token  # Restore old token
            return False

    def wait_for_reset(self, wait_seconds: float, wait_minutes: int) -> bool:
        """
        Wait for rate limit to reset with countdown.

        Args:
            wait_seconds: Seconds to wait
            wait_minutes: Minutes to wait (for display)

        Returns:
            True if waited successfully, False if aborted
        """
        # Check timeout
        if wait_minutes > self.timeout_minutes:
            print(f"⚠️  Wait time ({wait_minutes}m) exceeds timeout ({self.timeout_minutes}m)")
            return False

        if wait_seconds <= 0:
            print("✅ Rate limit should be reset now")
            return True

        print(f"⏳ Waiting {wait_minutes} minutes for rate limit reset...")
        print("   Press Ctrl+C to cancel\n")

        try:
            if self.show_countdown:
                self.show_countdown_timer(wait_seconds)
            else:
                time.sleep(wait_seconds)

            print("\n✅ Rate limit reset! Continuing...\n")
            return True

        except KeyboardInterrupt:
            print("\n\n⏸️  Wait interrupted by user")
            return False

    def show_countdown_timer(self, total_seconds: float):
        """
        Show a live countdown timer.

        Args:
            total_seconds: Total seconds to count down
        """
        end_time = time.time() + total_seconds

        while time.time() < end_time:
            remaining = int(end_time - time.time())
            minutes, seconds = divmod(remaining, 60)

            # Print countdown on same line
            sys.stdout.write(f"\r⏱️  Resuming in {minutes:02d}:{seconds:02d}...")
            sys.stdout.flush()

            time.sleep(1)

        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear line
        sys.stdout.flush()

    def prompt_user_action(self, wait_seconds: float, wait_minutes: int) -> bool:
        """
        Prompt user for action when rate limited.

        Args:
            wait_seconds: Seconds until reset
            wait_minutes: Minutes until reset

        Returns:
            True if user chooses to continue, False to abort
        """
        print("Options:")
        print(f"  [w] Wait {wait_minutes} minutes (auto-continues)")

        # Check if profile switching is available
        if self.token and self.config.get_next_profile(self.token):
            print("  [s] Switch to another GitHub profile")

        print("  [t] Set up new GitHub token")
        print("  [c] Cancel")
        print()

        while True:
            choice = input("Select an option [w/s/t/c]: ").strip().lower()

            if choice == "w":
                return self.wait_for_reset(wait_seconds, wait_minutes)

            elif choice == "s":
                if self.try_switch_profile():
                    return True
                else:
                    print("⚠️  Profile switching failed. Choose another option.")
                    continue

            elif choice == "t":
                print("\n💡 Opening GitHub token setup...")
                print("   Run this command in another terminal:")
                print("   $ skill-seekers config --github\n")
                print("   Then restart your scraping job.\n")
                return False

            elif choice == "c":
                print("\n⏸️  Operation cancelled by user\n")
                return False

            else:
                print("❌ Invalid choice. Please enter w, s, t, or c.")


def create_github_headers(token: str | None = None) -> dict[str, str]:
    """
    Create GitHub API headers with optional token.

    Args:
        token: GitHub token (or None)

    Returns:
        Dict of headers
    """
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers
