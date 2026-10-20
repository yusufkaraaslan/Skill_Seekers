"""MiniMax defaults and overrides through the real SDK HTTP serialization boundary."""

import json
from contextlib import ExitStack
from functools import partial
from importlib import import_module

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.agent_client import AgentClient
from skill_seekers.cli.minimax_config import MINIMAX_MODEL_IDS


@pytest.fixture
def requests_sent(monkeypatch):
    """Intercept HTTP only: use real SDK constructors, routing and serialization."""
    pytest.importorskip("openai")
    pytest.importorskip("anthropic")
    for name in (
        "SKILL_SEEKER_MODEL",
        "MINIMAX_MODEL",
        "MINIMAX_THINKING",
        "MINIMAX_API_REGION",
        "MINIMAX_API_PROTOCOL",
        "SKILL_SEEKER_PROVIDER",
    ):
        monkeypatch.delenv(name, raising=False)
    captured = []

    def handle(request, http_module):
        body = json.loads(request.read())
        captured.append((request.url, body))
        if request.url.path.endswith("/messages"):
            payload = {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": body["model"],
                "content": [
                    {"type": "thinking", "thinking": "Reasoning", "signature": "test-signature"},
                    {"type": "text", "text": "Enhanced instructions"},
                ],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        else:
            payload = {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "Enhanced instructions",
                            "reasoning_content": "Reasoning",
                        },
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
        return http_module.Response(200, json=payload)

    import anthropic
    import openai

    # New Anthropic SDKs use httpx2; the frozen SDK uses httpx. Derive the
    # transport from the SDK's public default client, never its network default.
    with ExitStack() as stack:
        for sdk, constructor in ((anthropic, "Anthropic"), (openai, "OpenAI")):
            http_module = import_module(
                next(
                    cls.__module__.split(".")[0]
                    for cls in sdk.DefaultHttpxClient.__mro__
                    if cls.__module__.split(".")[0] in {"httpx", "httpx2"}
                )
            )
            http_client = stack.enter_context(
                sdk.DefaultHttpxClient(
                    transport=http_module.MockTransport(partial(handle, http_module=http_module))
                )
            )
            monkeypatch.setattr(
                sdk, constructor, partial(getattr(sdk, constructor), http_client=http_client)
            )
        yield captured


def assert_route(url, region, protocol):
    assert url.host == ("api.minimax.io" if region == "global_en" else "api.minimaxi.com")
    assert url.path == (
        "/v1/chat/completions" if protocol == "openai" else "/anthropic/v1/messages"
    )


def assert_default_options(body):
    # Omission preserves the model's API default (Flash adaptive/max).
    assert "thinking" not in body
    assert "reasoning_effort" not in body
    assert "output_config" not in body
    assert "service_tier" not in body
    assert "reasoning_split" not in body


def test_ordinary_text_catalog():
    assert MINIMAX_MODEL_IDS == ("MiniMax-M3.1-Flash", "MiniMax-M3")


@pytest.mark.parametrize("region", ["global_en", "cn_zh"])
@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
@pytest.mark.parametrize("source", ["default", "explicit", "provider_env", "global_env"])
def test_agent_text_request(requests_sent, monkeypatch, region, protocol, source):
    monkeypatch.setenv("MINIMAX_API_REGION", region)
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    model = None
    expected = "MiniMax-M3.1-Flash"
    if source == "explicit":
        model = expected = "custom-model"
    elif source == "provider_env":
        expected = "MiniMax-M2.7"
        monkeypatch.setenv("MINIMAX_MODEL", expected)
    elif source == "global_env":
        expected = "MiniMax-M3"
        monkeypatch.setenv("SKILL_SEEKER_MODEL", expected)
        monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M2.7")
    client = AgentClient(mode="api", provider="minimax", api_key="unit-test-key", model=model)
    assert client.call("Explain this", system="Be concise") == "Enhanced instructions"
    url, body = requests_sent.pop()
    assert_route(url, region, protocol)
    assert body["model"] == expected
    assert_default_options(body)
    assert body["messages"][-1] == {"role": "user", "content": "Explain this"}
    assert (
        body["system"] if protocol == "anthropic" else body["messages"][0]["content"]
    ) == "Be concise"


@pytest.mark.parametrize("region", ["global_en", "cn_zh"])
@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
@pytest.mark.parametrize("model", [None, "MiniMax-M3", "MiniMax-M2.7", "custom-model"])
def test_adaptor_enhancement(requests_sent, monkeypatch, tmp_path, region, protocol, model):
    monkeypatch.setenv("MINIMAX_API_REGION", region)
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    monkeypatch.setenv("MINIMAX_THINKING", "adaptive")
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "guide.md").write_text("# Reference\nUse the API.")
    (tmp_path / "SKILL.md").write_text("Original instructions")
    adaptor = get_adaptor("minimax", {"custom_model": model} if model else {})
    assert adaptor.enhance(tmp_path, "unit-test-key") is True
    assert (tmp_path / "SKILL.md").read_text() == "Enhanced instructions"
    url, body = requests_sent.pop()
    assert_route(url, region, protocol)
    assert body["model"] == (model or "MiniMax-M3.1-Flash")
    assert body["thinking"] == {"type": "adaptive"}
    assert "Reference" in body["messages"][-1]["content"]


