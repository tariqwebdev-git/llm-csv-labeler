"""Load the OpenAI API key from .env. The key is never printed or logged."""
import os

from dotenv import load_dotenv

from labeler import config


def load_api_key() -> str | None:
    """Return the key from .env (or the environment), or None if missing."""
    load_dotenv(config.ENV_PATH)
    key = os.getenv(config.API_KEY_ENV_VAR, "").strip()
    return key or None
