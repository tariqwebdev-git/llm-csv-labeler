"""The real AnthropicClassifier against a fake HTTP server (no network, no cost)."""
import json

import httpx2  # HTTP library used inside the Anthropic SDK
import pytest

from labeler.anthropic_client import AnthropicClassifier
from labeler.errors import ApiConfigError, ApiKeyError
from labeler.labeling_engine import estimate_cost, run_query
from labeler.models import Note, Provider
from tests.fake_classifier import FakeClassifier

_FAST_RETRY = {"retry-after-ms": "10"}   # tell the SDK to retry almost at once


def _message(text: str, stop_reason: str = "end_turn", cache_read: int = 0) -> dict:
    return {
        "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "text", "text": text}] if text else [],
        "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 3, "cache_read_input_tokens": cache_read,
                  "cache_creation_input_tokens": 0},
    }


def _error(status: int, kind: str) -> httpx2.Response:
    return httpx2.Response(status, json={"type": "error", "error": {"type": kind, "message": "test"}},
                           headers=_FAST_RETRY)


def _classifier(responses: list[httpx2.Response]) -> tuple[AnthropicClassifier, list]:
    calls = []

    def handler(request):
        calls.append(request)
        return responses[min(len(calls), len(responses)) - 1]

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    return AnthropicClassifier("test-key", http_client=client), calls


def _run(classifier, tmp_path, texts=("a car hit me",)):
    return run_query(list(texts), "hit by a vehicle", classifier=classifier, provider=Provider.ANTHROPIC,
                     cache_path=tmp_path / "c.db")


def test_labels_come_back_without_confidence(tmp_path):
    classifier, calls = _classifier([httpx2.Response(200, json=_message("1|1"))])
    result = _run(classifier, tmp_path)
    assert result.labels[0].label == 1 and result.labels[0].confidence is None
    body = json.loads(calls[0].content)
    assert body["model"] == "claude-haiku-5-5"
    assert "temperature" not in body                      # this model rejects sampling settings
    assert body["thinking"] == {"type": "disabled"}
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_rate_limit_is_retried_then_labelled(tmp_path):
    classifier, calls = _classifier([_error(429, "rate_limit_error"), httpx2.Response(200, json=_message("1|0"))])
    result = _run(classifier, tmp_path)
    assert result.labels[0].label == 0 and len(calls) == 2


def test_rejected_key_stops_run(tmp_path):
    classifier, _ = _classifier([_error(401, "authentication_error")])
    with pytest.raises(ApiKeyError) as exc:
        _run(classifier, tmp_path)
    assert "test-key" not in str(exc.value)


def test_unknown_model_stops_run(tmp_path):
    classifier, _ = _classifier([_error(404, "not_found_error")])
    with pytest.raises(ApiConfigError):
        _run(classifier, tmp_path)


def test_refusal_leaves_row_blank_with_note(tmp_path):
    classifier, _ = _classifier([httpx2.Response(200, json=_message("", stop_reason="refusal"))])
    result = _run(classifier, tmp_path)
    assert result.labels[0].label is None and result.labels[0].note == Note.REFUSED


def test_cost_uses_claude_prices_and_cache_reads(tmp_path):
    classifier, _ = _classifier([httpx2.Response(200, json=_message("1|1", cache_read=100))])
    usage = _run(classifier, tmp_path).stats.usage
    assert usage.input_tokens == 110 and usage.cached_input_tokens == 100


def test_missing_key_raises_before_any_call():
    with pytest.raises(ApiKeyError):
        AnthropicClassifier(None)


def test_each_provider_keeps_its_own_cache(tmp_path):
    cache = tmp_path / "c.db"
    texts = ["a car hit me", "the bus was late"]
    run_query(texts, "hit by a vehicle", classifier=FakeClassifier(), cache_path=cache)          # OpenAI
    assert estimate_cost(texts, "hit by a vehicle", cache_path=cache).rows_cached == 2
    assert estimate_cost(texts, "hit by a vehicle", provider=Provider.ANTHROPIC, cache_path=cache).rows_cached == 0