@pytest.mark.parametrize("region", ["global_en", "cn_zh"])
@pytest.mark.parametrize("model", [None, "MiniMax-M2.7", "custom-model"])
def test_package_upload_preserves_saved_model(requests_sent, monkeypatch, tmp_path, region, model):
    monkeypatch.setenv("MINIMAX_API_REGION", region)
    (tmp_path / "SKILL.md").write_text("Saved instructions")
    adaptor = get_adaptor("minimax", {"custom_model": model} if model else {})
    package = adaptor.package(tmp_path, tmp_path / "skill.zip")
    # A fresh adaptor must keep the model recorded in the existing package.
    assert get_adaptor("minimax").upload(package, "unit-test-key")["success"] is True
    url, body = requests_sent.pop()
    assert_route(url, region, "openai")
    assert body["model"] == (model or "MiniMax-M3.1-Flash")
    assert_default_options(body)


@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
@pytest.mark.parametrize("model", [None, "minimax-m3.1-flash"])
def test_flash_disabled_rejected_before_http(requests_sent, monkeypatch, protocol, model):
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    client = AgentClient(mode="api", provider="minimax", api_key="unit-test-key", model=model)
    with pytest.raises(ValueError, match="only supports thinking mode.*adaptive"):
        client.call("Explain this", thinking="disabled")
    assert requests_sent == []


@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
@pytest.mark.parametrize("thinking", ["adaptive", "disabled"])
def test_m3_thinking_modes(requests_sent, monkeypatch, protocol, thinking):
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    client = AgentClient(
        mode="api", provider="minimax", api_key="unit-test-key", model="MiniMax-M3"
    )
    assert client.call("Explain this", thinking=thinking) == "Enhanced instructions"
    assert requests_sent.pop()[1]["thinking"] == {"type": thinking}


@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
@pytest.mark.parametrize("model", [None, "MiniMax-M3.1-Flash", "custom-image-model"])
def test_images_keep_media_default_and_overrides(
    requests_sent, monkeypatch, tmp_path, protocol, model
):
    monkeypatch.setenv("MINIMAX_API_PROTOCOL", protocol)
    image = tmp_path / "frame.png"
    image.write_bytes(b"image")
    client = AgentClient(mode="api", provider="minimax", api_key="unit-test-key", model=model)
    assert client.call_with_image("Read image", image) == "Enhanced instructions"
    _, body = requests_sent.pop()
    assert body["model"] == (model or "MiniMax-M3")
    content = body["messages"][-1]["content"]
    if protocol == "openai":
        assert content == [
            {"type": "text", "text": "Read image"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,aW1hZ2U="}},
        ]
    else:
        assert content == [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": "aW1hZ2U="},
            },
            {"type": "text", "text": "Read image"},
        ]


def test_video_keeps_m3_default(requests_sent, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    client = AgentClient(mode="api", provider="minimax", api_key="unit-test-key")
    assert (
        client.call_with_video("Read clip", video, thinking="disabled") == "Enhanced instructions"
    )
    _, body = requests_sent.pop()
    assert body["model"] == "MiniMax-M3"
    assert body["messages"][-1]["content"][1] == {
        "type": "video_url",
        "video_url": {"url": "data:video/mp4;base64,dmlkZW8="},
    }
    # A media call must not mutate subsequent text defaults.
    assert client.call("Explain this") == "Enhanced instructions"
    assert requests_sent.pop()[1]["model"] == "MiniMax-M3.1-Flash"


def test_explicit_base_url_is_preserved(requests_sent):
    client = AgentClient(
        mode="api",
        provider="minimax",
        api_key="unit-test-key",
        base_url="https://custom.example/v1",
        model="saved-model",
    )
    assert client.call("Explain this") == "Enhanced instructions"
    url, body = requests_sent.pop()
    assert str(url) == "https://custom.example/v1/chat/completions"
    assert body["model"] == "saved-model"


def test_other_provider_request_is_unchanged(requests_sent, monkeypatch):
    monkeypatch.setenv("MINIMAX_THINKING", "disabled")
    client = AgentClient(mode="api", provider="openai", api_key="unit-test-key")
    assert client.call("Explain this") == "Enhanced instructions"
    url, body = requests_sent.pop()
    assert str(url) == "https://api.openai.com/v1/chat/completions"
    assert body["model"] == "gpt-4o"
    assert_default_options(body)
