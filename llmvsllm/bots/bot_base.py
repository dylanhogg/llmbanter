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
        filename: str = "",
    ):
        self.name = name
        self.system = system
        self.opener = opener
        self.first_bot = first_bot
        self.filename = filename
        self.voice = voice
        self.debug = debug

        self.temperature = None
        self.model = None
        self.conversation = []
        self.total_tokens = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_chars = 0

    @abstractmethod
    def respond_to(self, user_input: str) -> tuple[int, str]:
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
        return self.name

    @abstractmethod
    def __repr__(self) -> str:
        return f"{type(self).__name__}"
