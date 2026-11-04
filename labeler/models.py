"""Data types shared across the app. Types only: no business logic lives here."""
from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

# Called after each finished batch with (batches_done, batches_total).
ProgressCallback = Callable[[int, int], None]
# Called after each finished batch with {text_index: RowLabel} for that batch.
BatchLabelledCallback = Callable[[dict[int, "RowLabel"]], None]


class Note(str, Enum):
    """Why a row needs attention. Written to the `<name>_note` column."""
    EMPTY = "empty"        # no text, not sent
    TRIMMED = "trimmed"    # text cut to MAX_ROW_CHARS, still labelled
    REFUSED = "refused"    # model would not answer for this row
    BLOCKED = "blocked"    # content filter blocked the request
    FAILED = "failed"      # API error after all retries


class QueryStatus(str, Enum):
    NOT_RUN = "Not run"
    TESTED = "Tested"
    RUNNING = "Running"
    DONE = "Done"
    DONE_WITH_ERRORS = "Done with errors"
    OUT_OF_DATE = "Out of date"


@dataclass
class Query:
    """One user query; becomes one set of output columns."""
    name: str                       # short column name, e.g. "car_crashes"
    text: str                       # full criterion, e.g. "Answers about car crashes"
    status: QueryStatus = QueryStatus.NOT_RUN
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass(frozen=True)
class RowLabel:
    """Result for one row. label is None when the row was not labelled."""
    label: int | None = None
    confidence: float | None = None
    note: Note | None = None


@dataclass(frozen=True)
class TokenLogprob:
    """One generated token with its top alternative tokens (token -> logprob)."""
    token: str
    top_logprobs: dict[str, float]


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class LLMReply:
    """Provider-neutral reply from one classification request."""
    content: str
    tokens: list[TokenLogprob]
    usage: TokenUsage
    refusal: str | None = None
    blocked: bool = False           # content filter stopped the reply


class Classifier(Protocol):
    """Anything that can classify one batch. OpenAIClassifier is the real one;
    tests use a fake. Implement this to switch provider."""

    async def classify(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> LLMReply: ...

    async def close(self) -> None: ...


@dataclass(frozen=True)
class PreparedRows:
    """Rows ready to send.

    unique_texts: de-duplicated, sanitised texts to label.
    row_to_unique: per input row, index into unique_texts (None = empty row).
    trimmed_rows: input row positions whose text was trimmed.
    """
    unique_texts: list[str]
    row_to_unique: list[int | None]
    trimmed_rows: frozenset[int]


@dataclass(frozen=True)
class BatchRunOutput:
    """What BatchRunner returns: labels by text index, plus tokens used."""
    labels: dict[int, RowLabel]
    usage: TokenUsage


@dataclass(frozen=True)
class CostEstimate:
    rows_total: int
    rows_cached: int                # rows whose text is already in the cache
    texts_to_send: int              # unique, uncached texts
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class RunStats:
    rows_total: int
    matched: int
    not_labelled: int
    note_counts: dict[str, int]
    rows_from_cache: int
    texts_sent: int
    usage: TokenUsage
    cost_usd: float
    seconds: float


@dataclass(frozen=True)
class RunResult:
    labels: list[RowLabel]          # one per input row, same order
    stats: RunStats
