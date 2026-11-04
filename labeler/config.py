"""All tunable settings in one place. Change values here, not in the code."""
from pathlib import Path

# --- Model -------------------------------------------------------------------
# Must be a standard chat model (NOT a reasoning model): confidence scores
# depend on token log probabilities, which reasoning models do not return.
MODEL = "gpt-4o-mini"

# USD per 1 million tokens, from https://openai.com/api/pricing (estimates only).
PRICE_INPUT_PER_1M = 0.15
PRICE_CACHED_INPUT_PER_1M = 0.075
PRICE_OUTPUT_PER_1M = 0.60

# --- Batching and speed ------------------------------------------------------
BATCH_SIZE = 50            # rows per request; lower to 25 if parsing errors appear
MAX_CONCURRENT = 10        # requests in flight at once; lower if you hit rate limits
TEMPERATURE = 0            # same row -> same answer
MAX_RETRIES = 3            # retries on rate limits / timeouts (SDK exponential backoff)
REQUEST_TIMEOUT_SECONDS = 60

# --- Rows --------------------------------------------------------------------
MAX_ROW_CHARS = 2000       # longer text is trimmed and noted "trimmed"
SOFT_ROW_LIMIT = 10_000    # warn above this many rows

# --- Test runs ---------------------------------------------------------------
TEST_SIZE = 20             # rows in a test run
TEST_SEED = 42             # fixed so a test run always uses the same rows

# --- Token budget ------------------------------------------------------------
# A reply line looks like "12|1\n" (~4 tokens). Used for estimates and as a
# hard cap on reply length so a runaway reply cannot cost more.
OUTPUT_TOKENS_PER_ROW_ESTIMATE = 4
OUTPUT_TOKENS_PER_ROW_LIMIT = 8
MESSAGE_OVERHEAD_TOKENS = 10   # chat formatting tokens added per request

# --- Files -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = PROJECT_ROOT / "cache.db"
ENV_PATH = PROJECT_ROOT / ".env"
API_KEY_ENV_VAR = "OPENAI_API_KEY"
