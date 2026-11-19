"""One LLM adapter, deliberately not named after a model.

Ollama (local) and vLLM (GPU) both speak the OpenAI protocol, so *which* ~7B
open model we run is a config value. That is why there is no ``qwen.py`` here:
re-picking the model at bench time must not rename a file.

!! VERIFY ON FIRST RUN (step 3): the OpenAILLMService import path against the
   installed Pipecat.
"""

from pipecat.services.openai.llm import OpenAILLMService

from gotiny.core.settings import settings


def build_llm(
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> OpenAILLMService:
    return OpenAILLMService(
        model=model or settings.llm_model,
        base_url=base_url or settings.llm_base_url,
        api_key=api_key or settings.llm_api_key,
    )
