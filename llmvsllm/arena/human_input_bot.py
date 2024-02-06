from llmvsllm.arena.bot_base import BotBase


class HumanInputBot(BotBase):
    def __init__(
        self,
        name: str,
        system: str,
        opener: str,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
        multiline: bool = False,
    ):
        super().__init__(name, system, opener, first_bot, voice, debug)

        self.i = 0
        self.system = ""
        self.temperature = "0"
        self.model = "NA"
        self.conversation = ["Not applicable, this bot is controlled by human input."]
        self.multiline = multiline

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

    def respond_to(self, user_input: str) -> (int, list, str, int, int):
        if self.multiline:
            lines = []
            try:
                while True:
                    lines.append(input("You (multiline Ctrl+d to end): "))
            except EOFError:
                pass
            response = "\n".join(lines)
            self.i += 1
            return self.i, self.conversation, response, 0, 0
        else:
            while True:
                response = input("You: ").strip()
                if response:
                    self.i += 1
                    return self.i, self.conversation, response, 0, 0

    def is_human(self):
        return True

    def cost_estimate_cents(self):
        return 0
