"""Per-provider model, prices and key name, read from config.py (no SDK imports here)."""
from labeler import config
from labeler.models import Prices, Provider

PROVIDER_LABELS = {Provider.OPENAI: "OpenAI", Provider.ANTHROPIC: "Claude"}


def default_provider() -> Provider:
    """The provider set in config.PROVIDER."""
    return Provider(config.PROVIDER)


def model_for(provider: Provider) -> str:
    """Model name used for this provider."""
    return config.ANTHROPIC_MODEL if provider == Provider.ANTHROPIC else config.MODEL


def prices_for(provider: Provider) -> Prices:
    """Token prices for this provider (read at call time, so scripts can override them)."""
    if provider == Provider.ANTHROPIC:
        return Prices(config.ANTHROPIC_PRICE_INPUT_PER_1M, config.ANTHROPIC_PRICE_CACHED_INPUT_PER_1M,
                      config.ANTHROPIC_PRICE_OUTPUT_PER_1M)
    return Prices(config.PRICE_INPUT_PER_1M, config.PRICE_CACHED_INPUT_PER_1M, config.PRICE_OUTPUT_PER_1M)


def api_key_env_var(provider: Provider) -> str:
    """Name of the .env line that holds this provider's key."""
    return config.ANTHROPIC_API_KEY_ENV_VAR if provider == Provider.ANTHROPIC else config.API_KEY_ENV_VAR


def uses_logprobs(provider: Provider) -> bool:
    """True if confidence comes from token probabilities (OpenAI). False for Claude, whose
    confidence comes from its own rating plus re-checks (confidence_check.py)."""
    return provider != Provider.ANTHROPIC
