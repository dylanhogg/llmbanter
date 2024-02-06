from joblib import Memory
from litellm import completion
from loguru import logger
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential

from llmvsllm.arena.bot_base import BotBase

memory = Memory(".joblib_cache", verbose=0)


class LLMBot(BotBase):
    def __init__(
        self,
        name: str,
        system: str,
        opener: str,
        first_bot: bool = False,
        voice: str = "onyx",
        model: str = "gpt-3.5-turbo",
        temperature: float = None,
        debug: bool = False,
    ):
        super().__init__(name, system, opener, first_bot, voice, debug)
        self.i = 0
        self.model = model
        self.temperature = temperature

    @staticmethod
    @memory.cache()
    @retry(
        wait=wait_exponential(multiplier=5, min=2, max=600),
        stop=stop_after_attempt(3),
        before_sleep=lambda state: logger.warning(f"Retrying OpenAI API call #{state.attempt_number}..."),
    )
    def _openai_call(model: str, messages: list, temperature: float, debug: bool = False):
        assert temperature is not None, f"Expected value for: {temperature=}"
        # TODO: handle errors like:
        # BadRequestError: Error code: 400 - {'error': {'message': "This model's maximum context length is 4097 tokens. However, your messages resulted in 12197 tokens. Please reduce the length of the messages.", 'type': 'invalid_request_error', 'param': 'messages', 'code': 'context_length_exceeded'}}
        completion_response = completion(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return completion_response

    def augmented_conversation_system(self):
        system_messages = [x for x in self.conversation if x["role"] == "system"]
        if len(system_messages) > 1:
            print("WARNING: more than one system message found, using first one.")
        first_system_message = system_messages[0]
        return first_system_message["content"]

    def respond_to(self, user_input: str) -> (int, list, str, int, int):
        if len(self.conversation) == 0 and self.i == 0:
            # Include system prompt in start of conversation (delayed until first response call so system can be updated after instantiation)
            self.conversation = [{"role": "system", "content": self.system}]

        if user_input == "%system":
            response = self.augmented_conversation_system()
            return self.i, self.conversation, response, 0, 0

        if user_input == "%debug":
            self.debug = not self.debug
            response = "Debug mode is now " + ("on." if self.debug else "off.")
            return self.i, self.conversation, response, 0, 0

        if user_input == "%full_conversation":
            #  print(f"{self.conversation=}")
            response = self.conversation
            return self.i, self.conversation, response, 0, 0

        if user_input == "%conversation":
            #  print(f"{self.conversation=}")
            response = [x for x in self.conversation if x["role"] == "user" or x["role"] == "assistant"]
            return self.i, self.conversation, response, 0, 0

        assert len(self.conversation) > 0, "Expected conversation to have been initialized with system role"
        if self.first_bot and self.i == 0:
            # Include opener in start of conversation (should only apply for the first initiating bot)
            assert (
                self.opener
            ), f"first_bot was True but no opener provided for bot {self.name}. {self.i=}, {self.first_bot=}, {self.opener=}"
            self.conversation.append({"role": "assistant", "content": self.opener})

        self.conversation.append({"role": "user", "content": user_input})
        completion = self._openai_call(self.model, self.conversation, self.temperature, self.debug)
        assert completion.model.startswith(self.model)
        response = completion.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": response})
        self.i += 1

        self.total_prompt_tokens += completion.usage.prompt_tokens
        self.total_completion_tokens += completion.usage.completion_tokens

        response_nl = response.replace("\\n", "\n")
        return (
            self.i,
            self.conversation,
            response_nl,
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )

    def cost_estimate_cents(self):
        # https://openai.com/pricing#language-models (as of Nov 2023)
        def gpt4_8k_price_estimate(prompt_tokens, completion_tokens):
            return (prompt_tokens / 1000) * 3 + (completion_tokens / 1000) * 6

        def gpt35_4k_price_estimate(prompt_tokens, completion_tokens):
            return (prompt_tokens / 1000) * 0.1 + (completion_tokens / 1000) * 0.2

        if self.model.startswith("gpt-3.5"):
            return gpt35_4k_price_estimate(self.total_prompt_tokens, self.total_completion_tokens)
        elif self.model.startswith("gpt-4"):
            return gpt4_8k_price_estimate(self.total_prompt_tokens, self.total_completion_tokens)
        else:
            logger.warning(f"Unknown model {self.model}, can't estimate cost.")
            return -1
