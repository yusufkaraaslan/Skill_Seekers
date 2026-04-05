#!/usr/bin/env python3
"""
Slack/Discord Chat Export to Skill Converter

Converts chat history from Slack and Discord into AI-ready skills.
Supports two modes of operation per platform:

**Export mode** (offline, no API key required):
  - Slack: Parse workspace export ZIP/directory (JSON files per channel per day)
  - Discord: Parse DiscordChatExporter JSON output

**API mode** (live, requires authentication token):
  - Slack: Fetch messages via Slack Web API (slack_sdk)
  - Discord: Fetch messages via Discord HTTP API (discord.py or aiohttp)

Extracted content includes messages, threads, reactions, code snippets,
shared links, attachments, and user references. Messages are categorized
by channel, date, and detected topic for structured skill output.

Usage:
    # Slack workspace export (directory or ZIP)
    skill-seekers chat --export-path ./slack-export/ --platform slack --name myteam

    # Slack API (live fetch)
    skill-seekers chat --platform slack --token xoxb-... --channel C01234 --name myteam

    # Discord export (DiscordChatExporter JSON)
    skill-seekers chat --export-path ./discord-export.json --platform discord --name myserver

    # Discord API (live fetch)
    skill-seekers chat --platform discord --token Bot ... --channel 12345 --name myserver

    # Build from previously extracted JSON
    skill-seekers chat --from-json myteam_extracted.json --name myteam
"""

import argparse
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Optional dependency guard — Slack SDK
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

# Optional dependency guard — Discord
try:
    import discord  # noqa: F401

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum messages to fetch per channel when using API mode
DEFAULT_MAX_MESSAGES = 5000

# Topic keywords for automatic content categorization
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "troubleshooting": [
        "error",
        "bug",
        "fix",
        "issue",
        "broken",
        "crash",
        "exception",
        "traceback",
        "debug",
        "failing",
        "stacktrace",
        "segfault",
    ],
    "setup": [
        "install",
        "setup",
        "configure",
        "config",
        "environment",
        "docker",
        "deploy",
        "ci/cd",
        "pipeline",
        "build",
        "dependency",
    ],
    "architecture": [
        "design",
        "architecture",
        "pattern",
        "refactor",
        "abstraction",
        "interface",
        "module",
        "service",
        "microservice",
        "api",
    ],
    "code_review": [
        "review",
        "pr",
        "pull request",
        "merge",
        "approve",
        "lgtm",
        "nit",
        "suggestion",
        "feedback",
        "diff",
    ],
    "howto": [
        "how to",
        "how do",
        "tutorial",
        "example",
        "guide",
        "walkthrough",
        "step by step",
        "documentation",
        "docs",
    ],
    "release": [
        "release",
        "version",
        "changelog",
        "migration",
        "upgrade",
        "breaking change",
        "deprecat",
        "v1",
        "v2",
        "v3",
    ],
    "performance": [
        "performance",
        "slow",
        "fast",
        "optimize",
        "latency",
        "throughput",
        "benchmark",
        "profil",
        "memory",
        "cpu",
    ],
    "testing": [
        "test",
        "pytest",
        "unittest",
        "coverage",
        "mock",
        "fixture",
        "assertion",
        "spec",
        "e2e",
        "integration test",
    ],
}


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------


def _check_slack_deps() -> None:
    """Raise RuntimeError if slack_sdk is not installed."""
    if not SLACK_AVAILABLE:
        raise RuntimeError(
            "slack_sdk is required for Slack API support.\n"
            'Install with: pip install "skill-seekers[slack]"\n'
            "Or: pip install slack_sdk"
        )


def _check_discord_deps() -> None:
    """Raise RuntimeError if discord.py is not installed."""
    if not DISCORD_AVAILABLE:
        raise RuntimeError(
            "discord.py is required for Discord API support.\n"
            'Install with: pip install "skill-seekers[discord]"\n'
            "Or: pip install discord.py"
        )


# ---------------------------------------------------------------------------
# Helper: code quality scoring (consistent with other scrapers)
# ---------------------------------------------------------------------------


def _score_code_quality(code: str) -> float:
    """Score code quality on a 0-10 scale using heuristics.

    Args:
        code: Source code text to score.

    Returns:
        Float quality score between 0.0 and 10.0.
    """
    if not code:
        return 0.0

    score = 5.0
    lines = code.strip().split("\n")
    line_count = len(lines)

    if line_count >= 10:
        score += 2.0
    elif line_count >= 5:
        score += 1.0

    if re.search(r"\b(def |class |function |func |fn )", code):
        score += 1.5
    if re.search(r"\b(import |from .+ import|require\(|#include|using )", code):
        score += 0.5
    if re.search(r"^    ", code, re.MULTILINE):
        score += 0.5
    if re.search(r"[=:{}()\[\]]", code):
        score += 0.3
    if len(code) < 30:
        score -= 2.0

    return min(10.0, max(0.0, score))


# ---------------------------------------------------------------------------
# Main converter class
# ---------------------------------------------------------------------------


