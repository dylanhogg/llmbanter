from loguru import logger
from rich import print as rprint

from llmbanter.banter.bot_base import BotBase
from llmbanter.library import llm
from llmbanter.library.classes import Response


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
        temperature: float = 1.0,
        debug: bool = False,
    ):
        super().__init__(version, name, system, opener, first_bot, voice, debug)
        self.model = model
        self.temperature = temperature
        self.conversation = [{"role": "system", "content": self.system}]

    def __repr__(self) -> str:
        custom_yaml = " (custom)" if self.is_local_file else ""
        return f"{type(self).__name__} {self.filename}.yaml{custom_yaml} '{self.name}' {self.model}@{self.temperature}"

    def system_message(self) -> str:
        system_messages = [x for x in self.conversation if x["role"] == "system"]
        assert len(system_messages) > 0, "Expected conversation to have been initialized with system message"
        assert len(system_messages) == 1, "Expected conversation to have a single system message"
        first_system_message = system_messages[0]
        return first_system_message["content"]

    def respond_to(self, user_input: str) -> Response:
        assert len(self.conversation) > 0, "Expected conversation to have been initialized with system role"
        if self.first_bot and len(self.conversation) == 1:
            # Include opener in start of conversation (should only apply for the first initiating bot)
            assert (
                self.opener
            ), f"first_bot was True but no opener provided for bot {self.name}. {len(self.conversation)=}, {self.first_bot=}, {self.opener=}"
            self.conversation.append({"role": "assistant", "content": self.opener})

        self.conversation.append({"role": "user", "content": user_input})

        response = llm.get_response(self.clean_name, self.model, self.temperature, self.conversation, self.debug)
        self.conversation.append({"role": "assistant", "content": response.chat_response})

        if not response.cache_hit:
            # TODO: show this have a cached count and a non-cached count to reflect costs for original queries?
            self.total_prompt_tokens += response.prompt_tokens
            self.total_completion_tokens += response.completion_tokens
            self.total_tokens += response.total_tokens
            self.total_chars += len(response.chat_response)

        response.chat_response = response.chat_response.replace(
            "\\n", "\n"
        )  # TODO: do this in BotResponse class perhaps?
        return response

    def cost_estimate_cents(self) -> float:
        # https://openai.com/pricing#language-models (as of Nov 2023)
        def gpt4_8k_price_estimate(prompt_tokens, completion_tokens) -> float:
            return (prompt_tokens / 1000) * 3 + (completion_tokens / 1000) * 6

        def gpt35_4k_price_estimate(prompt_tokens, completion_tokens) -> float:
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
        opener = ""
        super().__init__(version, name, system, opener, first_bot, voice, debug)

        self.i = 0
        self.multiline = multiline

    def get_opener(self) -> Response:
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
            return Response(response)
        else:
            while True:
                rprint("[u][white]Your message (opener):[/white][/u]", end=" ")
                response = input("").strip()
                if response:
                    self.opener = response
                    return Response(response)

    def respond_to(self, user_input: str) -> Response:
        if self.multiline:
            lines = []
            try:
                while True:
                    lines.append(input("You (multiline Ctrl+d to end): "))
            except EOFError:
                pass
            response = "\n".join(lines)
            return Response(response)
        else:
            while True:
                rprint("[u][white]Your message:[/white][/u]", end=" ")
                response = input("").strip()
                if response:
                    return Response(response)

    def is_human(self) -> bool:
        return True

    def cost_estimate_cents(self) -> float:
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
        self.conversation = []
        self.response_list = response_list

    def respond_to(self, user_input: str) -> Response:
        if self.first_bot and self.i == 0:
            # Include opener in start of conversation (should only apply for the first initiating bot)
            assert (
                self.opener
            ), f"first_bot was True but no opener provided for bot {self.name}. {self.i=}, {self.first_bot=}, {self.opener=}"
            self.conversation.append({"role": "assistant", "content": self.opener})

        self.i += 1
        response = self.response_list[self.i % len(self.response_list)]
        return Response(response)

    def cost_estimate_cents(self) -> float:
        return 0
