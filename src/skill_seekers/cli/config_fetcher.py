"""
Config fetcher for CLI - synchronous wrapper around API fetch.

Provides automatic config downloading from SkillSeekersWeb.com API
when local config files are not found.
"""

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.skillseekersweb.com"

# Track last searched paths for better error messages
_last_searched_paths = []


def fetch_config_from_api(
    config_name: str, destination: str = "configs", timeout: float = 30.0
) -> Path | None:
    """
    Fetch a config file from the SkillSeekersWeb.com API.

    Args:
        config_name: Name of config to download (e.g., 'react', 'godot')
        destination: Directory to save config file (default: 'configs')
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Path to downloaded config file, or None if fetch failed

    Example:
        >>> config_path = fetch_config_from_api('react')
        >>> if config_path:
        ...     print(f"Downloaded to {config_path}")
    """
    # Normalize config name (remove .json if present)
    if config_name.endswith(".json"):
        config_name = config_name[:-5]

    # Remove 'configs/' prefix if present
    if config_name.startswith("configs/"):
        config_name = config_name[8:]

    try:
        with httpx.Client(timeout=timeout) as client:
            # Get config details first
            detail_url = f"{API_BASE_URL}/api/configs/{config_name}"
            logger.info(f"🔍 Checking API for config: {config_name}")

            detail_response = client.get(detail_url)

            if detail_response.status_code == 404:
                logger.warning(f"⚠️  Config '{config_name}' not found on API")
                return None

            detail_response.raise_for_status()
            config_info = detail_response.json()

            # Download the actual config file using download_url from API response
            download_url = config_info.get("download_url")
            if not download_url:
                logger.error(f"❌ Config '{config_name}' has no download_url. Contact support.")
                return None

            logger.info("📥 Downloading config from API...")
            download_response = client.get(download_url)
            download_response.raise_for_status()
            config_data = download_response.json()

            # Save to destination
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            config_file = dest_path / f"{config_name}.json"

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"✅ Config downloaded successfully: {config_file}")
            logger.info(f"   Category: {config_info.get('category', 'uncategorized')}")
            logger.info(f"   Type: {config_info.get('type', 'unknown')}")

            return config_file

    except httpx.HTTPError as e:
        logger.warning(f"⚠️  HTTP Error fetching config: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  Invalid JSON response from API: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️  Error fetching config: {e}")
        return None


def list_available_configs(category: str | None = None, timeout: float = 30.0) -> list[str]:
    """
    List all available configs from the API.

    Args:
        category: Filter by category (optional)
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of available config names

    Example:
        >>> configs = list_available_configs()
        >>> print(f"Available: {', '.join(configs)}")
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            list_url = f"{API_BASE_URL}/api/configs"
            params = {}
            if category:
                params["category"] = category

            response = client.get(list_url, params=params)
            response.raise_for_status()
            data = response.json()

            configs = data.get("configs", [])
            return [cfg.get("name") for cfg in configs if cfg.get("name")]

    except Exception:
        return []


def resolve_config_path(config_path: str, auto_fetch: bool = True) -> Path | None:
    """
    Resolve config path with automatic API fallback.

    Tries to find config in this order:
    1. Exact path as provided
    2. With 'configs/' prefix added (current directory)
    3. User config directory (~/.config/skill-seekers/configs/)
    4. Fetch from API (if auto_fetch=True)

    Args:
        config_path: Config file path or name
        auto_fetch: Automatically fetch from API if not found locally (default: True)

    Returns:
        Path to config file, or None if not found

    Example:
        >>> path = resolve_config_path('react.json')
        >>> if path:
        ...     with open(path) as f:
        ...         config = json.load(f)
    """
    # Track searched paths for better error messages
    global _last_searched_paths
    _last_searched_paths = []

    # 1. Try exact path
    exact_path = Path(config_path)
    _last_searched_paths.append(exact_path.resolve())
    if exact_path.exists():
        return exact_path.resolve()

    # 2. Try with configs/ prefix (current directory)
    if not config_path.startswith("configs/"):
        with_prefix = Path("configs") / config_path
        _last_searched_paths.append(with_prefix.resolve())
        if with_prefix.exists():
            return with_prefix.resolve()

    # 3. Try user config directory
    user_config_dir = Path.home() / ".config" / "skill-seekers" / "configs"

    # Extract just the filename if path contains directory separators
    config_filename = Path(config_path).name
    user_config_path = user_config_dir / config_filename
    _last_searched_paths.append(user_config_path)

    if user_config_path.exists():
        return user_config_path.resolve()

    # 4. Try API fetch (if enabled)
    if auto_fetch:
        # Extract config name (remove .json, remove configs/ prefix)
        config_name = config_path
        if config_name.endswith(".json"):
            config_name = config_name[:-5]
        if config_name.startswith("configs/"):
            config_name = config_name[8:]

        logger.info(
            "\n💡 Config not found locally, attempting to fetch from SkillSeekersWeb.com API..."
        )
        fetched_path = fetch_config_from_api(config_name, destination="configs")
        if fetched_path and fetched_path.exists():
            return fetched_path.resolve()

    return None


def get_last_searched_paths() -> list[Path]:
    """
    Get the list of paths that were searched in the last resolve_config_path call.

    Returns:
        List of absolute paths that were checked for the config file

    Example:
        >>> resolve_config_path('myconfig.json', auto_fetch=False)
        >>> paths = get_last_searched_paths()
        >>> for p in paths:
        ...     print(f"Searched: {p}")
    """
    return _last_searched_paths.copy()
