"""
Configuration Manager for Skill Seekers

Handles multi-profile GitHub tokens, API keys, and application settings.
Provides secure storage with file permissions and auto-detection capabilities.
"""

import json
import os
import stat
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manages Skill Seekers configuration with multi-token support."""

    # Default paths
    CONFIG_DIR = Path.home() / ".config" / "skill-seekers"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    WELCOME_FLAG = CONFIG_DIR / ".welcomed"
    PROGRESS_DIR = Path.home() / ".local" / "share" / "skill-seekers" / "progress"

    # Default configuration
    DEFAULT_CONFIG = {
        "version": "1.0",
        "github": {"default_profile": None, "profiles": {}},
        "rate_limit": {
            "default_timeout_minutes": 30,
            "auto_switch_profiles": True,
            "show_countdown": True,
        },
        "resume": {"auto_save_interval_seconds": 60, "keep_progress_days": 7},
        "api_keys": {"anthropic": None, "google": None, "openai": None},
        "ai_enhancement": {
            "default_enhance_level": 1,  # Default AI enhancement level (0-3)
            "local_batch_size": 20,  # Patterns per Claude CLI call (default was 5)
            "local_parallel_workers": 3,  # Concurrent Claude CLI calls
        },
        "first_run": {"completed": False, "version": "2.7.0"},
    }

    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.progress_dir = self.PROGRESS_DIR
        self._ensure_directories()

        # Check if config file exists before loading
        config_exists = self.config_file.exists()
        self.config = self._load_config()

        # Save config file if it was just created with defaults
        if not config_exists:
            self.save_config()

    def _ensure_directories(self):
        """Ensure configuration and progress directories exist with secure permissions."""
        # Create main config and progress directories
        for directory in [self.config_dir, self.progress_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            # Set directory permissions to 700 (rwx------)
            directory.chmod(stat.S_IRWXU)

        # Also create configs subdirectory for user custom configs
        configs_dir = self.config_dir / "configs"
        configs_dir.mkdir(exist_ok=True)
        configs_dir.chmod(stat.S_IRWXU)

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or create default."""
        if not self.config_file.exists():
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_file) as f:
                config = json.load(f)

            # Merge with defaults for any missing keys
            config = self._merge_with_defaults(config)
            return config
        except (OSError, json.JSONDecodeError) as e:
            print(f"⚠️  Warning: Could not load config file: {e}")
            print("   Using default configuration.")
            return self.DEFAULT_CONFIG.copy()

    def _merge_with_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist."""

        def deep_merge(default: dict, custom: dict) -> dict:
            result = default.copy()
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self.DEFAULT_CONFIG, config)

    def save_config(self):
        """Save configuration to file with secure permissions."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)

            # Set file permissions to 600 (rw-------)
            self.config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

        except OSError as e:
            print(f"❌ Error saving config: {e}")
            sys.exit(1)

    # GitHub Token Management

    def add_github_profile(
        self,
        name: str,
        token: str,
        description: str = "",
        rate_limit_strategy: str = "prompt",
        timeout_minutes: int = 30,
        set_as_default: bool = False,
    ):
        """Add a new GitHub profile."""
        if not name:
            raise ValueError("Profile name cannot be empty")

        if not token.startswith("ghp_") and not token.startswith("github_pat_"):
            print("⚠️  Warning: Token doesn't match GitHub format (ghp_* or github_pat_*)")

        profile = {
            "token": token,
            "description": description,
            "rate_limit_strategy": rate_limit_strategy,
            "timeout_minutes": timeout_minutes,
            "added_at": datetime.now().isoformat(),
        }

        self.config["github"]["profiles"][name] = profile

        if set_as_default or not self.config["github"]["default_profile"]:
            self.config["github"]["default_profile"] = name

        self.save_config()
        print(f"✅ Added GitHub profile: {name}")
        if set_as_default:
            print("✅ Set as default profile")

    def remove_github_profile(self, name: str):
        """Remove a GitHub profile."""
        if name not in self.config["github"]["profiles"]:
            raise ValueError(f"Profile '{name}' not found")

        del self.config["github"]["profiles"][name]

        # Update default if we removed it
        if self.config["github"]["default_profile"] == name:
            remaining = list(self.config["github"]["profiles"].keys())
            self.config["github"]["default_profile"] = remaining[0] if remaining else None

        self.save_config()
        print(f"✅ Removed GitHub profile: {name}")

    def list_github_profiles(self) -> list[dict[str, Any]]:
        """List all GitHub profiles."""
        profiles = []
        default = self.config["github"]["default_profile"]

        for name, data in self.config["github"]["profiles"].items():
            profile_info = {
                "name": name,
                "description": data.get("description", ""),
                "strategy": data.get("rate_limit_strategy", "prompt"),
                "timeout": data.get("timeout_minutes", 30),
                "is_default": name == default,
                "added_at": data.get("added_at", "Unknown"),
            }
            profiles.append(profile_info)

        return profiles

    def get_github_token(
        self, profile_name: str | None = None, _repo_url: str | None = None
    ) -> str | None:
        """
        Get GitHub token with smart fallback chain.

        Priority:
        1. Specified profile_name
        2. Environment variable GITHUB_TOKEN
        3. Default profile from config
        4. None (will use 60/hour unauthenticated)
        """
        # 1. Check specified profile
        if profile_name:
            profile = self.config["github"]["profiles"].get(profile_name)
            if profile:
                return profile["token"]
            else:
                print(f"⚠️  Warning: Profile '{profile_name}' not found")

        # 2. Check environment variable
        env_token = os.getenv("GITHUB_TOKEN")
        if env_token:
            return env_token

        # 3. Check default profile
        default_profile = self.config["github"]["default_profile"]
        if default_profile:
            profile = self.config["github"]["profiles"].get(default_profile)
            if profile:
                return profile["token"]

        # 4. No token available
        return None

    def get_profile_for_token(self, token: str) -> str | None:
        """Get profile name for a given token."""
        for name, profile in self.config["github"]["profiles"].items():
            if profile["token"] == token:
                return name
        return None

    def get_next_profile(self, current_token: str) -> tuple | None:
        """
        Get next available profile for rate limit switching.

        Returns: (profile_name, token) or None
        """
        profiles = list(self.config["github"]["profiles"].items())
        if len(profiles) <= 1:
            return None

        # Find current profile index
        current_idx = None
        for idx, (_name, profile) in enumerate(profiles):
            if profile["token"] == current_token:
                current_idx = idx
                break

        if current_idx is None:
            # Current token not in profiles, return first profile
            name, profile = profiles[0]
            return (name, profile["token"])

        # Return next profile (circular)
        next_idx = (current_idx + 1) % len(profiles)
        name, profile = profiles[next_idx]
        return (name, profile["token"])

    def get_rate_limit_strategy(self, token: str | None = None) -> str:
        """Get rate limit strategy for a token (or default)."""
        if token:
            profile_name = self.get_profile_for_token(token)
            if profile_name:
                profile = self.config["github"]["profiles"][profile_name]
                return profile.get("rate_limit_strategy", "prompt")

        # Default strategy
        return "prompt"

    def get_timeout_minutes(self, token: str | None = None) -> int:
        """Get timeout minutes for a token (or default)."""
        if token:
            profile_name = self.get_profile_for_token(token)
            if profile_name:
                profile = self.config["github"]["profiles"][profile_name]
                return profile.get("timeout_minutes", 30)

        return self.config["rate_limit"]["default_timeout_minutes"]

    # API Keys Management

    def set_api_key(self, provider: str, key: str):
        """Set API key for a provider (anthropic, google, openai)."""
        if provider not in self.config["api_keys"]:
            raise ValueError(f"Unknown provider: {provider}. Use: anthropic, google, openai")

        self.config["api_keys"][provider] = key
        self.save_config()
        print(f"✅ Set {provider.capitalize()} API key")

    def get_api_key(self, provider: str) -> str | None:
        """
        Get API key with environment variable fallback.

        Priority:
        1. Environment variable
        2. Config file
        """
        # Check environment first
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
        }

        env_var = env_map.get(provider)
        if env_var:
            env_key = os.getenv(env_var)
            if env_key:
                return env_key

        # Check config file
        return self.config["api_keys"].get(provider)

    # Progress Management

    def save_progress(self, job_id: str, progress_data: dict[str, Any]):
        """Save progress for a job."""
        progress_file = self.progress_dir / f"{job_id}.json"

        progress_data["last_updated"] = datetime.now().isoformat()

        with open(progress_file, "w") as f:
            json.dump(progress_data, f, indent=2)

        # Set file permissions to 600
        progress_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def load_progress(self, job_id: str) -> dict[str, Any] | None:
        """Load progress for a job."""
        progress_file = self.progress_dir / f"{job_id}.json"

        if not progress_file.exists():
            return None

        try:
            with open(progress_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def list_resumable_jobs(self) -> list[dict[str, Any]]:
        """List all resumable jobs."""
        jobs = []

        for progress_file in self.progress_dir.glob("*.json"):
            try:
                with open(progress_file) as f:
                    data = json.load(f)

                if data.get("can_resume", False):
                    jobs.append(
                        {
                            "job_id": data.get("job_id", progress_file.stem),
                            "started_at": data.get("started_at"),
                            "command": data.get("command"),
                            "progress": data.get("progress", {}),
                            "last_updated": data.get("last_updated"),
                        }
                    )
            except (OSError, json.JSONDecodeError):
                continue

        # Sort by last updated (newest first)
        jobs.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return jobs

    def delete_progress(self, job_id: str):
        """Delete progress file for a job."""
        progress_file = self.progress_dir / f"{job_id}.json"
        if progress_file.exists():
            progress_file.unlink()

    def cleanup_old_progress(self):
        """Delete progress files older than configured days."""
        keep_days = self.config["resume"]["keep_progress_days"]
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        deleted_count = 0
        for progress_file in self.progress_dir.glob("*.json"):
            # Check file modification time
            mtime = datetime.fromtimestamp(progress_file.stat().st_mtime)
            if mtime < cutoff_date:
                progress_file.unlink()
                deleted_count += 1

        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old progress file(s)")

    # AI Enhancement Settings

    def get_default_enhance_level(self) -> int:
        """Get default AI enhancement level (0-3)."""
        return self.config.get("ai_enhancement", {}).get("default_enhance_level", 1)

    def set_default_enhance_level(self, level: int):
        """Set default AI enhancement level (0-3)."""
        if level not in [0, 1, 2, 3]:
            raise ValueError("enhance_level must be 0, 1, 2, or 3")
        if "ai_enhancement" not in self.config:
            self.config["ai_enhancement"] = {}
        self.config["ai_enhancement"]["default_enhance_level"] = level
        self.save_config()

    def get_local_batch_size(self) -> int:
        """Get batch size for LOCAL mode AI enhancement."""
        return self.config.get("ai_enhancement", {}).get("local_batch_size", 20)

    def set_local_batch_size(self, size: int):
        """Set batch size for LOCAL mode AI enhancement."""
        if "ai_enhancement" not in self.config:
            self.config["ai_enhancement"] = {}
        self.config["ai_enhancement"]["local_batch_size"] = size
        self.save_config()

    def get_local_parallel_workers(self) -> int:
        """Get number of parallel workers for LOCAL mode AI enhancement."""
        return self.config.get("ai_enhancement", {}).get("local_parallel_workers", 3)

    def set_local_parallel_workers(self, workers: int):
        """Set number of parallel workers for LOCAL mode AI enhancement."""
        if "ai_enhancement" not in self.config:
            self.config["ai_enhancement"] = {}
        self.config["ai_enhancement"]["local_parallel_workers"] = workers
        self.save_config()

    # First Run Experience

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self.config["first_run"]["completed"]

    def mark_first_run_complete(self):
        """Mark first run as completed."""
        self.config["first_run"]["completed"] = True
        self.save_config()

    def should_show_welcome(self) -> bool:
        """Check if we should show welcome message."""
        return not self.WELCOME_FLAG.exists()

    def mark_welcome_shown(self):
        """Mark welcome message as shown."""
        self.WELCOME_FLAG.touch()
        self.WELCOME_FLAG.chmod(stat.S_IRUSR | stat.S_IWUSR)

    # Display Helpers

    def display_config_summary(self):
        """Display current configuration summary."""
        print("\n📋 Skill Seekers Configuration\n")
        print(f"Config file: {self.config_file}")
        print(f"Custom configs dir: {self.config_dir / 'configs'}")
        print(f"Progress dir: {self.progress_dir}\n")

        # GitHub profiles
        profiles = self.list_github_profiles()
        print(f"GitHub Profiles: {len(profiles)}")
        if profiles:
            for p in profiles:
                default_marker = " (default)" if p["is_default"] else ""
                print(f"  • {p['name']}{default_marker}")
                if p["description"]:
                    print(f"    {p['description']}")
                print(f"    Strategy: {p['strategy']}, Timeout: {p['timeout']}m")
        else:
            print("  (none configured)")

        print()

        # API Keys
        print("API Keys:")
        for provider in ["anthropic", "google", "openai"]:
            key = self.get_api_key(provider)
            status = "✅ Set" if key else "❌ Not set"
            source = ""
            if key:
                if os.getenv(provider.upper() + "_API_KEY"):
                    source = " (from environment)"
                else:
                    source = " (from config)"
            print(f"  • {provider.capitalize()}: {status}{source}")

        print()

        # Settings
        print("Settings:")
        print(f"  • Rate limit timeout: {self.config['rate_limit']['default_timeout_minutes']}m")
        print(f"  • Auto-switch profiles: {self.config['rate_limit']['auto_switch_profiles']}")
        print(f"  • Keep progress for: {self.config['resume']['keep_progress_days']} days")

        # AI Enhancement settings
        level_names = {0: "off", 1: "SKILL.md only", 2: "standard", 3: "full"}
        default_level = self.get_default_enhance_level()
        print("\nAI Enhancement:")
        print(f"  • Default level: {default_level} ({level_names.get(default_level, 'unknown')})")
        print(f"  • Batch size: {self.get_local_batch_size()} patterns per call")
        print(f"  • Parallel workers: {self.get_local_parallel_workers()} concurrent calls")

        # Resumable jobs
        jobs = self.list_resumable_jobs()
        if jobs:
            print(f"\n📦 Resumable Jobs: {len(jobs)}")
            for job in jobs[:5]:  # Show max 5
                print(f"  • {job['job_id']}")
                if job.get("progress"):
                    phase = job["progress"].get("phase", "unknown")
                    print(f"    Phase: {phase}, Last: {job['last_updated']}")


# Global instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get singleton config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
