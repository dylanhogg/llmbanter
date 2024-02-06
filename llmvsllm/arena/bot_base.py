from abc import ABC, abstractmethod

from joblib import Memory

memory = Memory(".joblib_cache", verbose=0)


class BotBase(ABC):
    def __init__(
        self,
        name: str,
        system: str,
        opener: str,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
        attr_name: str = "",
    ):
        self.name = name
        self.system = system
        self.opener = opener
        self.first_bot = first_bot
        self.attr_name = attr_name
        self.voice = voice
        self.debug = debug

        self.conversation = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @abstractmethod
    def respond_to(self, user_input: str) -> (int, list, str, int, int):
        pass

    @abstractmethod
    def cost_estimate_cents(self):
        pass

    def is_human(self):
        return False

    def get_opener(self):
        return self.opener

    def pair_with(self, other: "BotBase") -> "BotBase":
        def talking_with_statement(name):
            return "You are talking with " + name.replace("_", " ") + " (only address them by name once, not more)\n"

        self.system = talking_with_statement(other.name) + self.system
        other.system = talking_with_statement(self.name) + other.system
        self.first_bot = True
        other.first_bot = False

    @property
    def display_name(self):
        return self.name.lower().replace(" ", "_").replace("(", "").replace(")", "")[0:15]

    def __repr__(self) -> str:
        return f"{type(self).__name__} {self.attr_name} '{self.name}' {self.model}@{self.temperature}{' (1st)' if self.first_bot else ' (2nd)'}"