class ChatToSkillConverter:
    """Convert Slack or Discord chat history into an AI-ready skill.

    Follows the same pipeline pattern as the EPUB, Jupyter, and PPTX scrapers:
    extract -> categorize -> build_skill (reference files + index + SKILL.md).

    Supports two input modes per platform:
    - **Export mode**: Parse a previously exported archive (Slack workspace
      export directory/ZIP or DiscordChatExporter JSON).
    - **API mode**: Fetch messages live from the platform's API using an
      authentication token.

    The extraction phase produces a normalized intermediate JSON containing
    messages with text, user, timestamp, reactions, threads, attachments,
    code snippets, and shared links. Messages are then categorized by
    channel, date range, and detected topic.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the converter with a configuration dictionary.

        Args:
            config: Configuration dict with keys:
                - name (str): Skill name (required).
                - export_path (str): Path to export file/directory (optional).
                - platform (str): "slack" or "discord" (default "slack").
                - token (str): API authentication token (optional, API mode).
                - channel (str): Channel ID to fetch (optional, API mode).
                - max_messages (int): Max messages to fetch per channel
                  (default 5000).
                - description (str): Skill description (optional, inferred
                  if absent).
        """
        self.config = config
        self.name: str = config["name"]
        self.export_path: str = config.get("export_path", "")
        self.platform: str = config.get("platform", "slack").lower()
        self.token: str = config.get("token", "")
        self.channel: str = config.get("channel", "")
        self.max_messages: int = config.get("max_messages", DEFAULT_MAX_MESSAGES)
        self.description: str = (
            config.get("description") or f"Use when referencing {self.name} chat knowledge base"
        )

        # Output paths
        self.skill_dir: str = f"output/{self.name}"
        self.data_file: str = f"output/{self.name}_extracted.json"

        # Extracted data (populated by extract_chat or load_extracted_data)
        self.extracted_data: dict | None = None

    # ------------------------------------------------------------------
    # Extraction — public entry point
    # ------------------------------------------------------------------

    def extract_chat(self) -> bool:
        """Extract chat content based on platform and input mode.

        Dispatches to the appropriate extraction method:
        - Export mode (export_path set): parse local export files.
        - API mode (token set): fetch messages via platform API.

        Returns:
            True on successful extraction.

        Raises:
            ValueError: If neither export_path nor token is provided, or
                if the platform is not recognized.
        """
        if self.platform not in ("slack", "discord"):
            raise ValueError(
                f"Unsupported platform: '{self.platform}'. Supported platforms: 'slack', 'discord'"
            )

        # Determine mode
        if self.export_path:
            print(f"\n🔍 Extracting {self.platform} chat from export: {self.export_path}")
            if self.platform == "slack":
                messages = self._extract_slack_export()
            else:
                messages = self._extract_discord_export()
        elif self.token:
            print(f"\n🔍 Fetching {self.platform} chat via API...")
            if self.platform == "slack":
                _check_slack_deps()
                messages = self._extract_slack_api()
            else:
                _check_discord_deps()
                messages = self._extract_discord_api()
        else:
            raise ValueError(
                "Must provide either --export-path (export mode) "
                "or --token (API mode) for chat extraction."
            )

        if not messages:
            logger.warning("No messages extracted from %s source", self.platform)
            print("   ⚠️  No messages were extracted.")

        # Identify threads and extract enrichment
        threads = self._identify_threads(messages)
        code_snippets = self._extract_code_snippets(messages)
        links = self._extract_links(messages)
        channel_summaries = self._summarize_channels(messages)

        # Group messages into sections by channel
        sections = self._build_sections(messages, threads)

        # Compute statistics
        total_messages = len(messages)
        total_threads = len(threads)
        total_code_snippets = len(code_snippets)
        total_links = len(links)
        unique_users = len({m.get("user", "unknown") for m in messages})
        channels_found = list(channel_summaries.keys())

        result_data = {
            "source": self.export_path or f"{self.platform}-api",
            "platform": self.platform,
            "metadata": {
                "total_messages": total_messages,
                "total_threads": total_threads,
                "total_code_snippets": total_code_snippets,
                "total_links": total_links,
                "unique_users": unique_users,
                "channels": channels_found,
            },
            "total_sections": len(sections),
            "total_code_blocks": total_code_snippets,
            "channel_summaries": channel_summaries,
            "code_snippets": code_snippets[:100],  # Keep top 100 for JSON size
            "links": links[:200],
            "pages": sections,
        }

        # Save extracted data
        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Saved extracted data to: {self.data_file}")
        self.extracted_data = result_data
        print(
            f"✅ Extracted {total_messages} messages across "
            f"{len(channels_found)} channel(s), "
            f"{total_threads} threads, "
            f"{total_code_snippets} code snippets"
        )
        return True

    # ------------------------------------------------------------------
    # Load previously extracted data
    # ------------------------------------------------------------------

    def load_extracted_data(self, json_path: str) -> bool:
        """Load previously extracted data from JSON file.

        Args:
            json_path: Path to the extracted JSON file.

        Returns:
            True on success.
        """
        print(f"\n📂 Loading extracted data from: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)
        total = self.extracted_data.get("total_sections", len(self.extracted_data.get("pages", [])))
        print(f"✅ Loaded {total} sections")
        return True

    # ------------------------------------------------------------------
    # Categorization
    # ------------------------------------------------------------------

    def categorize_content(self) -> dict[str, dict]:
        """Categorize sections by channel, date range, and detected topic.

        Groups the extracted sections into categories suitable for
        generating reference files. Each category contains a title
        and a list of page/section dicts.

        Returns:
            Dict mapping category keys to dicts with 'title' and 'pages'.
        """
        print("\n📋 Categorizing content...")

        categorized: dict[str, dict] = {}
        sections = self.extracted_data.get("pages", [])

        if not sections:
            categorized["content"] = {"title": "Chat Content", "pages": []}
            print("✅ Created 0 categories (no content)")
            return categorized

        # Group sections by channel name
        by_channel: dict[str, list[dict]] = defaultdict(list)
        for section in sections:
            channel = section.get("channel", "general")
            by_channel[channel].append(section)

        if len(by_channel) <= 1:
            # Single channel — categorize by topic instead
            all_sections = sections
            topic_buckets: dict[str, list[dict]] = defaultdict(list)
            uncategorized: list[dict] = []

            for section in all_sections:
                combined = self._section_text(section)
                matched_topic = ""
                best_score = 0
                for topic, keywords in _TOPIC_KEYWORDS.items():
                    score = sum(1 for kw in keywords if kw.lower() in combined)
                    if score > best_score:
                        best_score = score
                        matched_topic = topic
                if matched_topic and best_score >= 2:
                    topic_buckets[matched_topic].append(section)
                else:
                    uncategorized.append(section)

            for topic, pages in sorted(topic_buckets.items()):
                categorized[topic] = {
                    "title": topic.replace("_", " ").title(),
                    "pages": pages,
                }
            if uncategorized:
                categorized["general"] = {
                    "title": "General Discussion",
                    "pages": uncategorized,
                }
        else:
            # Multiple channels — use channel names as categories
            for channel, channel_sections in sorted(by_channel.items()):
                cat_key = self._sanitize_filename(channel)
                categorized[cat_key] = {
                    "title": f"#{channel}",
                    "pages": channel_sections,
                }

        if not categorized:
            categorized["content"] = {"title": "Chat Content", "pages": sections}

        print(f"✅ Created {len(categorized)} categories")
        for cat_data in categorized.values():
            print(f"   - {cat_data['title']}: {len(cat_data['pages'])} sections")

        return categorized

    # ------------------------------------------------------------------
    # Build skill
    # ------------------------------------------------------------------

    def build_skill(self) -> None:
        """Build complete skill directory structure from extracted data.

        Creates the output directory tree with:
        - references/ — one markdown file per category
        - references/index.md — category index with statistics
        - SKILL.md — main skill file with frontmatter and overview
        - scripts/ — reserved for future use
        - assets/ — reserved for future use
        """
        print(f"\n🏗️  Building skill: {self.name}")

        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        categorized = self.categorize_content()

        print("\n📝 Generating reference files...")
        total_categories = len(categorized)
        for section_num, (cat_key, cat_data) in enumerate(categorized.items(), 1):
            self._generate_reference_file(cat_key, cat_data, section_num, total_categories)

        self._generate_index(categorized)
        self._generate_skill_md(categorized)

        print(f"\n✅ Skill built successfully: {self.skill_dir}/")
        print(f"\n📦 Next step: Package with: skill-seekers package {self.skill_dir}/")

    # ------------------------------------------------------------------
    # Slack export extraction
    # ------------------------------------------------------------------

    def _extract_slack_export(self) -> list[dict]:
        """Parse a Slack workspace export directory.

        Slack exports contain one directory per channel, each with JSON
        files named by date (e.g., ``2024-01-15.json``). Each JSON file
        is a list of message objects.

        Returns:
            List of normalized message dicts.

        Raises:
            FileNotFoundError: If export_path does not exist.
            ValueError: If the path structure is not a valid Slack export.
        """
        export_path = Path(self.export_path)
        if not export_path.exists():
            raise FileNotFoundError(f"Slack export path not found: {self.export_path}")

        # Handle ZIP archives
        if export_path.is_file() and export_path.suffix == ".zip":
            export_path = self._unzip_export(export_path)

        if not export_path.is_dir():
            raise ValueError(
                f"Expected a directory for Slack export, got: {self.export_path}\n"
                "Slack workspace exports are directories containing channel "
                "subdirectories with daily JSON files."
            )

        messages: list[dict] = []
        channel_dirs = sorted(
            d for d in export_path.iterdir() if d.is_dir() and not d.name.startswith(".")
        )

        if not channel_dirs:
            raise ValueError(
                f"No channel directories found in Slack export: {self.export_path}\n"
                "Expected subdirectories named after channels (e.g., general/, random/)."
            )

        # Load users.json if available (for display name resolution)
        users_map = self._load_slack_users(export_path)

        for channel_dir in channel_dirs:
            channel_name = channel_dir.name
            json_files = sorted(channel_dir.glob("*.json"))

            for json_file in json_files:
                try:
                    with open(json_file, encoding="utf-8") as f:
                        day_messages = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Failed to parse %s: %s", json_file, e)
                    continue

                if not isinstance(day_messages, list):
                    continue

                for raw_msg in day_messages:
                    parsed = self._parse_slack_message(raw_msg, channel_name, users_map)
                    if parsed:
                        messages.append(parsed)

            print(f"   📁 #{channel_name}: {len(json_files)} day file(s)")

        print(f"   Total messages parsed: {len(messages)}")
        return messages

    def _load_slack_users(self, export_dir: Path) -> dict[str, str]:
        """Load user ID -> display name mapping from users.json.

        Args:
            export_dir: Root directory of the Slack export.

        Returns:
            Dict mapping user IDs to display names.
        """
        users_file = export_dir / "users.json"
        if not users_file.exists():
            return {}

        try:
            with open(users_file, encoding="utf-8") as f:
                users_list = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

        users_map: dict[str, str] = {}
        if isinstance(users_list, list):
            for user in users_list:
                uid = user.get("id", "")
                display = (
                    user.get("profile", {}).get("display_name")
                    or user.get("profile", {}).get("real_name")
                    or user.get("real_name")
                    or user.get("name", uid)
                )
                if uid:
                    users_map[uid] = display

        return users_map

    def _unzip_export(self, zip_path: Path) -> Path:
        """Extract a ZIP export to a temporary directory.

        Args:
            zip_path: Path to the ZIP archive.

        Returns:
            Path to the extracted directory.
        """
        import zipfile

        extract_dir = zip_path.parent / zip_path.stem
        if extract_dir.exists():
            print(f"   Using existing extracted directory: {extract_dir}")
            return extract_dir

        print(f"   Extracting ZIP: {zip_path} -> {extract_dir}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        return extract_dir

    # ------------------------------------------------------------------
    # Slack API extraction
    # ------------------------------------------------------------------

    def _extract_slack_api(self) -> list[dict]:
        """Fetch messages from Slack via the Web API using slack_sdk.

        Requires ``self.token`` to be set to a valid Slack Bot or User
        token. If ``self.channel`` is set, only that channel is fetched;
        otherwise all accessible channels are iterated.

        Returns:
            List of normalized message dicts.

        Raises:
            RuntimeError: If the API call fails.
        """
        client = WebClient(token=self.token)
        messages: list[dict] = []

        try:
            # Determine channels to fetch
            if self.channel:
                channel_ids = [self.channel]
                channel_names = {self.channel: self.channel}
            else:
                # List all accessible channels
                result = client.conversations_list(
                    types="public_channel,private_channel",
                    limit=200,
                )
                channels = result.get("channels", [])
                channel_ids = [ch["id"] for ch in channels]
                channel_names = {ch["id"]: ch.get("name", ch["id"]) for ch in channels}
                print(f"   Found {len(channel_ids)} channel(s)")

            for ch_id in channel_ids:
                ch_name = channel_names.get(ch_id, ch_id)
                ch_messages = self._fetch_slack_channel_messages(client, ch_id, ch_name)
                messages.extend(ch_messages)
                print(f"   📡 #{ch_name}: {len(ch_messages)} messages")

        except SlackApiError as e:
            raise RuntimeError(
                f"Slack API error: {e.response['error']}\n"
                "Check your token permissions (channels:history, channels:read)."
            ) from e

        print(f"   Total messages fetched: {len(messages)}")
        return messages

    def _fetch_slack_channel_messages(
        self, client: "WebClient", channel_id: str, channel_name: str
    ) -> list[dict]:
        """Fetch all messages from a single Slack channel with pagination.

        Args:
            client: Authenticated slack_sdk WebClient.
            channel_id: Slack channel ID.
            channel_name: Human-readable channel name.

        Returns:
            List of normalized message dicts.
        """
        messages: list[dict] = []
        cursor = None
        fetched = 0

        while fetched < self.max_messages:
            kwargs: dict = {
                "channel": channel_id,
                "limit": min(200, self.max_messages - fetched),
            }
            if cursor:
                kwargs["cursor"] = cursor

            result = client.conversations_history(**kwargs)
            batch = result.get("messages", [])
            if not batch:
                break

            for raw_msg in batch:
                parsed = self._parse_slack_message(raw_msg, channel_name, {})
                if parsed:
                    messages.append(parsed)

            fetched += len(batch)

            # Pagination
            response_meta = result.get("response_metadata", {})
            cursor = response_meta.get("next_cursor")
            if not cursor:
                break

        return messages

    # ------------------------------------------------------------------
    # Discord export extraction
    # ------------------------------------------------------------------

    def _extract_discord_export(self) -> list[dict]:
        """Parse a Discord chat export in DiscordChatExporter JSON format.

        DiscordChatExporter produces a single JSON file per channel with
        a ``messages`` array. Each message object has ``id``, ``content``,
        ``author``, ``timestamp``, ``attachments``, ``reactions``, etc.

        Returns:
            List of normalized message dicts.

        Raises:
            FileNotFoundError: If export_path does not exist.
            ValueError: If the file is not valid JSON or has unexpected structure.
        """
        export_path = Path(self.export_path)
        if not export_path.exists():
            raise FileNotFoundError(f"Discord export path not found: {self.export_path}")

        # Support single file or directory of JSON files
        json_files: list[Path] = []
        if export_path.is_file():
            json_files = [export_path]
        elif export_path.is_dir():
            json_files = sorted(export_path.glob("*.json"))
        else:
            raise ValueError(f"Invalid export path: {self.export_path}")

        if not json_files:
            raise ValueError(f"No JSON files found in Discord export: {self.export_path}")

        messages: list[dict] = []

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    export_data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to parse %s: %s", json_file, e)
                continue

            # DiscordChatExporter format: top-level object with "messages" key
            if isinstance(export_data, dict):
                channel_info = export_data.get("channel", {})
                channel_name = (
                    channel_info.get("name", json_file.stem)
                    if isinstance(channel_info, dict)
                    else json_file.stem
                )
                raw_messages = export_data.get("messages", [])
            elif isinstance(export_data, list):
                # Some exporters produce a bare list of messages
                channel_name = json_file.stem
                raw_messages = export_data
            else:
                logger.warning("Unexpected JSON structure in %s", json_file)
                continue

            for raw_msg in raw_messages:
                parsed = self._parse_discord_message(raw_msg, channel_name)
                if parsed:
                    messages.append(parsed)

            print(f"   📁 #{channel_name}: {len(raw_messages)} messages")

        print(f"   Total messages parsed: {len(messages)}")
        return messages

    # ------------------------------------------------------------------
    # Discord API extraction
    # ------------------------------------------------------------------

    def _extract_discord_api(self) -> list[dict]:
        """Fetch messages from Discord via the HTTP API.

        Uses aiohttp directly (not the discord.py gateway client) to
        fetch channel history. Requires a Bot token and channel ID.

        Returns:
            List of normalized message dicts.

        Raises:
            RuntimeError: If the API call fails.
            ValueError: If no channel ID is provided.
        """
        if not self.channel:
            raise ValueError(
                "Discord API mode requires --channel (channel ID). "
                "Find channel IDs in Discord Developer Mode."
            )

        import asyncio

        try:
            import aiohttp
        except ImportError:
            raise RuntimeError(
                "aiohttp is required for Discord API mode.\nInstall with: pip install aiohttp"
            ) from None

        async def _fetch() -> list[dict]:
            messages: list[dict] = []
            base_url = "https://discord.com/api/v10"
            headers = {"Authorization": f"Bot {self.token}"}

            # Get channel info
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/channels/{self.channel}", headers=headers
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise RuntimeError(
                            f"Discord API error (HTTP {resp.status}): {body}\n"
                            "Check your Bot token and channel ID."
                        )
                    channel_info = await resp.json()
                    channel_name = channel_info.get("name", self.channel)

                # Fetch messages with pagination (before= cursor)
                before: str | None = None
                fetched = 0

                while fetched < self.max_messages:
                    params: dict[str, str | int] = {"limit": min(100, self.max_messages - fetched)}
                    if before:
                        params["before"] = before

                    async with session.get(
                        f"{base_url}/channels/{self.channel}/messages",
                        headers=headers,
                        params=params,
                    ) as resp:
                        if resp.status != 200:
                            body = await resp.text()
                            logger.warning("Discord API error fetching messages: %s", body)
                            break
                        batch = await resp.json()

                    if not batch:
                        break

                    for raw_msg in batch:
                        parsed = self._parse_discord_message(raw_msg, channel_name)
                        if parsed:
                            messages.append(parsed)

                    fetched += len(batch)
                    before = batch[-1]["id"]

            print(f"   📡 #{channel_name}: {len(messages)} messages")
            return messages

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_fetch())
        finally:
            loop.close()

    # ------------------------------------------------------------------
    # Message parsing
    # ------------------------------------------------------------------

    def _parse_slack_message(
        self, raw: dict, channel: str, users_map: dict[str, str]
    ) -> dict | None:
        """Parse a single Slack message into normalized format.

        Handles regular messages, bot messages, and subtypes like
        ``channel_join``, ``channel_leave``, ``file_share``, etc.
        System subtypes (join/leave/topic) are skipped.

        Args:
            raw: Raw Slack message dict from export or API.
            channel: Channel name this message belongs to.
            users_map: User ID -> display name mapping.

        Returns:
            Normalized message dict, or None if the message should be skipped.
        """
        # Skip system messages
        subtype = raw.get("subtype", "")
        skip_subtypes = {
            "channel_join",
            "channel_leave",
            "channel_topic",
            "channel_purpose",
            "channel_name",
            "channel_archive",
            "channel_unarchive",
            "group_join",
            "group_leave",
        }
        if subtype in skip_subtypes:
            return None

        text = raw.get("text", "").strip()
        if not text and not raw.get("files") and not raw.get("attachments"):
            return None

        # Resolve user
        user_id = raw.get("user", raw.get("bot_id", "unknown"))
        user_name = users_map.get(user_id, user_id)
        if raw.get("username"):
            user_name = raw["username"]

        # Parse timestamp
        ts = raw.get("ts", "0")
        try:
            timestamp = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
        except (ValueError, TypeError, OSError):
            timestamp = ts

        # Resolve user mentions in text: <@U12345> -> @username
        def _resolve_mention(match: re.Match) -> str:
            uid = match.group(1)
            return f"@{users_map.get(uid, uid)}"

        text = re.sub(r"<@(U[A-Z0-9]+)>", _resolve_mention, text)

        # Decode Slack link format: <url|label> -> label (url)
        text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2 (\1)", text)
        text = re.sub(r"<(https?://[^>]+)>", r"\1", text)

        # Reactions
        reactions = []
        for reaction in raw.get("reactions", []):
            reactions.append(
                {
                    "emoji": reaction.get("name", ""),
                    "count": reaction.get("count", 0),
                }
            )

        # Attachments / files
        attachments = []
        for f in raw.get("files", []):
            attachments.append(
                {
                    "name": f.get("name", f.get("title", "unnamed")),
                    "type": f.get("mimetype", f.get("filetype", "")),
                    "url": f.get("url_private", f.get("permalink", "")),
                }
            )
        for att in raw.get("attachments", []):
            attachments.append(
                {
                    "name": att.get("title", att.get("fallback", "attachment")),
                    "type": "link",
                    "url": att.get("from_url", att.get("title_link", "")),
                    "text": att.get("text", ""),
                }
            )

        # Thread info
        thread_ts = raw.get("thread_ts")
        is_thread_parent = thread_ts == ts and raw.get("reply_count", 0) > 0
        reply_count = raw.get("reply_count", 0) if is_thread_parent else 0

        return {
            "platform": "slack",
            "channel": channel,
            "user": user_name,
            "user_id": user_id,
            "text": text,
            "timestamp": timestamp,
            "ts": ts,
            "thread_ts": thread_ts,
            "is_thread_parent": is_thread_parent,
            "reply_count": reply_count,
            "reactions": reactions,
            "attachments": attachments,
            "subtype": subtype,
        }

    def _parse_discord_message(self, raw: dict, channel: str) -> dict | None:
        """Parse a single Discord message into normalized format.

        Handles regular messages, embeds, and attachments. System messages
        (type != 0 and type != 19) are skipped.

        Args:
            raw: Raw Discord message dict from export or API.
            channel: Channel name this message belongs to.

        Returns:
            Normalized message dict, or None if the message should be skipped.
        """
        # Skip system messages (type 0 = DEFAULT, 19 = REPLY)
        msg_type = raw.get("type", 0)
        if isinstance(msg_type, int) and msg_type not in (0, 19):
            return None
        # DiscordChatExporter uses string type names
        if isinstance(msg_type, str) and msg_type not in ("Default", "Reply"):
            return None

        content = raw.get("content", "").strip()

        # Extract author info
        author = raw.get("author", {})
        if isinstance(author, dict):
            user_name = (
                author.get("nickname") or author.get("name") or author.get("username", "unknown")
            )
            user_id = str(author.get("id", "unknown"))
        else:
            user_name = str(author)
            user_id = str(author)

        # Parse timestamp
        raw_ts = raw.get("timestamp", "")
        try:
            if isinstance(raw_ts, str) and raw_ts:
                # ISO 8601 format from Discord API
                dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                timestamp = dt.isoformat()
            else:
                timestamp = str(raw_ts)
        except (ValueError, TypeError):
            timestamp = str(raw_ts)

        # Skip empty messages with no content and no attachments
        embeds = raw.get("embeds", [])
        attachments_raw = raw.get("attachments", [])
        if not content and not embeds and not attachments_raw:
            return None

        # Reactions
        reactions = []
        for reaction in raw.get("reactions", []):
            emoji_data = reaction.get("emoji", {})
            if isinstance(emoji_data, dict):
                emoji_name = emoji_data.get("name", "")
            else:
                emoji_name = str(emoji_data)
            reactions.append(
                {
                    "emoji": emoji_name,
                    "count": reaction.get("count", 0),
                }
            )

        # Attachments
        attachments = []
        for att in attachments_raw:
            attachments.append(
                {
                    "name": att.get("fileName", att.get("filename", "unnamed")),
                    "type": att.get("contentType", att.get("content_type", "")),
                    "url": att.get("url", ""),
                }
            )

        # Embeds as additional content
        embed_texts: list[str] = []
        for embed in embeds:
            title = embed.get("title", "")
            desc = embed.get("description", "")
            if title or desc:
                embed_texts.append(f"[Embed: {title}] {desc}".strip())

        if embed_texts:
            content = content + "\n" + "\n".join(embed_texts) if content else "\n".join(embed_texts)

        # Thread / reply info
        reference = raw.get("reference", raw.get("messageReference"))
        thread_ts = None
        if isinstance(reference, dict):
            thread_ts = str(reference.get("messageId", ""))

        msg_id = str(raw.get("id", ""))

        return {
            "platform": "discord",
            "channel": channel,
            "user": user_name,
            "user_id": user_id,
            "text": content,
            "timestamp": timestamp,
            "ts": msg_id,
            "thread_ts": thread_ts,
            "is_thread_parent": False,  # Determined later in _identify_threads
            "reply_count": 0,
            "reactions": reactions,
            "attachments": attachments,
            "subtype": "",
        }

    # ------------------------------------------------------------------
    # Content enrichment
    # ------------------------------------------------------------------

    def _extract_code_snippets(self, messages: list[dict]) -> list[dict]:
        """Extract fenced code blocks from all messages.

        Detects triple-backtick fenced code blocks (````` ```lang ... ``` `````)
        and inline code that spans multiple lines.

        Args:
            messages: List of normalized message dicts.

        Returns:
            List of code snippet dicts with 'code', 'language',
            'quality_score', 'channel', 'user', and 'timestamp'.
        """
        snippets: list[dict] = []
        code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

        for msg in messages:
            text = msg.get("text", "")
            for match in code_block_pattern.finditer(text):
                lang = match.group(1) or ""
                code = match.group(2).strip()
                if code:
                    snippets.append(
                        {
                            "code": code,
                            "language": lang,
                            "quality_score": _score_code_quality(code),
                            "channel": msg.get("channel", ""),
                            "user": msg.get("user", ""),
                            "timestamp": msg.get("timestamp", ""),
                        }
                    )

        # Sort by quality descending
        snippets.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        return snippets

    def _extract_links(self, messages: list[dict]) -> list[dict]:
        """Extract shared URLs from all messages.

        Finds HTTP/HTTPS URLs in message text and deduplicates by URL.

        Args:
            messages: List of normalized message dicts.

        Returns:
            List of link dicts with 'url', 'channel', 'user', 'timestamp',
            and 'context' (surrounding text snippet).
        """
        links: list[dict] = []
        seen_urls: set[str] = set()
        url_pattern = re.compile(r"https?://[^\s<>\"')\]]+")

        for msg in messages:
            text = msg.get("text", "")
            for match in url_pattern.finditer(text):
                url = match.group(0).rstrip(".,;:!?)")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Extract context: up to 80 chars around the URL
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 40)
                context = text[start:end].strip()

                links.append(
                    {
                        "url": url,
                        "channel": msg.get("channel", ""),
                        "user": msg.get("user", ""),
                        "timestamp": msg.get("timestamp", ""),
                        "context": context,
                    }
                )

        return links

    def _identify_threads(self, messages: list[dict]) -> list[dict]:
        """Group messages into conversation threads.

        Threads are identified by shared ``thread_ts`` values (Slack)
        or ``thread_ts`` references (Discord). Each thread contains the
        parent message and its replies in chronological order.

        Args:
            messages: List of normalized message dicts.

        Returns:
            List of thread dicts with 'parent', 'replies', 'channel',
            'reply_count', and 'participants'.
        """
        # Group by thread_ts
        thread_map: dict[str, list[dict]] = defaultdict(list)
        msg_by_ts: dict[str, dict] = {}

        for msg in messages:
            ts = msg.get("ts", "")
            if ts:
                msg_by_ts[ts] = msg

            thread_ts = msg.get("thread_ts")
            if thread_ts:
                thread_map[thread_ts].append(msg)

        threads: list[dict] = []
        for thread_ts, thread_msgs in thread_map.items():
            if len(thread_msgs) < 2:
                continue

            # Sort by timestamp
            thread_msgs.sort(key=lambda m: m.get("timestamp", ""))

            parent = msg_by_ts.get(thread_ts, thread_msgs[0])
            replies = [m for m in thread_msgs if m.get("ts") != thread_ts]
            participants = list({m.get("user", "unknown") for m in thread_msgs})

            threads.append(
                {
                    "parent": parent,
                    "replies": replies,
                    "channel": parent.get("channel", ""),
                    "reply_count": len(replies),
                    "participants": participants,
                }
            )

        return threads

    def _summarize_channels(self, messages: list[dict]) -> dict[str, dict]:
        """Generate summary statistics for each channel.

        Args:
            messages: List of normalized message dicts.

        Returns:
            Dict mapping channel names to summary dicts with message_count,
            unique_users, date_range, top_users, and has_code.
        """
        channel_data: dict[str, list[dict]] = defaultdict(list)
        for msg in messages:
            channel_data[msg.get("channel", "unknown")].append(msg)

        summaries: dict[str, dict] = {}
        for channel, ch_messages in channel_data.items():
            users = [m.get("user", "unknown") for m in ch_messages]
            user_counts: dict[str, int] = defaultdict(int)
            for u in users:
                user_counts[u] += 1

            top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            timestamps = [m.get("timestamp", "") for m in ch_messages if m.get("timestamp")]

            has_code = any("```" in m.get("text", "") for m in ch_messages)

            summaries[channel] = {
                "message_count": len(ch_messages),
                "unique_users": len(set(users)),
                "date_range": {
                    "earliest": min(timestamps) if timestamps else "",
                    "latest": max(timestamps) if timestamps else "",
                },
                "top_users": [{"user": u, "count": c} for u, c in top_users],
                "has_code": has_code,
            }

        return summaries

    # Alias for single-channel usage in _build_sections
    _summarize_channel = _summarize_channels

    # ------------------------------------------------------------------
    # Section building
    # ------------------------------------------------------------------

    def _build_sections(self, messages: list[dict], threads: list[dict]) -> list[dict]:
        """Build sections from messages, grouping by channel and date.

        Each section represents a chunk of conversation from a single
        channel on a single date. Sections are compatible with the
        pipeline's intermediate JSON 'pages' format.

        Args:
            messages: List of normalized message dicts.
            threads: List of thread dicts (for enrichment).

        Returns:
            List of section dicts with heading, text, code_samples, etc.
        """
        # Group by (channel, date)
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for msg in messages:
            channel = msg.get("channel", "general")
            ts = msg.get("timestamp", "")
            try:
                date_str = ts[:10] if ts else "unknown"
            except (TypeError, IndexError):
                date_str = "unknown"
            groups[(channel, date_str)].append(msg)

        sections: list[dict] = []

        for section_number, ((channel, date_str), group_msgs) in enumerate(
            sorted(groups.items()), 1
        ):
            # Sort messages chronologically
            group_msgs.sort(key=lambda m: m.get("timestamp", ""))

            # Build text from messages
            text_parts: list[str] = []
            code_samples: list[dict] = []

            for msg in group_msgs:
                user = msg.get("user", "unknown")
                text = msg.get("text", "")
                ts_display = msg.get("timestamp", "")[:19]

                # Format message
                msg_line = f"**{user}** ({ts_display}): {text}"
                text_parts.append(msg_line)

                # Add reactions
                reactions = msg.get("reactions", [])
                if reactions:
                    reaction_str = " ".join(f":{r['emoji']}: ({r['count']})" for r in reactions)
                    text_parts.append(f"  Reactions: {reaction_str}")

                # Extract inline code blocks
                code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
                for match in code_block_pattern.finditer(text):
                    lang = match.group(1) or ""
                    code = match.group(2).strip()
                    if code:
                        code_samples.append(
                            {
                                "code": code,
                                "language": lang,
                                "quality_score": _score_code_quality(code),
                            }
                        )

            sections.append(
                {
                    "section_number": section_number,
                    "heading": f"#{channel} - {date_str}",
                    "heading_level": "h2",
                    "text": "\n\n".join(text_parts),
                    "headings": [],
                    "code_samples": code_samples,
                    "tables": [],
                    "images": [],
                    "channel": channel,
                    "date": date_str,
                    "message_count": len(group_msgs),
                }
            )

        return sections

    # ------------------------------------------------------------------
    # Output generation (private)
    # ------------------------------------------------------------------

    def _generate_reference_file(
        self,
        _cat_key: str,
        cat_data: dict,
        section_num: int,
        total_sections: int,
    ) -> None:
        """Generate a reference markdown file for a category.

        Args:
            _cat_key: Category key (unused, for interface consistency).
            cat_data: Category dict with 'title' and 'pages'.
            section_num: 1-based index among all categories.
            total_sections: Total number of categories being generated.
        """
        sections = cat_data["pages"]

        if sections:
            section_nums = [s.get("section_number", i + 1) for i, s in enumerate(sections)]
            if total_sections == 1:
                filename = f"{self.skill_dir}/references/main.md"
            else:
                sec_range = f"s{min(section_nums)}-s{max(section_nums)}"
                filename = f"{self.skill_dir}/references/{_cat_key}_{sec_range}.md"
        else:
            filename = f"{self.skill_dir}/references/section_{section_num:02d}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {cat_data['title']}\n\n")

            for section in sections:
                sec_num = section.get("section_number", "?")
                heading = section.get("heading", "")
                msg_count = section.get("message_count", 0)

                f.write(f"---\n\n**📄 Section {sec_num}**")
                f.write(f" ({msg_count} messages)\n\n")

                if heading:
                    f.write(f"## {heading}\n\n")

                # Message text
                text = section.get("text", "").strip()
                if text:
                    f.write(f"{text}\n\n")

                # Code samples
                code_list = section.get("code_samples", [])
                if code_list:
                    f.write("### Code Snippets\n\n")
                    for code in code_list:
                        lang = code.get("language", "")
                        f.write(f"```{lang}\n{code['code']}\n```\n\n")

                f.write("---\n\n")

        print(f"   Generated: {filename}")

    def _generate_index(self, categorized: dict[str, dict]) -> None:
        """Generate reference index file listing all categories.

        Args:
            categorized: Dict mapping category keys to category dicts.
        """
        filename = f"{self.skill_dir}/references/index.md"
        total_cats = len(categorized)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {self.name.title()} Chat Reference\n\n")
            f.write("## Categories\n\n")

            for section_num, (_ck, cd) in enumerate(categorized.items(), 1):
                pages = cd["pages"]
                count = len(pages)
                total_msgs = sum(p.get("message_count", 0) for p in pages)

                if pages:
                    snums = [s.get("section_number", i + 1) for i, s in enumerate(pages)]
                    rng = f"Sections {min(snums)}-{max(snums)}"
                    link = "main.md" if total_cats == 1 else f"{_ck}_s{min(snums)}-s{max(snums)}.md"
                else:
                    link = f"section_{section_num:02d}.md"
                    rng = "N/A"

                f.write(
                    f"- [{cd['title']}]({link}) ({count} sections, {total_msgs} messages, {rng})\n"
                )

            # Statistics
            f.write("\n## Statistics\n\n")
            meta = self.extracted_data.get("metadata", {})
            f.write(f"- Platform: {self.extracted_data.get('platform', 'unknown')}\n")
            f.write(f"- Total messages: {meta.get('total_messages', 0)}\n")
            f.write(f"- Total threads: {meta.get('total_threads', 0)}\n")
            f.write(f"- Code snippets: {meta.get('total_code_snippets', 0)}\n")
            f.write(f"- Shared links: {meta.get('total_links', 0)}\n")
            f.write(f"- Unique users: {meta.get('unique_users', 0)}\n")
            f.write(f"- Channels: {len(meta.get('channels', []))}\n")

            # Channel summaries
            channel_summaries = self.extracted_data.get("channel_summaries", {})
            if channel_summaries:
                f.write("\n## Channel Summary\n\n")
                for ch_name, summary in sorted(channel_summaries.items()):
                    f.write(f"### #{ch_name}\n\n")
                    f.write(f"- Messages: {summary.get('message_count', 0)}\n")
                    f.write(f"- Users: {summary.get('unique_users', 0)}\n")
                    dr = summary.get("date_range", {})
                    if dr.get("earliest") and dr.get("latest"):
                        f.write(f"- Date range: {dr['earliest'][:10]} to {dr['latest'][:10]}\n")
                    if summary.get("has_code"):
                        f.write("- Contains code snippets\n")
                    top_users = summary.get("top_users", [])
                    if top_users:
                        top_str = ", ".join(f"{u['user']} ({u['count']})" for u in top_users[:3])
                        f.write(f"- Top contributors: {top_str}\n")
                    f.write("\n")

        print(f"   Generated: {filename}")

    def _generate_skill_md(self, categorized: dict[str, dict]) -> None:
        """Generate main SKILL.md file with YAML frontmatter and overview.

        Args:
            categorized: Dict mapping category keys to category dicts.
        """
        filename = f"{self.skill_dir}/SKILL.md"
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]
        desc = self.description[:1024]
        meta = self.extracted_data.get("metadata", {})

        with open(filename, "w", encoding="utf-8") as f:
            # YAML frontmatter
            f.write("---\n")
            f.write(f"name: {skill_name}\n")
            f.write(f"description: {desc}\n")
            f.write("---\n\n")

            platform_label = self.platform.title()
            f.write(f"# {self.name.title()} {platform_label} Chat Skill\n\n")
            f.write(f"{self.description}\n\n")

            # Chat metadata
            f.write(f"## 📋 {platform_label} Chat Information\n\n")
            f.write(f"**Platform:** {platform_label}\n\n")
            f.write(f"**Source:** {self.extracted_data.get('source', 'N/A')}\n\n")
            f.write(f"**Total Messages:** {meta.get('total_messages', 0)}\n\n")
            f.write(f"**Unique Users:** {meta.get('unique_users', 0)}\n\n")
            channels = meta.get("channels", [])
            if channels:
                f.write(f"**Channels:** {', '.join(f'#{c}' for c in channels)}\n\n")

            # When to Use
            f.write("## 💡 When to Use This Skill\n\n")
            f.write("Use this skill when you need to:\n")
            f.write(f"- Find solutions discussed in {self.name} chat history\n")
            f.write("- Reference code snippets shared by team members\n")
            f.write("- Understand team decisions and architectural discussions\n")
            f.write("- Look up troubleshooting steps from past conversations\n")
            f.write("- Find shared links and resources from the team\n\n")

            # Section overview
            total_sections = self.extracted_data.get("total_sections", 0)
            f.write(f"## 📖 Content Overview\n\n")
            f.write(f"**Total Sections:** {total_sections}\n\n")
            f.write("**Content Breakdown:**\n\n")
            for cd in categorized.values():
                f.write(f"- **{cd['title']}**: {len(cd['pages'])} sections\n")
            f.write("\n")

            # Key topics
            f.write(self._format_key_topics())

            # Top code examples
            code_snippets = self.extracted_data.get("code_snippets", [])
            if code_snippets:
                f.write("## 📝 Top Code Snippets\n\n")
                f.write("*High-quality code shared in chat*\n\n")

                by_lang: dict[str, list] = {}
                for cs in code_snippets[:15]:
                    lang = cs.get("language", "unknown") or "unknown"
                    by_lang.setdefault(lang, []).append(cs)

                for lang in sorted(by_lang.keys()):
                    examples = by_lang[lang]
                    f.write(f"### {lang.title()} ({len(examples)} snippets)\n\n")
                    for i, cs in enumerate(examples[:3], 1):
                        quality = cs.get("quality_score", 0)
                        user = cs.get("user", "")
                        code_text = cs.get("code", "")
                        f.write(f"**Snippet {i}**")
                        if user:
                            f.write(f" (by {user})")
                        f.write(f" (Quality: {quality:.1f}/10):\n\n")
                        f.write(f"```{lang}\n")
                        if len(code_text) <= 500:
                            f.write(code_text)
                        else:
                            f.write(code_text[:500] + "\n...")
                        f.write("\n```\n\n")

            # Shared links
            links = self.extracted_data.get("links", [])
            if links:
                f.write(f"## 🔗 Shared Links ({len(links)})\n\n")
                f.write("*Key resources shared in chat*\n\n")
                for link in links[:20]:
                    url = link.get("url", "")
                    user = link.get("user", "")
                    channel = link.get("channel", "")
                    f.write(f"- {url}")
                    if user or channel:
                        parts = []
                        if user:
                            parts.append(f"by {user}")
                        if channel:
                            parts.append(f"in #{channel}")
                        f.write(f" ({', '.join(parts)})")
                    f.write("\n")
                if len(links) > 20:
                    f.write(f"\n*... and {len(links) - 20} more links*\n")
                f.write("\n")

            # Statistics
            f.write(f"## 📊 Chat Statistics\n\n")
            f.write(f"- **Total Messages**: {meta.get('total_messages', 0)}\n")
            f.write(f"- **Total Threads**: {meta.get('total_threads', 0)}\n")
            f.write(f"- **Code Snippets**: {meta.get('total_code_snippets', 0)}\n")
            f.write(f"- **Shared Links**: {meta.get('total_links', 0)}\n")
            f.write(f"- **Unique Users**: {meta.get('unique_users', 0)}\n")
            f.write(f"- **Channels**: {len(meta.get('channels', []))}\n\n")

            # Channel breakdown
            channel_summaries = self.extracted_data.get("channel_summaries", {})
            if channel_summaries:
                f.write("**Channel Activity:**\n\n")
                for ch_name, summary in sorted(
                    channel_summaries.items(),
                    key=lambda x: x[1].get("message_count", 0),
                    reverse=True,
                ):
                    msg_count = summary.get("message_count", 0)
                    user_count = summary.get("unique_users", 0)
                    f.write(f"- #{ch_name}: {msg_count} messages, {user_count} users\n")
                f.write("\n")

            # Navigation
            f.write("## 🗺️ Navigation\n\n")
            f.write("**Reference Files:**\n\n")
            for cd in categorized.values():
                cat_file = self._sanitize_filename(cd["title"])
                f.write(f"- `references/{cat_file}.md` - {cd['title']}\n")
            f.write("\nSee `references/index.md` for complete chat structure.\n\n")

            # Footer
            f.write("---\n\n")
            f.write(f"**Generated by Skill Seeker** | {platform_label} Chat Scraper\n")

        with open(filename, encoding="utf-8") as f:
            line_count = len(f.read().split("\n"))
        print(f"   Generated: {filename} ({line_count} lines)")

    # ------------------------------------------------------------------
    # Content analysis helpers
    # ------------------------------------------------------------------

    def _format_key_topics(self) -> str:
        """Extract key discussion topics from section headings and content.

        Returns:
            Markdown string with key topics section.
        """
        sections = self.extracted_data.get("pages", [])
        if not sections:
            return ""

        # Count topic matches across all sections
        topic_counts: dict[str, int] = defaultdict(int)
        for section in sections:
            combined = self._section_text(section)
            for topic, keywords in _TOPIC_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw.lower() in combined)
                if score >= 2:
                    topic_counts[topic] += 1

        if not topic_counts:
            return ""

        content = "## 🔑 Key Discussion Topics\n\n"
        content += "*Topics frequently discussed in chat*\n\n"

        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            label = topic.replace("_", " ").title()
            content += f"- **{label}**: {count} conversations\n"
        content += "\n"

        return content

    def _section_text(self, section: dict) -> str:
        """Combine section text, heading, and code into a lowercase string.

        Args:
            section: Section dict.

        Returns:
            Combined lowercase text for keyword matching.
        """
        text = section.get("text", "").lower()
        heading = section.get("heading", "").lower()
        code = " ".join(cs.get("code", "").lower() for cs in section.get("code_samples", []))
        return f"{text} {heading} {code}"

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a filesystem-safe filename.

        Args:
            name: Input string to sanitize.

        Returns:
            Safe lowercase filename with underscores.
        """
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        return re.sub(r"[-\s]+", "_", safe)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for the Slack/Discord chat scraper.

    Parses command-line arguments and runs the extraction and
    skill-building pipeline. Supports export import, API fetch,
    and loading from previously extracted JSON.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    from .arguments.chat import add_chat_arguments

    parser = argparse.ArgumentParser(
        description="Convert Slack/Discord chat history to AI-ready skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Slack workspace export
    %(prog)s --export-path ./slack-export/ --platform slack --name myteam

    # Slack API
    %(prog)s --platform slack --token xoxb-... --channel C01234 --name myteam

    # Discord export (DiscordChatExporter)
    %(prog)s --export-path ./discord-export.json --platform discord --name myserver

    # Discord API
    %(prog)s --platform discord --token Bot-token --channel 12345 --name myserver

    # From previously extracted JSON
    %(prog)s --from-json myteam_extracted.json --name myteam
        """,
    )

    add_chat_arguments(parser)

    args = parser.parse_args()

    # Set logging level
    if getattr(args, "quiet", False):
        logging.getLogger().setLevel(logging.WARNING)
    elif getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --dry-run
    if args.dry_run:
        source = args.export_path or args.from_json or f"{args.platform}-api"
        print(f"\n{'=' * 60}")
        print("DRY RUN: Chat Extraction")
        print(f"{'=' * 60}")
        print(f"Platform:       {args.platform}")
        print(f"Source:         {source}")
        print(f"Name:           {args.name or '(auto-detect)'}")
        print(f"Channel:        {args.channel or '(all)'}")
        print(f"Max messages:   {args.max_messages}")
        print(f"Enhance level:  {args.enhance_level}")
        print(f"\n✅ Dry run complete")
        return 0

    # Validate inputs
    if args.from_json:
        # Build from previously extracted JSON
        name = args.name or Path(args.from_json).stem.replace("_extracted", "")
        config = {
            "name": name,
            "description": (args.description or f"Use when referencing {name} chat knowledge base"),
        }
        try:
            converter = ChatToSkillConverter(config)
            converter.load_extracted_data(args.from_json)
            converter.build_skill()
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return 0

    # Require either --export-path or --token for extraction
    if not args.export_path and not args.token:
        parser.error(
            "Must specify --export-path (export mode), --token (API mode), "
            "or --from-json (build from extracted data)"
        )

    if not args.name:
        if args.export_path:
            args.name = Path(args.export_path).stem
        else:
            args.name = f"{args.platform}_chat"

    config = {
        "name": args.name,
        "export_path": args.export_path or "",
        "platform": args.platform,
        "token": args.token or "",
        "channel": args.channel or "",
        "max_messages": args.max_messages,
        "description": args.description,
    }

    try:
        converter = ChatToSkillConverter(config)

        # Extract
        if not converter.extract_chat():
            print(
                "\n❌ Chat extraction failed - see error above",
                file=sys.stderr,
            )
            sys.exit(1)

        # Build skill
        converter.build_skill()

        # Enhancement Workflow Integration
        from skill_seekers.cli.workflow_runner import run_workflows

        workflow_executed, workflow_names = run_workflows(args)
        workflow_name = ", ".join(workflow_names) if workflow_names else None

        # Traditional enhancement (complements workflow system)
        if getattr(args, "enhance_level", 0) > 0:
            api_key = getattr(args, "api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
            mode = "API" if api_key else "LOCAL"

            print("\n" + "=" * 80)
            print(f"🤖 Traditional AI Enhancement ({mode} mode, level {args.enhance_level})")
            print("=" * 80)
            if workflow_executed:
                print(f"   Running after workflow: {workflow_name}")
                print(
                    "   (Workflow provides specialized analysis, "
                    "enhancement provides general improvements)"
                )
            print("")

            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                    print("✅ API enhancement complete!")
                except ImportError:
                    print("❌ API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import (
                        LocalSkillEnhancer,
                    )

                    enhancer = LocalSkillEnhancer(Path(skill_dir))
                    enhancer.run(headless=True)
                    print("✅ Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import (
                    LocalSkillEnhancer,
                )

                enhancer = LocalSkillEnhancer(Path(skill_dir))
                enhancer.run(headless=True)
                print("✅ Local enhancement complete!")

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Input error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(
            f"\n❌ Unexpected error during chat processing: {e}",
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
