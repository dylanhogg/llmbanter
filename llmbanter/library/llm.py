import hashlib
import pickle
from pathlib import Path

from litellm import completion, exceptions
from litellm.utils import ModelResponse
from loguru import logger

# from tenacity import (
#     retry,
#     retry_if_not_exception_type,
#     stop_after_attempt,
#     wait_exponential,
# )
from llmbanter.library import consts
from llmbanter.library.classes import AppUsageException, Response


def log_retry(state):
    msg = (
        f"Tenacity retry {state.fn.__name__}: {state.attempt_number=}, {state.idle_for=}, {state.seconds_since_start=}"
    )
    if state.attempt_number < 1:
        logger.info(msg)
    else:
        logger.exception(msg)


# @retry(
#     wait=wait_exponential(multiplier=2, min=5, max=600),
#     stop=stop_after_attempt(2),
#     before_sleep=log_retry,
#     retry=retry_if_not_exception_type(AppUsageException | exceptions.APIConnectionError),
# )
def _get_response_cached(
    bot_name: str, model: str, temperature: float, messages: list, cache_folder: str = consts.default_cache_folder_llm
) -> tuple[ModelResponse, bool]:
    args = f"{bot_name}-{model}@{temperature}-{messages}"
    args_hash = hashlib.sha256(args.encode()).hexdigest()
    filename_hash = f"{bot_name}_{model}_{temperature}_{args_hash}.pkl"

    folder = Path(cache_folder) / bot_name
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / filename_hash

    if filepath.exists():
        with open(filepath, "rb") as f:
            api_response = pickle.load(f)
            cache_hit = True
    else:
        # TODO: handle errors like:
        # BadRequestError: Error code: 400 - {'error': {'message': "This model's maximum context length is 4097 tokens. However, your messages resulted in 12197 tokens. Please reduce the length of the messages.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}
        # APIError: HTTP code 502 from API, Timeout: Request timed out: HTTPSConnectionPool(host='api.openai.com', port=443): Read timed out. (read timeout=600)
        api_response = completion(
            model=model,
            temperature=temperature,
            messages=messages,
        )
        assert api_response.model and api_response.model.startswith(model)
        with open(filepath, "wb") as f:
            pickle.dump(api_response, f)
        cache_hit = False

    assert isinstance(
        api_response, ModelResponse
    ), f"Expected api_response to be a ModelResponse, not {type(api_response)=}"
    return api_response, cache_hit


def get_response(bot_name: str, model: str, temperature: float, messages: list, debug: bool = False) -> Response:
    assert model is not None, f"Expected value for: {model=}"
    assert temperature is not None, f"Expected value for: {temperature=}"
    assert len(messages) > 0, f"Expected value for: {messages=}"
    # TODO: assert messages contain a single {"role": "system"} entry

    try:
        api_response, cache_hit = _get_response_cached(bot_name, model, temperature, messages)
    except exceptions.APIConnectionError as e:
        raise AppUsageException(
            f"APIConnectionError: {e}\n"
            "See https://litellm.vercel.app/docs/providers for additional information on setting LLM provider, keys etc."
        ) from e

    chat_response = api_response.choices[0].message.content  # type: ignore
    total_tokens = int(api_response["usage"]["total_tokens"])
    prompt_tokens = int(api_response["usage"]["prompt_tokens"])
    completion_tokens = int(api_response["usage"]["completion_tokens"])

    return Response(chat_response, total_tokens, prompt_tokens, completion_tokens, cache_hit)
