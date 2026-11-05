"""Group texts into batches by row count AND text length.

Many long texts in one request make the model drift (one answer influences
the next). Capping the tokens per batch keeps long texts in small batches,
while short survey answers still go 50 at a time (same speed and cost).
"""
from labeler import config
from labeler.token_counter import count_tokens


def plan_batches(
    texts: list[str],
    max_rows: int | None = None,
    max_tokens: int | None = None,
) -> list[list[int]]:
    """Return batches as lists of text indexes, in order.

    A batch closes when it reaches `max_rows` rows or adding the next text would
    exceed `max_tokens`. A single text longer than the budget gets its own batch.
    """
    max_rows = max_rows or config.BATCH_SIZE
    max_tokens = max_tokens or config.MAX_BATCH_ITEM_TOKENS

    batches: list[list[int]] = []
    current: list[int] = []
    used = 0
    for index, text in enumerate(texts):
        tokens = count_tokens(text)
        if current and (len(current) >= max_rows or used + tokens > max_tokens):
            batches.append(current)
            current, used = [], 0
        current.append(index)
        used += tokens
    if current:
        batches.append(current)
    return batches
