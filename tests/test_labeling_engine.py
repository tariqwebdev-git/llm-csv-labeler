"""Engine + batch runner behaviour with a fake classifier (no API calls)."""
import pytest

from labeler.errors import ApiCallError, ApiKeyError
from labeler.labeling_engine import estimate_cost, pick_test_rows, run_query
from labeler.models import LLMReply, Note
from tests.fake_classifier import BLOCK, SKIP, FakeClassifier, contains_hit


@pytest.fixture
def cache_path(tmp_path):
    return tmp_path / "cache.db"


def _run(texts, fake, cache_path, query="hit by a vehicle"):
    return run_query(texts, query, classifier=fake, cache_path=cache_path)


def test_labels_every_row_with_confidence(cache_path):
    texts = [f"row {i} was hit" if i % 3 == 0 else f"row {i} bus late" for i in range(120)]
    result = _run(texts, FakeClassifier(), cache_path)
    assert [r.label for r in result.labels] == [1 if i % 3 == 0 else 0 for i in range(120)]
    assert all(r.confidence == 0.9 for r in result.labels)
    assert result.stats.matched == 40 and result.stats.not_labelled == 0


def test_skipped_row_is_retried_alone_then_labelled(cache_path):
    calls = {"n": 0}

    def skip_first_time(text):
        if text == "b hit":
            calls["n"] += 1
            return SKIP if calls["n"] == 1 else "1"
        return contains_hit(text)

    fake = FakeClassifier(skip_first_time)
    result = _run(["a", "b hit", "c"], fake, cache_path)
    assert [r.label for r in result.labels] == [0, 1, 0]
    assert fake.calls[-1] == ["b hit"]
    assert result.stats.requests_sent == 2          # 1 batch + 1 retry


def test_always_refused_row_is_blank_with_note(cache_path):
    fake = FakeClassifier(lambda t: SKIP if "abuse" in t else contains_hit(t))
    result = _run(["fine", "abuse text", "hit"], fake, cache_path)
    assert result.labels[1].label is None and result.labels[1].note == Note.REFUSED
    assert result.labels[2].label == 1
    assert result.stats.note_counts == {"refused": 1}


def test_mostly_missing_batch_is_halved_first(cache_path):
    fake = FakeClassifier(lambda t: SKIP if len(fake.calls) == 1 else "0")
    _run([f"t{i}" for i in range(10)], fake, cache_path)
    assert [len(c) for c in fake.calls[:3]] == [10, 5, 5]


def test_blocked_row_isolated_and_noted(cache_path):
    fake = FakeClassifier(lambda t: BLOCK if t == "bad" else "0")
    result = _run(["ok", "bad", "fine"], fake, cache_path)
    assert result.labels[1].note == Note.BLOCKED and result.labels[1].label is None
    assert result.labels[0].label == 0 and result.labels[2].label == 0


def test_api_failure_marks_rows_failed(cache_path):
    result = _run(["a", "b"], FakeClassifier(error=ApiCallError("down")), cache_path)
    assert all(r.note == Note.FAILED and r.label is None for r in result.labels)


def test_bad_key_stops_run(cache_path):
    with pytest.raises(ApiKeyError):
        _run(["a"], FakeClassifier(error=ApiKeyError("bad")), cache_path)


def test_missing_key_raises_before_any_call(cache_path):
    with pytest.raises(ApiKeyError):
        run_query(["a"], "q", api_key=None, cache_path=cache_path)


def test_empty_and_trimmed_notes(cache_path, monkeypatch):
    monkeypatch.setattr("labeler.config.MAX_ROW_CHARS", 5)
    result = _run(["", "hit hit hit", "ok"], FakeClassifier(), cache_path)
    assert result.labels[0].note == Note.EMPTY and result.labels[0].label is None
    assert result.labels[1].note == Note.TRIMMED and result.labels[1].label == 1
    assert result.labels[2].note is None


def test_duplicates_sent_once_and_rerun_uses_cache(cache_path):
    texts = ["same hit", "same hit", "other"]
    fake = FakeClassifier()
    first = _run(texts, fake, cache_path)
    assert fake.calls == [["same hit", "other"]]
    assert [r.label for r in first.labels] == [1, 1, 0]

    second = _run(texts, fake, cache_path)
    assert len(fake.calls) == 1                     # nothing sent again
    assert second.stats.cost_usd == 0 and second.stats.rows_from_cache == 3
    assert [r.label for r in second.labels] == [1, 1, 0]


def test_failed_rows_not_cached(cache_path):
    _run(["a"], FakeClassifier(error=ApiCallError("down")), cache_path)
    fake = FakeClassifier()
    _run(["a"], fake, cache_path)
    assert fake.calls == [["a"]]


def test_estimate_skips_cached_and_duplicate_texts(cache_path):
    _run(["one"], FakeClassifier(), cache_path)
    estimate = estimate_cost(["one", "two", "two", ""], "hit by a vehicle", cache_path=cache_path)
    assert estimate.rows_cached == 1 and estimate.texts_to_send == 1
    assert estimate.cost_usd > 0


def test_pick_test_rows_is_repeatable():
    assert pick_test_rows(1000) == pick_test_rows(1000)
    assert len(pick_test_rows(1000)) == 20
    assert pick_test_rows(5) == [0, 1, 2, 3, 4]


def test_prose_reply_is_never_guessed(cache_path):
    """A reply with no 'id|label' lines (e.g. an apology) leaves every row blank and noted."""
    class ProseClassifier(FakeClassifier):
        async def classify(self, system_prompt, user_prompt, max_output_tokens):
            reply = await super().classify(system_prompt, user_prompt, max_output_tokens)
            return LLMReply(content="Sorry, I can't help with that.", tokens=[], usage=reply.usage)

    result = _run(["a hit", "b", "c"], ProseClassifier(), cache_path)
    assert all(r.label is None and r.note == Note.REFUSED for r in result.labels)
    assert result.stats.not_labelled == 3
