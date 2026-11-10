"""Dollar cost, before a run (estimate) and after (actual usage)."""
from labeler import config
from labeler.batch_planner import plan_batches
from labeler.models import Provider, TokenUsage
from labeler.prompt_builder import SYSTEM_PROMPT, build_batch_prompt
from labeler.provider_settings import prices_for
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


def cost_usd(usage: TokenUsage, provider: Provider = Provider.OPENAI) -> float:
    """Dollar cost of the given token usage, using the provider's prices in config.py."""
    prices = prices_for(provider)
    uncached_input = usage.input_tokens - usage.cached_input_tokens
    return (
        uncached_input * prices.input_per_1m
        + usage.cached_input_tokens * prices.cached_input_per_1m
        + usage.output_tokens * prices.output_per_1m
    ) / 1_000_000
