"""
Unified AI Client for Skill Seekers

Centralizes all AI invocations (API and LOCAL mode) so that every enhancer
uses a single abstraction instead of hardcoding subprocess calls or model names.

Supports:
- API mode: Anthropic, Moonshot/Kimi, Google Gemini, OpenAI, MiniMax
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

import base64
import logging
import mimetypes
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from skill_seekers.cli.minimax_config import (
    MINIMAX_DEFAULT_MODEL,
    MINIMAX_DEFAULT_PROTOCOL,
    MINIMAX_ENDPOINTS,
)

logger = logging.getLogger(__name__)

# Agent presets for LOCAL mode — THE single source of truth, also consumed by
# enhance_skill_local.LocalSkillEnhancer (it previously carried its own copy,
# whose kimi preset silently diverged). Placeholders: {prompt_file} is the
# prompt path; {cwd} / {skill_dir} are both replaced with the working
# directory by each consumer. "supports_skip_permissions" agents get
# --dangerously-skip-permissions inserted for headless runs (interactive
# callers may omit it).
AGENT_PRESETS = {
    "claude": {
        "display_name": "Claude Code",
        "command": ["claude", "{prompt_file}"],
        "version_check": ["claude", "--version"],
        "supports_skip_permissions": True,
    },
    "codex": {
        "display_name": "OpenAI Codex CLI",
        "command": ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-"],
        "version_check": ["codex", "--version"],
        "uses_stdin": True,
        "supports_skip_permissions": False,
    },
    "copilot": {
        "display_name": "GitHub Copilot CLI",
        "command": ["gh", "copilot", "chat", "-"],
        "version_check": ["gh", "copilot", "--version"],
        "uses_stdin": True,
        "supports_skip_permissions": False,
    },
    "opencode": {
        "display_name": "OpenCode CLI",
        "command": ["opencode"],
        "version_check": ["opencode", "--version"],
        "supports_skip_permissions": False,
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
        "supports_skip_permissions": False,
    },
}

# Default models per API provider
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "moonshot": "moonshot-v1-auto",
    "google": "gemini-2.0-flash",
    "openai": "gpt-4o",
    "minimax": MINIMAX_DEFAULT_MODEL,
}

# Ordered provider registry — THE single home for which API providers exist,
# which env vars hold their keys, and their auto-detection priority. Consumed
# by enhance_command (mode picking) and enhance_skill_local (target detection);
# a provider forgotten at a call site was exactly the ENH-12 bug. Add new
# providers HERE (plus an _init_api_client branch), not at call sites.
# "target" is the platform name the enhance CLI / adaptors use.
# "protocol" is the wire format (see WIRE_PROTOCOLS) — _call_api branches on it,
#   NOT on provider name, so an OpenAI/Anthropic-compatible provider needs no new
#   _call_api branch. Providers may declare "protocol_env" for a runtime override.
# "supports_images" gates multimodal (call_with_image); "endpoints"/"region_env"
#   describe a region→protocol→URL map for providers with regional base URLs.
WIRE_PROTOCOLS = ("anthropic", "openai", "google")
API_PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "provider": "anthropic",
        "target": "claude",
        "env_vars": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
        "protocol": "anthropic",
        "supports_images": True,
    },
    {
        "provider": "google",
        "target": "gemini",
        "env_vars": ("GOOGLE_API_KEY",),
        "protocol": "google",
        "supports_images": True,
    },
    {
        "provider": "openai",
        "target": "openai",
        "env_vars": ("OPENAI_API_KEY",),
        "protocol": "openai",
        "supports_images": True,
    },
    {
        "provider": "moonshot",
        "target": "kimi",
        "env_vars": ("MOONSHOT_API_KEY",),
        "protocol": "anthropic",
        "supports_images": False,
    },
    {
        "provider": "minimax",
        "target": "minimax",
        "env_vars": ("MINIMAX_API_KEY",),
        "protocol": MINIMAX_DEFAULT_PROTOCOL,
        "protocol_env": "MINIMAX_API_PROTOCOL",
        "endpoints": MINIMAX_ENDPOINTS,
        "region_env": "MINIMAX_API_REGION",
        "supports_images": True,
    },
)

# provider name → its registry entry (single lookup, avoids re-scanning the tuple)
PROVIDER_META = {p["provider"]: p for p in API_PROVIDERS}

# Registry invariant: every provider must declare a known wire protocol, else
# _call_api would silently return None for it (no matching branch).
assert all(p.get("protocol") in WIRE_PROTOCOLS for p in API_PROVIDERS), (
    "every API_PROVIDERS entry must declare a protocol in WIRE_PROTOCOLS"
)

# API key env var → provider mapping (derived from the registry)
API_KEY_MAP = {var: p["provider"] for p in API_PROVIDERS for var in p["env_vars"]}


def provider_supports_images(provider: str) -> bool:
    """Whether a provider accepts image input (registry-declared capability)."""
    return bool(PROVIDER_META.get(provider, {}).get("supports_images"))


def get_provider_api_keys() -> dict[str, str | None]:
    """Map target name → API key from env, in registry order."""
    return {
        p["target"]: next(
            (os.environ.get(var) for var in p["env_vars"] if os.environ.get(var)), None
        )
        for p in API_PROVIDERS
    }


def detect_api_target() -> tuple[str, str] | None:
    """First provider (in registry priority order) with a key set → (target, key)."""
    for p in API_PROVIDERS:
        for var in p["env_vars"]:
            key = os.environ.get(var)
            if key:
                return p["target"], key
    return None


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
    "minimax": "minimax",
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


def build_local_agent_command(
    agent: str,
    prompt_file: str | Path,
    workdir: str | Path,
    *,
    include_permissions_flag: bool = True,
    agent_cmd: str | None = None,
) -> tuple[list[str], bool]:
    """Build the subprocess argv for a LOCAL agent run.

    Single home for preset-template handling: placeholder substitution
    ({prompt_file}, {cwd}, {skill_dir} — the latter two are synonyms for the
    working directory) and the conditional --dangerously-skip-permissions
    insert. Used by AgentClient._call_local and LocalSkillEnhancer, which
    previously each hand-rolled this and drifted.

    Args:
        agent: Preset name (must exist in AGENT_PRESETS) — ignored when
            ``agent_cmd`` is given.
        prompt_file: Path substituted for {prompt_file}.
        workdir: Path substituted for {cwd}/{skill_dir}.
        include_permissions_flag: Insert --dangerously-skip-permissions for
            presets that support it (headless runs); interactive callers may
            pass False.
        agent_cmd: Custom command template overriding the preset.

    Returns:
        (cmd_parts, uses_prompt_file) — ``uses_prompt_file`` is True when the
        template consumed {prompt_file}; otherwise the prompt should be piped
        via stdin.
    """
    if agent_cmd:
        cmd_parts = shlex.split(agent_cmd)
        supports_skip = False
    else:
        preset = AGENT_PRESETS[agent]
        cmd_parts = list(preset["command"])
        supports_skip = preset.get("supports_skip_permissions", False)

    if (
        include_permissions_flag
        and supports_skip
        and "--dangerously-skip-permissions" not in cmd_parts
    ):
        cmd_parts.insert(1, "--dangerously-skip-permissions")

    uses_prompt_file = False
    out = []
    for arg in cmd_parts:
        if "{prompt_file}" in arg:
            arg = arg.replace("{prompt_file}", str(prompt_file))
            uses_prompt_file = True
        arg = arg.replace("{cwd}", str(workdir)).replace("{skill_dir}", str(workdir))
        out.append(arg)
    return out, uses_prompt_file


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
        provider: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the agent client.

        Args:
            mode: "auto" (detect from env), "api" (force API), "local" (force CLI agent)
            agent: LOCAL mode agent name ("claude", "kimi", "codex", "copilot", "opencode", "custom")
                   Resolved from: arg → env SKILL_SEEKER_AGENT → "claude"
            api_key: API key override. If None, auto-detected from env vars.
            provider: API provider override ("anthropic", "moonshot", "openai",
                "google", "minimax"). Skips key-prefix detection - required for
                OpenAI-compatible platforms whose keys don't follow OpenAI's
                prefix (MiniMax, DeepSeek, Together, ...).
            base_url: Custom API endpoint (anthropic- and openai-SDK providers).
                Overrides env-based endpoints.
            model: Model override; defaults to get_model(provider).
        """
        # Resolve agent name: param > ExecutionContext > env var > default
        try:
            from skill_seekers.cli.execution_context import ExecutionContext

            ctx = ExecutionContext.get()
            ctx_agent = ctx.enhancement.agent or ""
        except Exception:
            ctx_agent = ""
        env_agent = os.environ.get("SKILL_SEEKER_AGENT", "").strip()
        self.agent = normalize_agent_name(agent or ctx_agent or env_agent or "claude")
        self.agent_display = AGENT_PRESETS.get(self.agent, {}).get("display_name", self.agent)

        # Detect API key and provider (explicit provider override wins)
        self.base_url = base_url
        self.model = model
        if api_key:
            self.api_key = api_key
            self.provider = provider or self._detect_provider_from_key(api_key)
        else:
            self.api_key, detected = self.detect_api_key()
            self.provider = provider or detected
        self.api_protocol = self._resolve_api_protocol()

        # Determine mode (keep original for error handling decisions)
        self._requested_mode = mode
        self.mode = mode
        if mode == "auto":
            if self.api_key:
                self.mode = "api"
            else:
                self.mode = "local"

        # Set by _call_api when the truncation gate fires, so call() can
        # distinguish "truncated" from other failures and retry with a
        # bigger budget.
        self._last_truncated = False

        # Initialize API client if needed
        self.client = None
        if self.mode == "api" and self.api_key:
            self.client = self._init_api_client()

    @staticmethod
    def _detect_provider_from_key(api_key: str) -> str:
        """Detect provider from API key prefix or fall back to env var check."""
        # Explicit override wins. Moonshot/Kimi keys also start with "sk-", so a
        # directly-passed Moonshot key (without MOONSHOT_API_KEY also exported)
        # would otherwise be misclassified as OpenAI and hit the wrong endpoint.
        # Accepts provider or target names from API_PROVIDERS ("kimi" → "moonshot").
        forced = os.environ.get("SKILL_SEEKER_PROVIDER", "").strip().lower()
        for p in API_PROVIDERS:
            if forced in (p["provider"], p["target"]):
                return p["provider"]
        for env_var, provider in API_KEY_MAP.items():
            if os.environ.get(env_var, "").strip() == api_key:
                return provider
        if api_key.startswith("sk-ant-"):
            return "anthropic"
        if api_key.startswith("sk-"):
            # Ambiguous "sk-" prefix (OpenAI or Moonshot). A key that matches a
            # known env var was already resolved by the loop above, so default
            # to OpenAI here.
            return "openai"
        if api_key.startswith("AIza"):
            return "google"
        return "anthropic"  # Safe fallback

    def _resolve_api_protocol(self) -> str:
        """Resolve the wire protocol (see WIRE_PROTOCOLS) for the provider.

        Precedence: a base_url ending in ``/anthropic`` forces the Anthropic
        wire format; then a registry-declared ``protocol_env`` override (e.g.
        MINIMAX_API_PROTOCOL); then the provider's registry default.
        """
        meta = PROVIDER_META.get(self.provider, {})
        if self.base_url and self.base_url.rstrip("/").endswith("/anthropic"):
            return "anthropic"
        protocol_env = meta.get("protocol_env")
        if protocol_env:
            override = os.environ.get(protocol_env, "").strip().lower()
            if override:
                if override not in ("openai", "anthropic"):
                    raise ValueError(
                        f"Unsupported {protocol_env}={override!r}; choose one of: openai, anthropic"
                    )
                return override
        return meta.get("protocol", "openai")

    def _resolve_base_url(self) -> str | None:
        """Resolve the API base URL for the provider.

        Precedence: an explicit ``base_url`` override; then a registry-declared
        regional ``endpoints`` map keyed by ``region_env`` and the resolved
        protocol; then None (let the SDK use its own default).
        """
        if self.base_url:
            return self.base_url
        meta = PROVIDER_META.get(self.provider, {})
        endpoints = meta.get("endpoints")
        if not endpoints:
            return None
        region_env = meta.get("region_env")
        region = (os.environ.get(region_env, "").strip() if region_env else "") or next(
            iter(endpoints)
        )
        if region not in endpoints:
            choices = ", ".join(endpoints)
            raise ValueError(f"Unsupported region {region!r}; choose one of: {choices}")
        return endpoints[region][self.api_protocol]

    def _init_api_client(self):
        """Initialize the API client based on detected provider."""
        try:
            if self.provider == "anthropic":
                import anthropic

                kwargs = {"api_key": self.api_key}
                base_url = self.base_url or os.environ.get("ANTHROPIC_BASE_URL")
                if base_url:
                    kwargs["base_url"] = base_url
                return anthropic.Anthropic(**kwargs)
            elif self.provider == "moonshot":
                import anthropic

                return anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.base_url or "https://api.moonshot.cn/v1",
                )
            elif self.provider == "openai":
                from openai import OpenAI

                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                return OpenAI(**kwargs)
            elif self.provider == "minimax":
                base_url = self._resolve_base_url()
                if self.api_protocol == "anthropic":
                    import anthropic

                    return anthropic.Anthropic(api_key=self.api_key, base_url=base_url)

                from openai import OpenAI

                return OpenAI(api_key=self.api_key, base_url=base_url)
            elif self.provider == "google":
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                return genai
            else:
                # Unknown provider: don't silently fall through to `return None`
                # (mode would stay "api" and every _call_api returns None with no
                # LOCAL fallback). Raise so the except below routes it correctly.
                raise ValueError(f"Unknown API provider: {self.provider!r}")
        except ImportError as e:
            logger.info(f"{self.provider} SDK not installed, falling back to LOCAL mode: {e}")
            self.mode = "local"
        except Exception as e:
            if self._requested_mode == "api":
                raise RuntimeError(f"Failed to initialize {self.provider} API client: {e}") from e
            logger.error(f"Failed to initialize {self.provider} API client: {e}")
            self.mode = "local"
        return None

    def call_with_image(
        self,
        prompt: str,
        image_path: str | Path,
        max_tokens: int = 4096,
        timeout: int | None = None,
        system: str | None = None,
        temperature: float | None = None,
    ) -> str | None:
        """Call an API provider with a local image and text prompt.

        Args:
            prompt: Text instruction accompanying the image.
            image_path: Local image file to encode in the request.
            max_tokens: Maximum response tokens.
            timeout: Request timeout in seconds.
            system: Optional system prompt.
            temperature: Optional sampling temperature.

        Returns:
            Response text, or None when the image cannot be read or the call fails.
        """
        if self.mode != "api":
            logger.warning("Image requests require API mode")
            return None
        if not provider_supports_images(self.provider):
            logger.warning("Provider %r does not support image requests", self.provider)
            return None

        path = Path(image_path)
        try:
            image_data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        except OSError as e:
            logger.error(f"Could not read image {path}: {e}")
            return None

        media_type = mimetypes.guess_type(path.name)[0] or "image/png"
        result = self._call_api(
            prompt,
            max_tokens,
            timeout,
            system=system,
            temperature=temperature,
            image=(media_type, image_data),
        )
        if result is None and self._last_truncated:
            logger.warning(
                "Retrying image request once with doubled max_tokens=%s after truncation.",
                max_tokens * 2,
            )
            result = self._call_api(
                prompt,
                max_tokens * 2,
                timeout,
                system=system,
                temperature=temperature,
                image=(media_type, image_data),
            )
        return result

    def call(
        self,
        prompt: str,
        max_tokens: int = 4096,
        timeout: int | None = None,
        output_file: str | Path | None = None,
        cwd: str | Path | None = None,
        system: str | None = None,
        temperature: float | None = None,
    ) -> str | None:
        """
        Call the AI agent (API or LOCAL mode).

        Args:
            prompt: The prompt to send
            max_tokens: Max response tokens (API mode only)
            timeout: Timeout in seconds (default from SKILL_SEEKER_ENHANCE_TIMEOUT or 2700 = 45m)
            output_file: Path for agent to write output (LOCAL mode, some agents)
            cwd: Working directory for LOCAL mode subprocess
            system: Optional system prompt (API mode only)
            temperature: Optional sampling temperature (API mode only;
                None = provider default)

        Returns:
            Response text, or None on failure
        """
        # No defaulting here: _call_api and _call_local each resolve a None
        # timeout via get_default_timeout(), so defaulting in call() too left
        # two places to update when the policy changes.
        if self.mode == "api":
            result = self._call_api(
                prompt, max_tokens, timeout, system=system, temperature=temperature
            )
            # The truncation gate returns None rather than corrupt callers'
            # output with a cut-off body. Before giving up, retry ONCE with
            # double the budget — the response may simply not fit.
            if result is None and self._last_truncated:
                logger.warning(
                    "Retrying once with doubled max_tokens=%s after truncation.",
                    max_tokens * 2,
                )
                result = self._call_api(
                    prompt, max_tokens * 2, timeout, system=system, temperature=temperature
                )
            return result
        elif self.mode == "local":
            return self._call_local(prompt, timeout, output_file, cwd)
        return None

    def _call_api(
        self,
        prompt: str,
        max_tokens: int = 4096,
        timeout: int | None = None,
        system: str | None = None,
        temperature: float | None = None,
        image: tuple[str, str] | None = None,
    ) -> str | None:
        """Call via API using the detected provider."""
        self._last_truncated = False
        if not self.client:
            return None

        model = self.model or self.get_model(self.provider)
        # Honor the caller's timeout (default 45m / SKILL_SEEKER_ENHANCE_TIMEOUT)
        # instead of a hardcoded 120s that killed large enhancement prompts.
        request_timeout = timeout if timeout is not None else get_default_timeout()

        try:
            if self.api_protocol == "anthropic":
                kwargs: dict[str, Any] = {}
                if system is not None:
                    kwargs["system"] = system
                if temperature is not None:
                    kwargs["temperature"] = temperature
                anthropic_content: str | list[dict[str, Any]] = prompt
                if image:
                    media_type, image_data = image
                    anthropic_content = [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ]
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": anthropic_content}],
                    timeout=request_timeout,
                    **kwargs,
                )
                # Treat a max_tokens truncation as a failure: callers overwrite
                # SKILL.md / parse JSON with this text, so returning a truncated
                # body silently corrupts their output.
                if getattr(response, "stop_reason", None) == "max_tokens":
                    self._last_truncated = True
                    logger.warning(
                        "API response truncated at max_tokens=%s; returning None "
                        "to avoid using incomplete content.",
                        max_tokens,
                    )
                    return None
                # Newer SDKs may prepend ThinkingBlocks — return the first
                # block that carries text instead of assuming content[0].
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                logger.warning("No text content found in API response")
                return None

            elif self.api_protocol == "openai":
                messages: list[dict[str, Any]] = []
                if system is not None:
                    messages.append({"role": "system", "content": system})
                openai_content: str | list[dict[str, Any]] = prompt
                if image:
                    media_type, image_data = image
                    openai_content = [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                            },
                        },
                    ]
                messages.append({"role": "user", "content": openai_content})
                kwargs = {}
                if temperature is not None:
                    kwargs["temperature"] = temperature
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    timeout=request_timeout,
                    **kwargs,
                )
                if response.choices and response.choices[0].finish_reason == "length":
                    self._last_truncated = True
                    logger.warning(
                        "API response truncated at max_tokens=%s; returning None "
                        "to avoid using incomplete content.",
                        max_tokens,
                    )
                    return None
                return response.choices[0].message.content

            elif self.api_protocol == "google":
                gmodel_kwargs = {}
                if system is not None:
                    gmodel_kwargs["system_instruction"] = system
                gmodel = self.client.GenerativeModel(model, **gmodel_kwargs)
                generation_config = {"max_output_tokens": max_tokens}
                if temperature is not None:
                    generation_config["temperature"] = temperature
                # Gemini inline image parts want raw bytes, not the base64 string
                # the OpenAI/Anthropic JSON payloads carry, so decode here.
                content: str | list[Any] = prompt
                if image:
                    media_type, image_data = image
                    content = [
                        {"mime_type": media_type, "data": base64.b64decode(image_data)},
                        prompt,
                    ]
                # Honor max_tokens + timeout (were ignored → output capped at the
                # model default, request unbounded), and reject a truncated reply.
                response = gmodel.generate_content(
                    content,
                    generation_config=generation_config,
                    request_options={"timeout": request_timeout},
                )
                candidates = getattr(response, "candidates", None) or []
                # Gemini finish_reason 2 == MAX_TOKENS (truncated).
                if candidates and getattr(candidates[0], "finish_reason", None) == 2:
                    self._last_truncated = True
                    logger.warning(
                        "Gemini response truncated at max_tokens=%s; returning None.",
                        max_tokens,
                    )
                    return None
                return response.text

        except Exception as e:
            error_type = type(e).__name__
            error_module = type(e).__module__ or ""
            # Prefer the HTTP status code when the SDK exception carries one — the
            # name-substring checks below misfire (a 429 whose exception class
            # doesn't contain "rate" would otherwise get a generic message).
            status = getattr(e, "status_code", None) or getattr(
                getattr(e, "response", None), "status_code", None
            )

            # Rate limit errors
            if status == 429 or "rate" in error_type.lower() or "ratelimit" in error_type.lower():
                logger.error(
                    f"{self.provider} API rate limited: {e}. "
                    "Retry after waiting or reduce request frequency."
                )
                return None

            # Auth / permission errors
            if (
                status in (401, 403)
                or "auth" in error_type.lower()
                or "permission" in error_type.lower()
            ):
                logger.error(
                    f"{self.provider} API authentication failed: {e}. "
                    "Check your API key is valid and has sufficient permissions."
                )
                return None

            # Timeout / connection errors
            if (
                any(
                    kw in error_type.lower()
                    for kw in ("timeout", "connect", "connection", "network")
                )
                or "httpx" in error_module.lower()
            ):
                logger.error(
                    f"{self.provider} API connection error: {e}. "
                    "Check your network connectivity and try again."
                )
                return None

            # All other errors
            logger.error(f"{self.provider} API call failed: {e}")
            return None

        return None

    def _call_local(
        self,
        prompt: str,
        timeout: int | None = None,
        output_file: str | Path | None = None,
        cwd: str | Path | None = None,
    ) -> str | None:
        """Call via LOCAL CLI agent using agent presets."""
        # Recursion guard. A LOCAL agent (e.g. ``claude``) spawned for
        # enhancement may itself run the test suite, and a test that shells out
        # to ``skill-seekers create`` would spawn yet another enhance agent —
        # a fork-bomb of real LLM processes. We mark the child environment when
        # spawning an agent (see ``env`` below) and refuse to spawn a nested one
        # here, so an inner ``create`` keeps its base SKILL.md instead of
        # recursing.
        if os.environ.get("SKILL_SEEKER_ENHANCE_ACTIVE") == "1":
            logger.warning(
                "⚠️  Skipping LOCAL enhancement: already running inside a Skill "
                "Seekers enhance agent (SKILL_SEEKER_ENHANCE_ACTIVE=1); refusing "
                "to spawn a nested agent to avoid recursion."
            )
            return None
        if timeout is None:
            timeout = get_default_timeout()
        # Handle custom agent from env var
        custom_cmd = None
        if self.agent == "custom":
            custom_cmd = os.environ.get("SKILL_SEEKER_AGENT_CMD", "").strip()
            if not custom_cmd:
                logger.warning("⚠️  Custom agent selected but SKILL_SEEKER_AGENT_CMD not set")
                return None
            preset = {"display_name": "Custom Agent"}
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

                prompt_file.write_text(full_prompt, encoding="utf-8")

                # Build command via the shared builder (headless: always
                # skip permission prompts when the preset supports it). The
                # custom-agent template goes through the same path via
                # agent_cmd (shlex-split, same placeholder substitution).
                cmd, uses_prompt_file = build_local_agent_command(
                    self.agent, prompt_file, cwd or temp_path, agent_cmd=custom_cmd
                )

                # Execute — pipe stdin for agents that read from it (e.g.,
                # codex), and whenever the template never consumed
                # {prompt_file} (bare ["opencode"], custom commands without
                # the placeholder) so the prompt actually reaches the agent.
                stdin_input = (
                    full_prompt if (preset.get("uses_stdin") or not uses_prompt_file) else None
                )
                # Mark the child environment so a nested ``skill-seekers create``
                # (e.g. if this agent runs the test suite) won't spawn another
                # enhance agent — see the recursion guard at the top of this method.
                child_env = {**os.environ, "SKILL_SEEKER_ENHANCE_ACTIVE": "1"}
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(cwd or temp_path),
                    input=stdin_input,
                    env=child_env,
                )

                if result.returncode != 0:
                    logger.error(f"{self.agent_display} returned error code {result.returncode}")
                    if result.stderr and result.stderr.strip():
                        logger.error(f"{self.agent_display} stderr: {result.stderr.strip()}")

                # Only trust a written response file when the caller explicitly
                # requested one (output_file). Otherwise no agent was instructed
                # to write a file, and a stray *.json the agent happens to create
                # in its cwd would shadow the real stdout response.
                if output_file:
                    resp_path = Path(resp_file)
                    if resp_path.exists():
                        return resp_path.read_text(encoding="utf-8")

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
            logger.error(f"{self.agent_display} error: {e}")
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

        # Scanner instead of a single regex: a lazy capture truncated at the
        # first internal "')" before a CamelCase-looking line (print('done')
        # then Config(...)), and garbled trailing records when the lookahead
        # failed at the true boundary. For each opening, the closing is the
        # LAST "')" before the next record header — a CamelCase constructor
        # (two+ capitals, e.g. ThinkPart(, ToolCallPart() at line start; kimi's
        # record list isn't exhaustive, so any such constructor is a boundary.
        # Single-capital identifiers (Config(, Path() are common in code
        # samples inside the text and must NOT be treated as boundaries.
        opening = "TextPart(type='text', text='"
        header_re = re.compile(r"(?m)^[A-Z][A-Za-z_]*[A-Z][A-Za-z_]*\(")

        text_parts = []
        pos = 0
        while True:
            start = raw_output.find(opening, pos)
            if start == -1:
                break
            content_start = start + len(opening)
            header = header_re.search(raw_output, content_start)
            boundary = header.start() if header else len(raw_output)
            close = raw_output.rfind("')", content_start, boundary)
            if close == -1:
                # No closing before the boundary — malformed record; skip it.
                pos = content_start
                continue
            text_parts.append(raw_output[content_start:close])
            pos = close + 2
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
            (api_key, provider) tuple. Provider is "anthropic", "moonshot", "google",
            "openai", or "minimax".
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
            "minimax": "MINIMAX_MODEL",
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

        Returns platform name: "claude", "kimi", "gemini", "openai", "minimax",
        or "markdown" (fallback).
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
