"""A fake Classifier for tests: answers by rule, records calls, costs nothing."""
import math
from collections.abc import Callable

from labeler.models import LLMReply, TokenLogprob, TokenUsage

BLOCK = "BLOCK"   # answer that makes the whole request content-filtered
SKIP = None       # answer that leaves the row out of the reply (like a refusal)


def contains_hit(text: str) -> str:
    return "1" if "hit" in text.lower() else "0"


class FakeClassifier:
    def __init__(self, answer: Callable[[str], str | None] = contains_hit, error: Exception | None = None,
                 confidence: float = 0.9):
        self.answer = answer
        self.error = error
        self.confidence = confidence
        self.calls: list[list[str]] = []

    async def classify(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> LLMReply:
        items = [line.split("|", 1)[1] for line in user_prompt.split("Items:\n", 1)[1].splitlines()]
        self.calls.append(items)
        if self.error:
            raise self.error

        tokens: list[TokenLogprob] = []
        for local_id, text in enumerate(items, start=1):
            answer = self.answer(text)
            if answer == BLOCK:
                return LLMReply(content="", tokens=[], usage=TokenUsage(), blocked=True)
            if answer is SKIP:
                continue
            other = "0" if answer == "1" else "1"
            tokens += [
                TokenLogprob(str(local_id), {}),
                TokenLogprob("|", {}),
                TokenLogprob(answer, {answer: math.log(self.confidence), other: math.log(1 - self.confidence)}),
                TokenLogprob("\n", {}),
            ]
        content = "".join(t.token for t in tokens)
        return LLMReply(content=content, tokens=tokens, usage=TokenUsage(100, 0, len(tokens)))

    async def close(self) -> None:
        pass
