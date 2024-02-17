from joblib import Memory
from litellm import completion
from loguru import logger
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from .classes import AppUsageException

memory = Memory(".joblib_cache", verbose=0)

# TODO: try/catch! E.g.
#       APIError: HTTP code 502 from API
#       Timeout: Request timed out: HTTPSConnectionPool(host='api.openai.com', port=443): Read timed out. (read timeout=600)


def log_retry(state):
    msg = (
        f"Tenacity retry {state.fn.__name__}: {state.attempt_number=}, {state.idle_for=}, {state.seconds_since_start=}"
    )
    if state.attempt_number < 1:
        logger.info(msg)
    else:
        logger.exception(msg)


@memory.cache()
@retry(
    wait=wait_exponential(multiplier=2, min=5, max=600),
    stop=stop_after_attempt(3),
    before_sleep=log_retry,
    retry=retry_if_not_exception_type(AppUsageException),
)
def make_call(model: str, temperature: float, messages: list, debug: bool = False) -> tuple[str, int, int, int]:
    assert model is not None, f"Expected value for: {model=}"
    assert temperature is not None, f"Expected value for: {temperature=}"
    assert len(messages) > 0, f"Expected value for: {messages=}"
    # TODO: assert messages contain a single {"role": "system"} entry

    # TODO: handle errors like:
    # BadRequestError: Error code: 400 - {'error': {'message': "This model's maximum context length is 4097 tokens. However, your messages resulted in 12197 tokens. Please reduce the length of the messages.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}

    api_response = completion(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    assert api_response.model.startswith(model)

    chat_response = api_response.choices[0].message.content
    total_tokens = int(api_response["usage"]["total_tokens"])
    prompt_tokens = int(api_response["usage"]["prompt_tokens"])
    completion_tokens = int(api_response["usage"]["completion_tokens"])

    return chat_response, total_tokens, prompt_tokens, completion_tokens  # TODO: dataclass return type
