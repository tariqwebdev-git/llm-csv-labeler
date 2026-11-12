"""Turn a model reply ("1|0\\n2|1 ...", or from Claude "1|0|85 ...") plus token logprobs
into labels and confidence."""
import math
import re

from labeler.models import RowLabel, TokenLogprob

_LINE = re.compile(r"^\s*(\d+)\s*\|\s*([01])\s*(?:\|\s*(\d{1,3})\s*)?$", re.MULTILINE)
_MIN_SCORE, _MAX_SCORE = 50, 100     # a stated certainty ("|85") is clamped to this range
_ANSWERS = ("0", "1")


def parse_reply(content: str, tokens: list[TokenLogprob], batch_size: int) -> dict[int, RowLabel]:
    """Return {local_id: RowLabel} for every valid line.

    - Ids outside 1..batch_size are ignored.
    - If an id appears twice, the first answer is kept.
    - Missing ids are simply absent; the caller retries them.
    """
    token_at = _answer_tokens_by_offset(tokens)
    results: dict[int, RowLabel] = {}

    for match in _LINE.finditer(content):
        local_id, answer = int(match.group(1)), match.group(2)
        if not 1 <= local_id <= batch_size or local_id in results:
            continue
        token = token_at.get(match.start(2))
        score = match.group(3)
        if token:                       # OpenAI: confidence from token probabilities
            confidence = _confidence(token, answer)
        elif score is not None:         # Claude: the model's own 50-100 rating
            confidence = min(max(int(score), _MIN_SCORE), _MAX_SCORE) / 100
        else:
            confidence = None
        results[local_id] = RowLabel(label=int(answer), confidence=confidence)
    return results


def _answer_tokens_by_offset(tokens: list[TokenLogprob]) -> dict[int, TokenLogprob]:
    """Map the character offset of each '0'/'1' token in the reply to that token.

    Only tokens that are exactly '0' or '1' (ignoring spaces) are mapped, so a
    merged token like '|1' gives no confidence rather than a wrong one.
    """
    index: dict[int, TokenLogprob] = {}
    offset = 0
    for token in tokens:
        stripped = token.token.strip()
        if stripped in _ANSWERS:
            index[offset + token.token.index(stripped)] = token
        offset += len(token.token)
    return index


def _confidence(token: TokenLogprob, answer: str) -> float | None:
    """p(answer) / (p(0) + p(1)) from the token's top alternatives: 0.5 to 1.0."""
    probs = dict.fromkeys(_ANSWERS, 0.0)
    for alt, logprob in token.top_logprobs.items():
        key = alt.strip()
        if key in probs:
            probs[key] += math.exp(logprob)
    total = probs["0"] + probs["1"]
    if total == 0:
        return None
    return round(probs[answer] / total, 2)
