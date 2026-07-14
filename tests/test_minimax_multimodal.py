"""Tests for MiniMax multimodal provider configuration and image requests."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest

from skill_seekers.cli.agent_client import AgentClient
from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.minimax_config import (
    MINIMAX_DEFAULT_MODEL,
    MINIMAX_ENDPOINTS,
    resolve_minimax_endpoint,
)
from skill_seekers.cli.video_models import FrameType
from skill_seekers.cli.video_visual import _ocr_with_minimax_vision, _ocr_with_vision


def _mock_minimax_client(monkeypatch, protocol: str) -> AgentClient:
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    monkeypatch.setattr(AgentClient, "_init_api_client", lambda _self: MagicMock())
    return AgentClient(mode="api", api_key="unit-test-key", provider="minimax")


def test_minimax_endpoint_matrix_matches_public_regions():
    assert get_adaptor("minimax").SUPPORTED_MODELS == ("MiniMax-M3", "MiniMax-M2.7")
    assert resolve_minimax_endpoint("global_en", "openai") == "https://api.minimax.io/v1"
    assert resolve_minimax_endpoint("cn_zh", "openai") == "https://api.minimaxi.com/v1"
    assert resolve_minimax_endpoint("global_en", "anthropic") == "https://api.minimax.io/anthropic"
    assert resolve_minimax_endpoint("cn_zh", "anthropic") == "https://api.minimaxi.com/anthropic"
    assert all(
        endpoints["anthropic"].endswith("/anthropic") for endpoints in MINIMAX_ENDPOINTS.values()
    )


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("MINIMAX_API_REGION", "unknown"),
        ("MINIMAX_API_PROTOCOL", "unknown"),
    ],
)
def test_invalid_minimax_endpoint_configuration_fails(monkeypatch, variable, value):
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValueError):
        resolve_minimax_endpoint()


def test_agent_client_detects_minimax_key_and_model(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "unit-test-key")
    monkeypatch.delenv("SKILL_SEEKER_MODEL", raising=False)
    assert AgentClient.detect_api_key() == ("unit-test-key", "minimax")
    assert AgentClient.get_model("minimax") == MINIMAX_DEFAULT_MODEL
    assert AgentClient.detect_default_target() == "minimax"


def test_openai_protocol_sends_image_data_url(monkeypatch, tmp_path):
    client = _mock_minimax_client(monkeypatch, "openai")
    response = client.client.chat.completions.create.return_value
    response.choices = [
        type(
            "Choice",
            (),
            {"finish_reason": "stop", "message": type("Message", (), {"content": "code"})()},
        )()
    ]
    image_path = tmp_path / "frame.png"
    image_path.write_bytes(b"png-data")

    assert client.call_with_image("Extract text", image_path) == "code"

    messages = client.client.chat.completions.create.call_args.kwargs["messages"]
    content = messages[-1]["content"]
    assert content[0] == {"type": "text", "text": "Extract text"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_anthropic_protocol_sends_base64_image_block(monkeypatch, tmp_path):
    client = _mock_minimax_client(monkeypatch, "anthropic")
    response = client.client.messages.create.return_value
    response.stop_reason = "end_turn"
    response.content = [type("TextBlock", (), {"text": "code"})()]
    image_path = tmp_path / "frame.webp"
    image_path.write_bytes(b"webp-data")

    assert client.call_with_image("Extract text", image_path) == "code"

    content = client.client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert content[0]["type"] == "image"
    assert content[0]["source"]["media_type"] == "image/webp"
    assert content[1] == {"type": "text", "text": "Extract text"}


def test_vision_dispatch_uses_minimax_when_selected(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.call_with_image.return_value = "print('ok')"
    constructor = MagicMock(return_value=fake_client)
    monkeypatch.setattr("skill_seekers.cli.video_visual.AgentClient", constructor)
    monkeypatch.setenv("SKILL_SEEKER_VISION_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "unit-test-key")
    image_path = tmp_path / "frame.png"
    image_path.write_bytes(b"png-data")

    text, confidence = _ocr_with_vision(str(image_path), FrameType.CODE_EDITOR)

    assert text == "print('ok')"
    assert confidence == 0.95
    assert constructor.call_args.kwargs["provider"] == "minimax"
    assert constructor.call_args.kwargs["model"] == MINIMAX_DEFAULT_MODEL


def test_minimax_vision_without_key_returns_empty(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    assert _ocr_with_minimax_vision("missing.png", FrameType.CODE_EDITOR) == ("", 0.0)


def test_anthropic_compatible_base_appends_messages_path(monkeypatch):
    pytest.importorskip("anthropic")
    captured_paths: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            captured_paths.append(self.path)
            content_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(content_length)
            body = json.dumps(
                {
                    "id": "message-test",
                    "type": "message",
                    "role": "assistant",
                    "model": MINIMAX_DEFAULT_MODEL,
                    "content": [{"type": "text", "text": "ok"}],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("MINIMAX_API_PROTOCOL", "anthropic")
        base_url = f"http://127.0.0.1:{server.server_port}/anthropic"
        client = AgentClient(
            mode="api",
            api_key="unit-test-key",
            provider="minimax",
            base_url=base_url,
            model=MINIMAX_DEFAULT_MODEL,
        )
        assert client.call("Reply with ok", timeout=5) == "ok"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert captured_paths == ["/anthropic/v1/messages"]
