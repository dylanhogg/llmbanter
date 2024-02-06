from llmvsllm.arena.bot_base import BotBase


class FixedRespoonseBot(BotBase):
    def __init__(
        self,
        name: str,
        system: str,
        opener: str,
        response_list: list,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
    ):
        super().__init__(name, system, opener, first_bot, voice, debug)

        self.i = 0
        self.system = ""
        self.temperature = ""
        self.model = ""
        self.conversation = ["Not applicable, this bot has a fixed response list."]
        self.response_list = response_list

    def respond_to(self, user_input: str) -> (int, list, str, int, int):
        if self.first_bot and self.i == 0:
            # Include opener in start of conversation (should only apply for the first initiating bot)
            assert (
                self.opener
            ), f"first_bot was True but no opener provided for bot {self.name}. {self.i=}, {self.first_bot=}, {self.opener=}"
            self.conversation.append({"role": "assistant", "content": self.opener})

        response = self.response_list[self.i % len(self.response_list)]
        self.i += 1
        return self.i, self.conversation, response, 0, 0

    def cost_estimate_cents(self):
        return 0
