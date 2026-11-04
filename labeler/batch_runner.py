"""Send batches concurrently and recover rows the model skipped, refused or blocked.

Recovery rules (never guess a label):
  - Some rows missing from a reply -> those rows are retried one by one.
  - More than half missing -> retried once in two halves, then one by one.
  - A single row still missing -> blank label, note "refused" (or "blocked"
    if the content filter stopped it).
  - API failure after the SDK's retries -> rows in that request get "failed"
    (no splitting: smaller requests do not fix rate limits or outages).
  - ApiKeyError / ApiConfigError -> the whole run stops.
"""
import asyncio

from labeler import config
from labeler.errors import ApiCallError
from labeler.models import (
    BatchLabelledCallback,
    BatchRunOutput,
    Classifier,
    LLMReply,
    Note,
    ProgressCallback,
    RowLabel,
    TokenUsage,
)
from labeler.prompt_builder import SYSTEM_PROMPT, build_batch_prompt
from labeler.response_parser import parse_reply

_REPLY_OVERHEAD_TOKENS = 16


class BatchRunner:
    def __init__(
        self,
        classifier: Classifier,
        criterion: str,
        *,
        batch_size: int = config.BATCH_SIZE,
        max_concurrent: int = config.MAX_CONCURRENT,
    ):
        self._classifier = classifier
        self._criterion = criterion
        self._batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._usage = TokenUsage()

    async def run(
        self,
        texts: list[str],
        on_progress: ProgressCallback | None = None,
        on_batch_labelled: BatchLabelledCallback | None = None,
    ) -> BatchRunOutput:
        """Label every text. Returns {text_index: RowLabel} and total token usage."""
        batches = [
            list(range(start, min(start + self._batch_size, len(texts))))
            for start in range(0, len(texts), self._batch_size)
        ]
        labels: dict[int, RowLabel] = {}
        done = 0

        async def run_batch(indices: list[int]) -> None:
            nonlocal done
            batch_labels = await self._label_group(texts, indices, allow_halving=True)
            labels.update(batch_labels)
            if on_batch_labelled:
                on_batch_labelled(batch_labels)
            done += 1
            if on_progress:
                on_progress(done, len(batches))

        tasks = [asyncio.create_task(run_batch(b)) for b in batches]
        try:
            await asyncio.gather(*tasks)
        except BaseException:
            # A fatal error (bad key, bad model) stops all other batches.
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        return BatchRunOutput(labels=labels, usage=self._usage)

    async def _label_group(self, texts: list[str], indices: list[int], allow_halving: bool) -> dict[int, RowLabel]:
        reply = await self._send([texts[i] for i in indices])
        if reply is None:
            return {i: RowLabel(note=Note.FAILED) for i in indices}

        if reply.blocked:
            parsed, failure_note = {}, Note.BLOCKED
        else:
            parsed, failure_note = parse_reply(reply.content, reply.tokens, len(indices)), Note.REFUSED

        labels = {indices[local_id - 1]: label for local_id, label in parsed.items()}
        missing = [i for i in indices if i not in labels]
        if not missing:
            return labels
        if len(indices) == 1:
            labels[indices[0]] = RowLabel(note=failure_note)
            return labels

        if allow_halving and len(missing) > 1 and len(missing) > len(indices) / 2:
            middle = (len(missing) + 1) // 2
            groups = [missing[:middle], missing[middle:]]
        else:
            groups = [[i] for i in missing]

        retried = await asyncio.gather(
            *(self._label_group(texts, group, allow_halving=False) for group in groups)
        )
        for group_labels in retried:
            labels.update(group_labels)
        return labels

    async def _send(self, items: list[str]) -> LLMReply | None:
        """One API call under the concurrency limit. None means it failed after retries."""
        max_tokens = len(items) * config.OUTPUT_TOKENS_PER_ROW_LIMIT + _REPLY_OVERHEAD_TOKENS
        async with self._semaphore:
            try:
                reply = await self._classifier.classify(
                    SYSTEM_PROMPT, build_batch_prompt(self._criterion, items), max_tokens
                )
            except ApiCallError:
                return None
        self._usage = TokenUsage(
            self._usage.input_tokens + reply.usage.input_tokens,
            self._usage.cached_input_tokens + reply.usage.cached_input_tokens,
            self._usage.output_tokens + reply.usage.output_tokens,
        )
        return reply
