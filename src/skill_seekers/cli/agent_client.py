"""
Unified AI Client for Skill Seekers

Centralizes all AI invocations (API and LOCAL mode) so that every enhancer
uses a single abstraction instead of hardcoding subprocess calls or model names.

Supports:
- API mode: Anthropic, Moonshot/Kimi, Google Gemini, OpenAI (via adaptor pattern)
- LOCAL mode: Claude Code, Kimi Code, Codex, Copilot, OpenCode, custom agents

Usage:
    from skill_seekers.cli.agent_client import AgentClient

    client = AgentClient(mode="auto")
    response = client.call("Analyze this code and return JSON")

    # Or with explicit agent
    client = AgentClient(mode="local", agent="kimi")
    response = client.call(prompt, timeout=300)

    # Static helpers
    key, provider = AgentClient.detect_api_key()
    model = AgentClient.get_model()
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Agent presets for LOCAL mode — reused from enhance_skill_local.py pattern
AGENT_PRESETS = {
    "claude": {
        "display_name": "Claude Code",
        "command": ["claude", "--dangerously-skip-permissions", "{prompt_file}"],
        "version_check": ["claude", "--version"],
    },
    "codex": {
        "display_name": "OpenAI Codex CLI",
        "command": ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-"],
        "version_check": ["codex", "--version"],
        "uses_stdin": True,
    },
    "copilot": {
        "display_name": "GitHub Copilot CLI",
        "command": ["gh", "copilot", "chat", "-"],
        "version_check": ["gh", "copilot", "--version"],
        "uses_stdin": True,
    },
    "opencode": {
        "display_name": "OpenCode CLI",
        "command": ["opencode"],
        "version_check": ["opencode", "--version"],
    },
    "kimi": {
        "display_name": "Kimi Code CLI",
        "command": [
            "kimi",
            "--print",
            "--input-format",
            "text",
            "--work-dir",
            "{cwd}",
        ],
        "version_check": ["kimi", "--version"],
        "uses_stdin": True,
        "parse_output": "kimi",  # Needs special output parsing
    },
}

# Default models per API provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "moonshot": "moonshot-v1-auto",
    "google": "gemini-2.0-flash",
    "openai": "gpt-4o",
}

# API key env var → provider mapping
API_KEY_MAP = {
    "ANTHROPIC_API_KEY": "anthropic",
    "ANTHROPIC_AUTH_TOKEN": "anthropic",
    "MOONSHOT_API_KEY": "moonshot",
    "GOOGLE_API_KEY": "google",
    "OPENAI_API_KEY": "openai",
}

DEFAULT_ENHANCE_TIMEOUT = 2700  # 45 minutes
UNLIMITED_TIMEOUT = 86400  # 24 hours (subprocess requires a finite number)


def get_default_timeout() -> int:
    """Return default enhancement timeout in seconds.

    Priority:
    1. SKILL_SEEKER_ENHANCE_TIMEOUT environment variable
    2. DEFAULT_ENHANCE_TIMEOUT (45 minutes)

    Supports 'unlimited' or 0/negative values which map to UNLIMITED_TIMEOUT (24h).
    """
    env_val = os.environ.get("SKILL_SEEKER_ENHANCE_TIMEOUT", "").strip().lower()
    if env_val in ("unlimited", "none", "0"):
        return UNLIMITED_TIMEOUT
    try:
        timeout = int(env_val)
        if timeout <= 0:
            return UNLIMITED_TIMEOUT
        return timeout
    except ValueError:
        return DEFAULT_ENHANCE_TIMEOUT

# Provider → target platform mapping (for --target defaults)
PROVIDER_TARGET_MAP = {
    "anthropic": "claude",
    "moonshot": "kimi",
    "google": "gemini",
    "openai": "openai",
}


def normalize_agent_name(agent_name: str) -> str:
    """Normalize agent name to canonical form."""
    if not agent_name:
        return "claude"
    normalized = agent_name.strip().lower()
    aliases = {
        "claude-code": "claude",
        "claude_code": "claude",
        "codex-cli": "codex",
        "copilot-cli": "copilot",
        "open-code": "opencode",
        "open_code": "opencode",
        "kimi-cli": "kimi",
        "kimi_code": "kimi",
        "kimi-code": "kimi",
    }
    return aliases.get(normalized, normalized)


class AgentClient:
    """
    Unified AI client that routes to API or LOCAL agent based on configuration.

    All enhancers should use this instead of direct subprocess calls or API imports.
    """

    def __init__(
        self,
        mode: str = "auto",
        agent: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the agent client.

        Args:
            mode: "auto" (detect from env), "api" (force API), "local" (force CLI agent)
            agent: LOCAL mode agent name ("claude", "kimi", "codex", "copilot", "opencode", "custom")
                   Resolved from: arg → env SKILL_SEEKER_AGENT → "claude"
            api_key: API key override. If None, auto-detected from env vars.
        """
        # Resolve agent name
        env_agent = os.environ.get("SKILL_SEEKER_AGENT", "").strip()
        self.agent = normalize_agent_name(agent or env_agent or "claude")
        self.agent_display = AGENT_PRESETS.get(self.agent, {}).get("display_name", self.agent)

        # Detect API key and provider
        if api_key:
            self.api_key = api_key
            # Detect provider from key prefix or env vars
            self.provider = self._detect_provider_from_key(api_key)
        else:
            self.api_key, self.provider = self.detect_api_key()

        # Determine mode
        self.mode = mode
        if mode == "auto":
            if self.api_key:
                self.mode = "api"
            else:
                self.mode = "local"

        # Initialize API client if needed
        self.client = None
        if self.mode == "api" and self.api_key:
            self.client = self._init_api_client()

    @staticmethod
    def _detect_provider_from_key(api_key: str) -> str:
        """Detect provider from API key prefix or fall back to env var check."""
        if api_key.startswith("sk-ant-"):
            return "anthropic"
        if api_key.startswith("sk-"):
            # Could be OpenAI or Moonshot — check env vars
            if os.environ.get("MOONSHOT_API_KEY", "").strip() == api_key:
                return "moonshot"
            return "openai"
        if api_key.startswith("AIza"):
            return "google"
        # Default: check which env var matches
        for env_var, provider in API_KEY_MAP.items():
            if os.environ.get(env_var, "").strip() == api_key:
                return provider
        return "anthropic"  # Safe fallback

    def _init_api_client(self):
        """Initialize the API client based on detected provider."""
        try:
            if self.provider == "anthropic":
                import anthropic

                kwargs = {"api_key": self.api_key}
                base_url = os.environ.get("ANTHROPIC_BASE_URL")
                if base_url:
                    kwargs["base_url"] = base_url
                return anthropic.Anthropic(**kwargs)
            elif self.provider == "moonshot":
                import anthropic

                return anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url="https://api.moonshot.cn/v1",
                )
            elif self.provider == "openai":
                from openai import OpenAI

                return OpenAI(api_key=self.api_key)
            elif self.provider == "google":
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                return genai
        except ImportError as e:
            logger.warning(f"⚠️  {self.provider} SDK not installed: {e}")
            self.mode = "local"
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize {self.provider} API client: {e}")
            self.mode = "local"
        return None

    def call(
        self,
        prompt: str,
        max_tokens: int = 4096,
        timeout: int | None = None,
        output_file: str | Path | None = None,
        cwd: str | Path | None = None,
    ) -> str | None:
        """
        Call the AI agent (API or LOCAL mode).

        Args:
            prompt: The prompt to send
            max_tokens: Max response tokens (API mode only)
            timeout: Timeout in seconds (default from SKILL_SEEKER_ENHANCE_TIMEOUT or 2700 = 45m)
            output_file: Path for agent to write output (LOCAL mode, some agents)
            cwd: Working directory for LOCAL mode subprocess

        Returns:
            Response text, or None on failure
        """
        if timeout is None:
            timeout = get_default_timeout()

        if self.mode == "api":
            return self._call_api(prompt, max_tokens)
        elif self.mode == "local":
            return self._call_local(prompt, timeout, output_file, cwd)
        return None

    def _call_api(self, prompt: str, max_tokens: int = 4096) -> str | None:
        """Call via API using the detected provider."""
        if not self.client:
            return None

        model = self.get_model(self.provider)

        try:
            if self.provider in ("anthropic", "moonshot"):
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=120,
                )
                return response.content[0].text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=120,
                )
                return response.choices[0].message.content

            elif self.provider == "google":
                gmodel = self.client.GenerativeModel(model)
                response = gmodel.generate_content(prompt)
                return response.text

        except Exception as e:
            logger.warning(f"⚠️  {self.provider} API call failed: {e}")
            return None

    def _call_local(
        self,
        prompt: str,
        timeout: int = 300,
        output_file: str | Path | None = None,
        cwd: str | Path | None = None,
    ) -> str | None:
        """Call via LOCAL CLI agent using agent presets."""
        # Handle custom agent from env var
        if self.agent == "custom":
            custom_cmd = os.environ.get("SKILL_SEEKER_AGENT_CMD", "").strip()
            if not custom_cmd:
                logger.warning("⚠️  Custom agent selected but SKILL_SEEKER_AGENT_CMD not set")
                return None
            preset = {
                "display_name": "Custom Agent",
                "command": custom_cmd.split(),
                "version_check": custom_cmd.split()[:1] + ["--version"],
            }
        else:
            preset = AGENT_PRESETS.get(self.agent)
            if not preset:
                logger.warning(f"⚠️  Unknown agent: {self.agent}")
                return None

        try:
            with tempfile.TemporaryDirectory(prefix="agent_client_") as temp_dir:
                temp_path = Path(temp_dir)
                prompt_file = temp_path / "prompt.md"
                resp_file = Path(output_file) if output_file else (temp_path / "response.json")

                # Only append output file instruction when caller explicitly requests it
                full_prompt = prompt
                if output_file:
                    full_prompt += f"\n\nWrite your response to: {resp_file}\n"

                prompt_file.write_text(full_prompt)

                # Build command from preset
                cmd = []
                for part in preset["command"]:
                    part = part.replace("{prompt_file}", str(prompt_file))
                    part = part.replace("{cwd}", str(cwd or temp_path))
                    part = part.replace("{skill_dir}", str(cwd or temp_path))
                    cmd.append(part)

                # Execute — pipe stdin for agents that read from it (e.g., codex)
                stdin_input = full_prompt if preset.get("uses_stdin") else None
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(cwd or temp_path),
                    input=stdin_input,
                )

                if result.returncode != 0:
                    logger.warning(f"⚠️  {self.agent_display} returned error: {result.returncode}")

                # Try to read output file first
                resp_path = Path(resp_file)
                if resp_path.exists():
                    return resp_path.read_text(encoding="utf-8")

                # Try any JSON file in temp dir
                for json_file in temp_path.glob("*.json"):
                    if json_file.name != "prompt.json":
                        return json_file.read_text(encoding="utf-8")

                # Fall back to stdout (with agent-specific parsing)
                if result.stdout and result.stdout.strip():
                    stdout = result.stdout.strip()
                    parser = preset.get("parse_output")
                    if parser == "kimi":
                        stdout = self._parse_kimi_output(stdout)
                    return stdout

                logger.warning(f"⚠️  No output from {self.agent_display}")
                return None

        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️  {self.agent_display} timeout ({timeout}s)")
            return None
        except FileNotFoundError:
            logger.warning(
                f"⚠️  {self.agent_display} CLI not found. "
                f"Install it or set SKILL_SEEKER_AGENT to a different agent."
            )
            return None
        except Exception as e:
            logger.warning(f"⚠️  {self.agent_display} error: {e}")
            return None

    @staticmethod
    def _parse_kimi_output(raw_output: str) -> str:
        """Parse Kimi CLI --print mode output to extract text content.

        Kimi's --print mode outputs structured lines like:
            TurnBegin(...)
            StepBegin(...)
            TextPart(type='text', text='actual content')
            ThinkPart(type='think', think='...')

        This extracts the text= values from TextPart lines.
        """
        import re

        text_parts = re.findall(r"TextPart\(type='text', text='(.+?)'\)", raw_output)
        if text_parts:
            return "\n".join(text_parts)
        # Fallback: return raw if no TextPart found
        return raw_output

    def is_available(self) -> bool:
        """Check if the configured agent/API is available."""
        if self.mode == "api":
            return self.client is not None

        # LOCAL mode: check if CLI exists
        preset = AGENT_PRESETS.get(self.agent)
        if not preset:
            return False

        version_cmd = preset.get("version_check")
        if not version_cmd:
            return shutil.which(preset["command"][0]) is not None

        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def detect_api_key() -> tuple[str | None, str | None]:
        """
        Detect API key from environment variables.

        Returns:
            (api_key, provider) tuple. Provider is "anthropic", "moonshot", "google", or "openai".
            Returns (None, None) if no key found.
        """
        for env_var, provider in API_KEY_MAP.items():
            key = os.environ.get(env_var, "").strip()
            if key:
                return key, provider
        return None, None

    @staticmethod
    def get_model(provider: str = "anthropic") -> str:
        """
        Get the model name for a provider.

        Checks SKILL_SEEKER_MODEL env var first, then provider-specific env vars,
        then falls back to defaults.
        """
        # Global override
        global_model = os.environ.get("SKILL_SEEKER_MODEL", "").strip()
        if global_model:
            return global_model

        # Provider-specific env vars
        provider_env_map = {
            "anthropic": "ANTHROPIC_MODEL",
            "moonshot": "MOONSHOT_MODEL",
            "google": "GOOGLE_MODEL",
            "openai": "OPENAI_MODEL",
        }
        env_var = provider_env_map.get(provider)
        if env_var:
            model = os.environ.get(env_var, "").strip()
            if model:
                return model

        return DEFAULT_MODELS.get(provider, "claude-sonnet-4-20250514")

    @staticmethod
    def detect_default_target() -> str:
        """
        Auto-detect the default --target platform from available API keys.

        Returns platform name: "claude", "kimi", "gemini", "openai", or "markdown" (fallback).
        """
        _, provider = AgentClient.detect_api_key()
        if provider:
            return PROVIDER_TARGET_MAP.get(provider, "markdown")
        return "markdown"

    def log_mode(self) -> None:
        """Log the current mode and agent for UX."""
        if self.mode == "api":
            logger.info(f"✅ AI enhancement enabled (using {self.provider} API)")
        elif self.mode == "local":
            logger.info(f"✅ AI enhancement enabled (using LOCAL mode - {self.agent_display})")
        else:
            logger.info("ℹ️  AI enhancement disabled")
