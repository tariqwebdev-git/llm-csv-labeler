"""Create the right classifier (OpenAI or Claude) for a run."""
from labeler.anthropic_client import AnthropicClassifier
from labeler.models import Classifier, Provider
from labeler.openai_client import OpenAIClassifier
from labeler.provider_settings import model_for


def make_classifier(provider: Provider, api_key: str | None, model: str | None = None) -> Classifier:
    """A classifier for `provider`, using its configured model unless `model` is given."""
    model = model or model_for(provider)
    if provider == Provider.ANTHROPIC:
        return AnthropicClassifier(api_key, model)
    return OpenAIClassifier(api_key, model)
