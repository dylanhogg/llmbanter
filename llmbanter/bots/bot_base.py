import importlib
import os
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from llmbanter.library.classes import AppUsageException


class BotBase(ABC):
    bot_folder = Path("./bots_json")

    def __init__(
        self,
        version: float,
        name: str,
        system: str,
        opener: str,
        first_bot: bool = False,
        voice: str = "onyx",
        debug: bool = False,
        filename: str = "",
    ):
        self.version = version
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

    @property
    def clean_name(self):
        return self.name.lower().strip().replace(" ", "-")

    @abstractmethod
    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    @classmethod
    def _get_all_bot_filenames(cls) -> list[Path]:
        suffix = ".yaml"
        files = []
        for root, _, filenames in os.walk(cls.bot_folder):
            for filename in filenames:
                if filename.endswith(suffix):
                    files.append(Path(os.path.join(root, filename)))

        return files

    @classmethod
    def _get_all_valid_bot_names(cls, include_system: bool = False) -> list[str]:
        all_bot_filenames = cls._get_all_bot_filenames()
        filenames = [
            f.parent.name + "/" + f.name.replace(".yaml", "")
            for f in all_bot_filenames
            if include_system or not f.name.startswith("_")
        ]
        filenames = sorted(filenames)
        filenames = [f.replace(f"{cls.bot_folder}/", "") for f in filenames]  # TODO: HACK: make this better
        return filenames

    @classmethod
    def get_human_bot(cls) -> "BotBase":
        return cls.get_bot("human")

    @classmethod
    def get_bot(cls, bot_name) -> "BotBase":
        try:
            if len(bot_name.split("/")) == 2:
                bot_path = bot_name.split("/")[0]
                bot_name = bot_name.split("/")[1]
                file_path = Path("./bots_json") / bot_path / f"{bot_name}.yaml"
            elif len(bot_name.split("/")) == 1:
                file_path = Path("./bots_json") / f"{bot_name}.yaml"
            else:
                raise AppUsageException(
                    f"Bot name should be in the format 'bot_type/bot_name' e.g. 'evangelist/instagram'. You specified bot name of '{bot_name}'."
                )

            # TODO: include and search firstly the local folder for custom bot yaml
            with open(file_path) as f:
                data = yaml.safe_load(f)
                bot_type = data.pop("bot_type")
                bot_types_module = importlib.import_module("llmbanter.bots.bot_types")
                DynamicBotClass = getattr(bot_types_module, bot_type)
                found_bot = DynamicBotClass(**data)
                found_bot.filename = bot_name
                return found_bot
        except FileNotFoundError as e:
            raise AppUsageException(
                f"Bot name '{bot_name}' not found at {file_path}. Try one of: {cls._get_all_valid_bot_names()}"
            ) from e
        except TypeError as e:
            raise AppUsageException(
                f"Bot file {file_path} has incorrect parameters set: {e}. Please fix and run again."
            ) from e
