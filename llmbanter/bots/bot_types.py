from loguru import logger
from rich import print

from llmbanter.bots.bot_base import BotBase
from llmbanter.library import llm


class LLMBot(BotBase):
    def __init__(
        self,
        version: float,
        name: str,
        system: str,
        opener: str,
        first_bot: bool = False,
        voice: str = "onyx",
        model: str = "gpt-3.5-turbo",
        temperature: float = None,
        debug: bool = False,
    ):
        super().__init__(version, name, system, opener, first_bot, voice, debug)
        self.i = 0
        self.model = model
        self.temperature = temperature

    def __repr__(self) -> str:
        return f"{type(self).__name__} {self.filename}.yaml '{self.name}' {self.model}@{self.temperature}"

    def augmented_conversation_system(self):
        system_messages = [x for x in self.conversation if x["role"] == "system"]
        if len(system_messages) > 1:
            print("WARNING: more than one system message found, using first one.")
        first_system_message = system_messages[0]
        return first_system_message["content"]

    def respond_to(self, user_input: str) -> tuple[int, str]:
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

        llm_result = llm.get_response(self.clean_name, self.model, self.temperature, self.conversation, self.debug)
        self.conversation.append({"role": "assistant", "content": llm_result.chat_response})
        # TODO: adjust tokens by cache_hit value!
        self.total_prompt_tokens += llm_result.prompt_tokens
        self.total_completion_tokens += llm_result.completion_tokens
        self.total_tokens += llm_result.total_tokens
        self.total_chars += len(llm_result.chat_response)
        self.i += 1

        response_nl = llm_result.chat_response.replace("\\n", "\n")
        return (
            self.i,
            response_nl,
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


class HumanInputBot(BotBase):
    def __init__(
        self,
        version: float,
        name: str,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
        multiline: bool = False,
    ):
        system = ""
        opener = None
        super().__init__(version, name, system, opener, first_bot, voice, debug)

        self.i = 0
        self.multiline = multiline

    def __repr__(self) -> str:
        return f"{type(self).__name__} '{self.name}'"

    def get_opener(self):
        assert (
            self.first_bot and self.i == 0
        ), "get_opener() should only be called for first bot at start of conversation."

        if self.multiline:
            lines = []
            try:
                while True:
                    lines.append(input("You (multiline Ctrl+d to end) (opener): "))
            except EOFError:
                pass
            response = "\n".join(lines)
            self.opener = response
            return response
        else:
            while True:
                response = input("You (opener): ").strip()
                if response:
                    self.opener = response
                    return response

    def respond_to(self, user_input: str) -> tuple[int, str]:
        if self.multiline:
            lines = []
            try:
                while True:
                    lines.append(input("You (multiline Ctrl+d to end): "))
            except EOFError:
                pass
            response = "\n".join(lines)
            self.i += 1
            return self.i, response
        else:
            while True:
                response = input("You: ").strip()
                if response:
                    self.i += 1
                    return self.i, response

    def is_human(self):
        return True

    def cost_estimate_cents(self):
        return 0


class FixedResponseBot(BotBase):
    def __init__(
        self,
        version: float,
        name: str,
        opener: str,
        response_list: list,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
    ):
        system = ""
        super().__init__(version, name, system, opener, first_bot, voice, debug)

        self.i = 0
        self.temperature = ""
        self.model = ""
        self.conversation = ["Not applicable, this bot has a fixed response list."]
        self.response_list = response_list

    def __repr__(self) -> str:
        return f"{type(self).__name__} '{self.name}'"

    def respond_to(self, user_input: str) -> tuple[int, str]:
        if self.first_bot and self.i == 0:
            # Include opener in start of conversation (should only apply for the first initiating bot)
            assert (
                self.opener
            ), f"first_bot was True but no opener provided for bot {self.name}. {self.i=}, {self.first_bot=}, {self.opener=}"
            self.conversation.append({"role": "assistant", "content": self.opener})

        response = self.response_list[self.i % len(self.response_list)]
        self.i += 1
        return self.i, response

    def cost_estimate_cents(self):
        return 0
