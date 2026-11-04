"""Token counting and dollar cost, before a run (estimate) and after (actual usage)."""
from functools import lru_cache

import tiktoken

from labeler import config
from labeler.models import TokenUsage
from labeler.prompt_builder import SYSTEM_PROMPT, build_batch_prompt

_FALLBACK_ENCODING = "o200k_base"   # used by current OpenAI chat models


def estimate_tokens(texts: list[str], criterion: str, batch_size: int = config.BATCH_SIZE) -> tuple[int, int]:
    """(input_tokens, output_tokens) to label `texts`, counted on the real prompts."""
    if not texts:
        return 0, 0
    system_tokens = _count(SYSTEM_PROMPT)
    input_tokens = 0
    for start in range(0, len(texts), batch_size):
        prompt = build_batch_prompt(criterion, texts[start:start + batch_size])
        input_tokens += system_tokens + _count(prompt) + config.MESSAGE_OVERHEAD_TOKENS
    output_tokens = len(texts) * config.OUTPUT_TOKENS_PER_ROW_ESTIMATE
    return input_tokens, output_tokens


def cost_usd(usage: TokenUsage) -> float:
    """Dollar cost of the given token usage, using prices in config.py."""
    uncached_input = usage.input_tokens - usage.cached_input_tokens
    return (
        uncached_input * config.PRICE_INPUT_PER_1M
        + usage.cached_input_tokens * config.PRICE_CACHED_INPUT_PER_1M
        + usage.output_tokens * config.PRICE_OUTPUT_PER_1M
    ) / 1_000_000


def _count(text: str) -> int:
    return len(_encoding().encode(text, disallowed_special=()))


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(config.MODEL)
    except KeyError:
        return tiktoken.get_encoding(_FALLBACK_ENCODING)
