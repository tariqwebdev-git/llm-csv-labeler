"""Dollar cost, before a run (estimate) and after (actual usage)."""
from labeler import config
from labeler.batch_planner import plan_batches
from labeler.models import TokenUsage
from labeler.prompt_builder import SYSTEM_PROMPT, build_batch_prompt
from labeler.token_counter import count_tokens


def estimate_tokens(texts: list[str], criterion: str) -> tuple[int, int]:
    """(input_tokens, output_tokens) to label `texts`, counted on the real batch prompts."""
    if not texts:
        return 0, 0
    system_tokens = count_tokens(SYSTEM_PROMPT)
    input_tokens = 0
    for batch in plan_batches(texts):
        prompt = build_batch_prompt(criterion, [texts[i] for i in batch])
        input_tokens += system_tokens + count_tokens(prompt) + config.MESSAGE_OVERHEAD_TOKENS
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
