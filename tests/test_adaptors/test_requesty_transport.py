"""Requesty CLI regression tests through the real SDK with offline HTTP transport."""

import json
import sys

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.enhance_command import main as enhance_main

openai = pytest.importorskip("openai")
httpx = pytest.importorskip("httpx")


@pytest.fixture
def skill_dir(tmp_path):
    """Create a skill whose instructions and references can be distinguished."""
    skill = tmp_path / "requesty-test"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Original instructions", encoding="utf-8")
    (skill / "references" / "guide.md").write_text(
        "# Reference sentinel\nExample documentation.", encoding="utf-8"
    )
    return skill


@pytest.fixture
def requesty_http(monkeypatch):
    """Inject a mock HTTP client so no SDK request can reach a live provider."""
    requests = []
    response = {"content": "# Enhanced instructions", "finish_reason": "stop"}

    def handle(request):
        body = json.loads(request.content)
        requests.append((request, body))
        return httpx.Response(
            200,
            json={
                "id": "requesty-offline-test",
                "object": "chat.completion",
                "created": 1,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response["content"]},
                        "finish_reason": response["finish_reason"],
                    }
                ],
            },
        )

    real_openai = openai.OpenAI
    with httpx.Client(transport=httpx.MockTransport(handle)) as http_client:

        def make_client(**kwargs):
            return real_openai(**kwargs, http_client=http_client)

        monkeypatch.setattr(openai, "OpenAI", make_client)
        monkeypatch.setenv("REQUESTY_API_KEY", "requesty-offline-test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "unrelated-openai-test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://unrelated.invalid/v1")
        yield requests, response


@pytest.mark.parametrize("model", [None, "anthropic/claude-sonnet-4-5"])
def test_enhance_cli_uses_requesty_key_endpoint_and_model(
    skill_dir, requesty_http, monkeypatch, model
):
    """Exercise target parsing, env-key lookup, SDK serialization and atomic save."""
    requests, _ = requesty_http
    argv = ["enhance", str(skill_dir), "--target", "requesty"]
    if model:
        argv.extend(["--model", model])
    monkeypatch.setattr(sys, "argv", argv)

    assert enhance_main() == 0

    assert len(requests) == 1
    request, body = requests[0]
    assert str(request.url) == "https://router.requesty.ai/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer requesty-offline-test-key"
    assert body["model"] == (model or "openai/gpt-4o-mini")
    assert "Reference sentinel" in json.dumps(body["messages"])
    assert "Original instructions" in json.dumps(body["messages"])
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "# Enhanced instructions"
    assert (skill_dir / "SKILL.md.backup").read_text(encoding="utf-8") == (
        "# Original instructions"
    )
    assert not (skill_dir / "SKILL.md.tmp").exists()


@pytest.mark.parametrize("content,finish_reason", [("# Partial", "length"), ("", "stop")])
def test_enhance_preserves_original_on_unusable_response(
    skill_dir, requesty_http, content, finish_reason
):
    """Empty or truncated provider output must not overwrite existing knowledge."""
    requests, response = requesty_http
    response.update(content=content, finish_reason=finish_reason)

    assert not get_adaptor("requesty").enhance(skill_dir, "requesty-offline-test-key")

    assert requests
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "# Original instructions"
    assert not (skill_dir / "SKILL.md.backup").exists()


def test_package_is_local_and_upload_only_validates_instructions(
    skill_dir, requesty_http, tmp_path
):
    """Validation makes a chat call, without persisting a skill or reference files."""
    requests, _ = requesty_http
    adaptor = get_adaptor("requesty")
    package = adaptor.package(skill_dir, tmp_path / "packages")
    assert package.exists()
    assert not requests

    result = adaptor.upload(package, "requesty-offline-test-key")

    assert result["success"]
    assert result["skill_id"] is None
    assert len(requests) == 1
    request, body = requests[0]
    assert str(request.url) == "https://router.requesty.ai/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer requesty-offline-test-key"
    assert body["model"] == "openai/gpt-4o-mini"
    assert "Original instructions" in json.dumps(body["messages"])
    assert "Reference sentinel" not in json.dumps(body["messages"])
