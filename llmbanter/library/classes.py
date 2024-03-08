from dataclasses import dataclass


class AppUsageException(Exception):
    pass


@dataclass
class Response:
    def __init__(
        self,
        chat_response: str,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cache_hit: bool = False,
    ):
        self.chat_response = chat_response
        self.total_tokens = total_tokens
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cache_hit = cache_hit

    chat_response: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cache_hit: bool
