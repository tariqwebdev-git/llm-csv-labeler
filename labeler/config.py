"""All tunable settings in one place. Change values here, not in the code."""
from pathlib import Path

# --- Model -------------------------------------------------------------------
# Confidence scores need token log probabilities. Older chat models return them
# directly (REASONING_EFFORT = None). Newer reasoning models only return them with
# reasoning switched off (REASONING_EFFORT = "none"); otherwise OpenAI rejects
# the request. Check https://developers.openai.com/api/docs/deprecations before
# changing, and update the 3 prices below to match the model.
MODEL = "gpt-6-luna"           # replaced gpt-4o-mini (shuts down 2027-01-14)
REASONING_EFFORT = "none"       # gpt-6-luna is a reasoning model: "none" is required for logprobs

# USD per 1 million tokens (estimates only). Source: OpenAI model page, checked 2026-11-05.
PRICE_INPUT_PER_1M = 0.10
PRICE_CACHED_INPUT_PER_1M = 0.01
PRICE_OUTPUT_PER_1M = 0.50

# --- Claude (Anthropic), the second provider ---------------------------------
# Pick the provider in the app (gear icon, top right); PROVIDER is the starting choice.
# Claude returns no token probabilities, so its labels have no confidence score yet
# (the _conf column stays blank). Prices: Anthropic pricing, checked 2026-11-10
# (rates for prompts up to 100K tokens; batches here are far smaller).
PROVIDER = "openai"                 # "openai" or "anthropic"
ANTHROPIC_MODEL = "claude-haiku-5-5"
ANTHROPIC_PRICE_INPUT_PER_1M = 0.10
ANTHROPIC_PRICE_CACHED_INPUT_PER_1M = 0.01
ANTHROPIC_PRICE_OUTPUT_PER_1M = 0.50
ANTHROPIC_API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"

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
KEYWORD_WHOLE_WORDS_DEFAULT = True  # keyword queries: 'car' does not match 'scar' (a checkbox per query)

# --- Interface ---------------------------------------------------------------
PREVIEW_ROWS = 10          # rows shown in the "Data preview" section
RESULT_PREVIEW_ROWS = 50   # rows shown in the result preview (lowest confidence first)
SIDEBAR_WIDTH_PX = 480     # starting sidebar width (200-600); drag its edge to resize
TABLE_ROW_HEIGHT_PX = 80   # taller rows wrap long answers (about 3 lines); click a cell for all of it
TABLE_TEXT_WIDTH_PX = 480  # starting width of the answer column in the main tables
READING_LIST_TEXT_WIDTH_PX = 220  # same in the sidebar list (stretches to the sidebar's width)
READING_LIST_MAX_ROWS = 5000  # most answers listed in the sidebar
READING_LIST_HEIGHT_PX = 650  # height of the sidebar list; it scrolls inside
SIDEBAR_FILTER_BUTTONS = False  # a query's rows in the sidebar: matches highlighted; True adds
                                # All / Matched / Not matched / Not labelled buttons

# --- Python ------------------------------------------------------------------
MIN_PYTHON = (3, 12)       # the pinned packages (numpy 2.5) need Python 3.12 or newer

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
