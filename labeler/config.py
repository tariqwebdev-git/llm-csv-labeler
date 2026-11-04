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
BATCH_SIZE = 10            # max rows per request; >20 lets answers drift between items (tested)
MAX_BATCH_ITEM_TOKENS = 1000  # max text tokens per request; keeps long texts in small
                              # batches so answers do not drift between items
MAX_CONCURRENT = 10        # requests in flight at once; lower if you hit rate limits
TEMPERATURE = 0            # same row -> same answer
MAX_RETRIES = 3            # retries on rate limits / timeouts (SDK exponential backoff)
REQUEST_TIMEOUT_SECONDS = 60

# --- Rows --------------------------------------------------------------------
MAX_ROW_CHARS = 2000       # longer text is trimmed and noted "trimmed"
SOFT_ROW_LIMIT = 10_000    # warn above this many rows
EMPTY_WARNING_SHARE = 0.20 # strong warning if more than this share of rows is empty
QUERY_MIN_WORDS = 3        # warn when a query is shorter (short queries are often misread)

# --- Interface ---------------------------------------------------------------
PREVIEW_ROWS = 10          # rows shown after upload
RESULT_PREVIEW_ROWS = 50   # rows shown in the result preview (lowest confidence first)

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
