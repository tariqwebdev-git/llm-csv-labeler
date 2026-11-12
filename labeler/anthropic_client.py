"""The only file that talks to Anthropic (Claude). Same classify/close methods as
OpenAIClassifier, so the rest of the app does not care which provider answers.

Confidence: Claude's API returns no token probabilities (logprobs), so the reply
carries no tokens and labels come without a confidence score (_conf stays blank).
The agreed confidence method plugs in here, in `classify`, once it is decided.
"""
import anthropic
from anthropic import AsyncAnthropic

from labeler import config
from labeler.errors import ApiCallError, ApiConfigError, ApiKeyError
from labeler.models import LLMReply, TokenUsage


class AnthropicClassifier:
    """Sends one batch prompt to Claude and returns the reply text.

    Rate limits, timeouts and 5xx errors are retried by the SDK with
    exponential backoff (config.MAX_RETRIES), honouring Retry-After.
    """

    def __init__(self, api_key: str | None, model: str = config.ANTHROPIC_MODEL, http_client=None):
        """`http_client` is only for tests (a fake HTTP transport); leave it None."""
        if not api_key:
            raise ApiKeyError(f"No Claude API key found. Add {config.ANTHROPIC_API_KEY_ENV_VAR}=... to the .env file.")
        self._model = model
        self._client = AsyncAnthropic(
            api_key=api_key,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
            max_retries=config.MAX_RETRIES,
            http_client=http_client,
        )

    async def classify(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> LLMReply:
        """Send one batch to Claude; map SDK errors to our errors (key, config, failed)."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_output_tokens,
                # The system prompt is the same for every batch, so it can be served from cache.
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user_prompt}],
                # One short "id|label" line per row needs no reasoning: this keeps it fast and cheap.
                # No temperature: this model rejects sampling settings.
                thinking={"type": "disabled"},
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            # Never include the exception text: it can echo part of the key.
            raise ApiKeyError("Anthropic rejected the Claude API key. Check the key in the .env file.") from exc
        except anthropic.NotFoundError as exc:
            raise ApiConfigError(f"Model '{self._model}' unavailable ({exc.message}). "
                                 "Check ANTHROPIC_MODEL in config.py.") from exc
        except anthropic.BadRequestError as exc:
            raise ApiConfigError(f"Anthropic rejected the request: {exc.message}") from exc
        except anthropic.APIError as exc:      # rate limit, server or network error after retries
            raise ApiCallError(f"Claude call failed after retries ({type(exc).__name__}).") from exc
        return _to_reply(response)

    async def close(self) -> None:
        """Close the HTTP connection pool."""
        await self._client.close()


def _to_reply(response) -> LLMReply:
    """Convert the SDK response into our provider-neutral LLMReply.

    A refusal ("refusal" stop reason) leaves rows unanswered; the batch runner
    then retries them one by one and notes the ones still refused.
    """
    content = "".join(block.text for block in response.content if block.type == "text")
    usage = response.usage
    cache_read = usage.cache_read_input_tokens or 0
    cache_write = usage.cache_creation_input_tokens or 0
    return LLMReply(
        content=content,
        tokens=[],                       # no logprobs from Claude -> no confidence score yet
        usage=TokenUsage(
            input_tokens=usage.input_tokens + cache_read + cache_write,
            cached_input_tokens=cache_read,
            output_tokens=usage.output_tokens,
        ),
        refusal="refusal" if response.stop_reason == "refusal" else None,
    )
