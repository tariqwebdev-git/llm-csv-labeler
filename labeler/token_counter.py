"""Count tokens the way the OpenAI model does (used for batching and cost estimates)."""
from functools import lru_cache

import tiktoken

from labeler import config

_FALLBACK_ENCODING = "o200k_base"   # used by current OpenAI chat models


def count_tokens(text: str) -> int:
    """Number of model tokens in `text`."""
    return len(_encoding().encode(text, disallowed_special=()))


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(config.MODEL)
    except KeyError:
        return tiktoken.get_encoding(_FALLBACK_ENCODING)
