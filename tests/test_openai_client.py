"""The real OpenAIClassifier against a fake HTTP server (no network, no cost)."""
import httpx2  # HTTP library used inside the OpenAI SDK
import pytest

from labeler.errors import ApiKeyError
from labeler.labeling_engine import run_query
from labeler.models import Note
from labeler.openai_client import OpenAIClassifier

_FAST_RETRY = {"retry-after-ms": "10"}   # tell the SDK to retry almost at once


def _completion(content: str) -> dict:
    def token(text, logprob=-0.01, top=None):
        return {"token": text, "logprob": logprob, "bytes": None, "top_logprobs": top or []}

    answer_top = [token("1", -0.05), token("0", -3.0)]
    return {
        "id": "test", "object": "chat.completion", "created": 0, "model": "gpt-4o-mini",
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": content, "refusal": None},
            "logprobs": {"content": [token("1"), token("|"), token("1", -0.05, answer_top)]},
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
    }


def _classifier(responses: list[httpx2.Response]) -> tuple[OpenAIClassifier, list]:
    calls = []

    def handler(request):
        calls.append(request)
        return responses[min(len(calls), len(responses)) - 1]

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    return OpenAIClassifier("test-key", http_client=client), calls


def _run(classifier, tmp_path):
    return run_query(["a car hit me"], "hit by a vehicle", classifier=classifier, cache_path=tmp_path / "c.db")


def test_rate_limit_is_retried_then_labelled(tmp_path):
    classifier, calls = _classifier([
        httpx2.Response(429, headers=_FAST_RETRY, json={"error": {"message": "rate limit"}}),
        httpx2.Response(200, json=_completion("1|1")),
    ])
    result = _run(classifier, tmp_path)
    assert len(calls) == 2
    assert result.labels[0].label == 1 and result.labels[0].confidence == 0.95


def test_rate_limit_forever_marks_row_failed(tmp_path):
    classifier, calls = _classifier([
        httpx2.Response(429, headers=_FAST_RETRY, json={"error": {"message": "rate limit"}}),
    ])
    result = _run(classifier, tmp_path)
    assert result.labels[0].label is None and result.labels[0].note == Note.FAILED
    assert len(calls) == 4                      # 1 try + 3 retries (config.MAX_RETRIES)


def test_rejected_key_stops_run(tmp_path):
    classifier, _ = _classifier([httpx2.Response(401, json={"error": {"message": "bad key sk-123"}})])
    with pytest.raises(ApiKeyError) as err:
        _run(classifier, tmp_path)
    assert "sk-123" not in str(err.value)       # the key is never echoed
