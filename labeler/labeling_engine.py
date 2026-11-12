"""Public entry point for labelling. The UI and scripts call only these functions.

Flow of run_query():
  prepare rows -> look up cache -> send uncached texts in batches ->
  save each batch to cache -> copy results back to every row -> stats
"""
import asyncio
import random
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from labeler import config
from labeler.batch_runner import BatchRunner
from labeler.cost_estimator import cost_usd, estimate_tokens
from labeler.models import (
    Classifier,
    CostEstimate,
    Note,
    PreparedRows,
    ProgressCallback,
    Provider,
    RowLabel,
    RunResult,
    RunStats,
    TokenUsage,
)
from labeler.keyword_matcher import match_keywords, parse_keywords
from labeler.classifier_factory import make_classifier
from labeler.prompt_builder import SYSTEM_PROMPT
from labeler.provider_settings import default_provider, model_for
from labeler.result_cache import ResultCache
from labeler.row_preparer import prepare_rows


def pick_test_rows(n_rows: int, size: int = config.TEST_SIZE, seed: int = config.TEST_SEED) -> list[int]:
    """Row positions for a test run: random but repeatable (fixed seed)."""
    if n_rows <= size:
        return list(range(n_rows))
    return sorted(random.Random(seed).sample(range(n_rows), size))


def estimate_cost(
    texts: Sequence[object],
    query_text: str,
    *,
    provider: Provider | None = None,
    model: str | None = None,
    cache_path: Path | None = None,
) -> CostEstimate:
    """Estimated cost of labelling `texts`. Cached and duplicate texts cost nothing.

    provider: OpenAI or Claude (default: config.PROVIDER); model: that provider's
    configured model unless given.
    """
    provider = provider or default_provider()
    model = model or model_for(provider)
    prepared = prepare_rows(texts, config.MAX_ROW_CHARS)
    keys = _cache_keys(prepared, query_text, model)
    with ResultCache(cache_path) as cache:
        cached = cache.get_many(keys)

    to_send = [text for text, key in zip(prepared.unique_texts, keys) if key not in cached]
    input_tokens, output_tokens = estimate_tokens(to_send, query_text)
    return CostEstimate(
        rows_total=len(texts),
        rows_cached=_rows_with_cached_text(prepared, keys, cached.keys()),
        texts_to_send=len(to_send),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd(TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens), provider),
    )


def run_query(
    texts: Sequence[object],
    query_text: str,
    *,
    api_key: str | None = None,
    on_progress: ProgressCallback | None = None,
    provider: Provider | None = None,
    model: str | None = None,
    cache_path: Path | None = None,
    classifier: Classifier | None = None,
) -> RunResult:
    """Label each text against `query_text`. Returns one RowLabel per text, same order.

    provider: OpenAI or Claude (default: config.PROVIDER). Claude labels have no
    confidence score yet. Raises ApiKeyError / ApiConfigError if the run cannot continue.
    `classifier` is for tests; normally one is created for the provider from api_key.
    """
    provider = provider or default_provider()
    return asyncio.run(_run_query_async(
        texts, query_text, api_key, on_progress, provider, model or model_for(provider), cache_path, classifier
    ))


def run_keyword_query(
    texts: Sequence[object],
    keywords_text: str,
    whole_words: bool = config.KEYWORD_WHOLE_WORDS_DEFAULT,
) -> RunResult:
    """Label each text 1 if it contains any of the keywords ("car, truck, bus"), else 0.

    No API call and no cost. Matching ignores case; whole_words=True means "car"
    does not match "scar". Empty rows get note 'empty', as with LLM queries.
    """
    started = time.perf_counter()
    labels = match_keywords(texts, parse_keywords(keywords_text), whole_words)
    return RunResult(labels=labels, stats=_run_stats(labels, started))


def clear_cache(cache_path: Path | None = None) -> None:
    """Delete all cached results."""
    with ResultCache(cache_path) as cache:
        cache.clear()


async def _run_query_async(texts, query_text, api_key, on_progress, provider, model, cache_path,
                           classifier) -> RunResult:
    started = time.perf_counter()
    prepared = prepare_rows(texts, config.MAX_ROW_CHARS)
    keys = _cache_keys(prepared, query_text, model)

    with ResultCache(cache_path) as cache:
        cached = cache.get_many(keys)
        unique_labels: list[RowLabel | None] = [cached.get(key) for key in keys]
        todo = [i for i, label in enumerate(unique_labels) if label is None]
        usage = TokenUsage()
        requests_sent = 0

        if todo:
            client = classifier or make_classifier(provider, api_key, model)

            def save_batch(batch_labels: dict[int, RowLabel]) -> None:
                cache.put_many({keys[todo[i]]: label for i, label in batch_labels.items()})

            try:
                output = await BatchRunner(client, query_text).run(
                    [prepared.unique_texts[i] for i in todo], on_progress, save_batch
                )
            finally:
                if classifier is None:
                    await client.close()
            for i, label in output.labels.items():
                unique_labels[todo[i]] = label
            usage = output.usage
            requests_sent = output.requests_sent

    row_labels = _labels_per_row(prepared, unique_labels)
    stats = _run_stats(row_labels, started, rows_from_cache=_rows_with_cached_text(prepared, keys, cached.keys()),
                       texts_sent=len(todo), requests_sent=requests_sent, usage=usage, provider=provider)
    return RunResult(labels=row_labels, stats=stats)


def _run_stats(row_labels: list[RowLabel], started: float, *, rows_from_cache: int = 0, texts_sent: int = 0,
               requests_sent: int = 0, usage: TokenUsage = TokenUsage(),
               provider: Provider = Provider.OPENAI) -> RunStats:
    """Counts shown in the card's result box (same for LLM and keyword queries)."""
    return RunStats(
        rows_total=len(row_labels),
        matched=sum(1 for r in row_labels if r.label == 1),
        not_labelled=sum(1 for r in row_labels if r.label is None),
        note_counts=dict(Counter(r.note.value for r in row_labels if r.note)),
        rows_from_cache=rows_from_cache,
        texts_sent=texts_sent,
        requests_sent=requests_sent,
        usage=usage,
        cost_usd=cost_usd(usage, provider),
        seconds=round(time.perf_counter() - started, 2),
    )


def _cache_keys(prepared: PreparedRows, query_text: str, model: str) -> list[str]:
    return [ResultCache.make_key(model, SYSTEM_PROMPT, query_text, t) for t in prepared.unique_texts]


def _rows_with_cached_text(prepared: PreparedRows, keys: list[str], cached_keys) -> int:
    cached_keys = set(cached_keys)
    return sum(1 for u in prepared.row_to_unique if u is not None and keys[u] in cached_keys)


def _labels_per_row(prepared: PreparedRows, unique_labels: list[RowLabel | None]) -> list[RowLabel]:
    """Copy each unique text's result back to every row that had that text."""
    rows: list[RowLabel] = []
    for row, unique_index in enumerate(prepared.row_to_unique):
        if unique_index is None:
            rows.append(RowLabel(note=Note.EMPTY))
            continue
        label = unique_labels[unique_index] or RowLabel(note=Note.FAILED)
        if row in prepared.trimmed_rows and label.note is None:
            label = replace(label, note=Note.TRIMMED)
        rows.append(label)
    return rows
