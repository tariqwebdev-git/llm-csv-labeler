"""The only file that talks to OpenAI. To switch provider, write a new class
with the same `classify` / `close` methods (see models.Classifier)."""
import openai
from openai import AsyncOpenAI

from labeler import config
from labeler.errors import ApiCallError, ApiConfigError, ApiKeyError
from labeler.models import LLMReply, TokenLogprob, TokenUsage

_TOP_LOGPROBS = 2          # we only need the '0' vs '1' alternatives
_CONTENT_FILTER_CODES = ("content_filter", "content_policy_violation")


class OpenAIClassifier:
    """Sends one batch prompt and returns the reply with token logprobs.

    Rate limits, timeouts and 5xx errors are retried by the SDK with
    exponential backoff (config.MAX_RETRIES), honouring Retry-After.
    """

    def __init__(self, api_key: str | None, model: str = config.MODEL, http_client=None):
        """`http_client` is only for tests (a fake HTTP transport); leave it None."""
        if not api_key:
            raise ApiKeyError(f"No OpenAI API key found. Add {config.API_KEY_ENV_VAR}=... to the .env file.")
        self._model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
            max_retries=config.MAX_RETRIES,
            http_client=http_client,
        )

    async def classify(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> LLMReply:
        """Send one batch to OpenAI; map SDK errors to our errors (key, config, failed, blocked)."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.TEMPERATURE,
                max_completion_tokens=max_output_tokens,
                logprobs=True,
                top_logprobs=_TOP_LOGPROBS,
                **_reasoning_options(),
            )
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            # Never include the exception text: it can echo part of the key.
            raise ApiKeyError("OpenAI rejected the API key. Check the key in the .env file.") from exc
        except openai.BadRequestError as exc:
            if _is_content_filter(exc):
                return LLMReply(content="", tokens=[], usage=TokenUsage(), blocked=True)
            raise ApiConfigError(f"OpenAI rejected the request: {exc.message}") from exc
        except openai.NotFoundError as exc:
            raise ApiConfigError(f"Model '{self._model}' unavailable ({exc.message}). Check MODEL in config.py.") from exc
        except openai.APIError as exc:
            raise ApiCallError(f"OpenAI call failed after retries ({type(exc).__name__}).") from exc
        return _to_reply(response)

    async def close(self) -> None:
        """Close the HTTP connection pool."""
        await self._client.close()


def _reasoning_options() -> dict:
    """Reasoning models only return logprobs with reasoning switched off ('none');
    older chat models reject the parameter, so it is sent only when configured."""
    return {"reasoning_effort": config.REASONING_EFFORT} if config.REASONING_EFFORT else {}


def _is_content_filter(exc: openai.BadRequestError) -> bool:
    return exc.code in _CONTENT_FILTER_CODES or "content_filter" in str(exc.body)


def _to_reply(response) -> LLMReply:
    """Convert the SDK response into our provider-neutral LLMReply."""
    choice = response.choices[0]
    logprob_items = choice.logprobs.content if choice.logprobs and choice.logprobs.content else []
    tokens = [
        TokenLogprob(
            token=item.token,
            top_logprobs={alt.token: alt.logprob for alt in item.top_logprobs or []},
        )
        for item in logprob_items
    ]
    usage = response.usage
    cached = usage.prompt_tokens_details.cached_tokens if usage and usage.prompt_tokens_details else 0
    return LLMReply(
        content=choice.message.content or "",
        tokens=tokens,
        usage=TokenUsage(
            input_tokens=usage.prompt_tokens if usage else 0,
            cached_input_tokens=cached or 0,
            output_tokens=usage.completion_tokens if usage else 0,
        ),
        refusal=choice.message.refusal,
        blocked=choice.finish_reason == "content_filter",
    )
