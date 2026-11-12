"""Load the API key (OpenAI or Claude) from .env. The key is never printed or logged."""
import os

from dotenv import load_dotenv

from labeler import config
from labeler.models import Provider
from labeler.provider_settings import api_key_env_var


def load_api_key(provider: Provider = Provider.OPENAI) -> str | None:
    """Return the provider's key from .env (or the environment), or None if missing."""
    load_dotenv(config.ENV_PATH)
    key = os.getenv(api_key_env_var(provider), "").strip()
    return key or None
