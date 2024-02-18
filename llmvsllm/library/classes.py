from dataclasses import dataclass


class AppUsageException(Exception):
    pass


@dataclass
class LLMResult:
    chat_response: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cache_hit: bool
