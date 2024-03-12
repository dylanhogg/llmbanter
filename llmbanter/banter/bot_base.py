import importlib.resources
import os
from abc import ABC, abstractmethod
from pathlib import Path

import yaml
from loguru import logger

from llmbanter.library.classes import AppUsageException, Response


class BotBase(ABC):
    bot_folder = Path("./bots")

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

        self.temperature = 1.0
        self.model = ""
        self.conversation = []
        self.is_local_file = False
        self.total_tokens = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_chars = 0

    @abstractmethod
    def respond_to(self, user_input: str) -> Response:
        pass

    @abstractmethod
    def cost_estimate_cents(self) -> float:
        pass

    @property
    def conversation_without_system(self) -> list[dict]:
        return [x for x in self.conversation if x["role"] == "user" or x["role"] == "assistant"]

    def is_human(self) -> bool:
        return False

    def get_opener(self) -> Response:
        return Response(self.opener)

    def pair_with(self, other: "BotBase"):
        def talking_with_statement(name):
            # return "You are talking with " + name.replace("_", " ") + " (only address them by name once, not more)\n"
            return "You are talking with " + name.replace("_", " ") + "\n"

        self.system = talking_with_statement(other.name) + self.system
        other.system = talking_with_statement(self.name) + other.system
        self.first_bot = True
        other.first_bot = False

    def system_message(self) -> str:
        return "Not applicable for this bot type: " + type(self).__name__

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def clean_name(self) -> str:
        return self.name.lower().strip().replace(" ", "-")

    def __repr__(self) -> str:
        custom_yaml = " (custom)" if self.is_local_file else ""
        return f"{type(self).__name__} {self.filename}.yaml{custom_yaml} '{self.name}'"

    @classmethod
    def _get_all_resources_bot_filenames(cls) -> list[Path]:
        suffix = ".yaml"
        files = []
        resources_folder = Path(
            importlib.resources.files("llmbanter")._paths[0]  # type: ignore
        )  # TODO: HACK: Fix the use of _paths[0] and test across lower Python versions.
        for root, _, filenames in os.walk(resources_folder):
            for filename in filenames:
                if filename.endswith(suffix):
                    files.append(Path(os.path.join(root, filename)))
        return files

    @classmethod
    def get_all_valid_bot_names(cls, include_system: bool = False) -> list[str]:
        all_bot_filenames = cls._get_all_resources_bot_filenames()
        filenames = [
            f.parent.name + "/" + f.name.replace(".yaml", "")
            for f in all_bot_filenames
            if (include_system or not f.name.startswith("_")) and not f.parent.name == "testing"
        ]
        filenames = sorted(filenames)
        filenames = [f.replace(f"{cls.bot_folder}/", "") for f in filenames]  # TODO: HACK: make this better
        return filenames

    @classmethod
    def get_human_bot(cls) -> "BotBase":
        return cls.get_bot("human")

    @classmethod
    def _get_bot_yaml_file(cls, bot_folder: str, bot_name: str) -> tuple[Path, bool]:
        if len(bot_name.split("/")) == 2:
            # bot_name format 1: 'bot_type/bot_name'
            bot_path = bot_name.split("/")[0]
            bot_name = bot_name.split("/")[1]
            local_path = Path(bot_folder) / bot_path / f"{bot_name}.yaml"
            resources_file = Path(
                str(importlib.resources.files("llmbanter").joinpath(f"{cls.bot_folder}/{bot_path}/{bot_name}.yaml"))
            )
        elif len(bot_name.split("/")) == 1:
            # bot_name format 2: 'bot_name'
            local_path = Path(bot_folder) / f"{bot_name}.yaml"
            resources_file = Path(
                str(importlib.resources.files("llmbanter").joinpath(f"{cls.bot_folder}/{bot_name}.yaml"))
            )
        else:
            raise AppUsageException(
                f"Bot name should be in the format 'bot_type/bot_name' e.g. 'evangelist/instagram'. You specified bot name of '{bot_name}'."
            )

        if local_path.is_file():
            logger.info(f"Using locally found bot file: '{local_path}'")
            is_local_file = True
            return local_path, is_local_file
        elif resources_file.is_file():
            logger.info(f"Using packaged resources bot file: '{resources_file}'")
            is_local_file = False
            return resources_file, is_local_file

        raise AppUsageException(
            f"Given bot name '{bot_name}' was not found locally at ({local_path}) or in the package resources folder ({resources_file}). "
            f"\nCheck the bot name, or try one of: {', '.join(cls.get_all_valid_bot_names())}"
            "\n"
        )

    @classmethod
    def get_bot(cls, bot_name: str, bot_folder: str = "./bots") -> "BotBase":
        file_path, is_local_file = cls._get_bot_yaml_file(bot_folder, bot_name)
        bot_filename = file_path.name.replace(file_path.suffix, "")

        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
                bot_type = data.pop("bot_type")
                bot_types_module = importlib.import_module("llmbanter.banter.bot_types")
                DynamicBotClass = getattr(bot_types_module, bot_type)
                found_bot: BotBase = DynamicBotClass(**data)
                found_bot.filename = bot_filename
                found_bot.is_local_file = is_local_file

                return found_bot
        except FileNotFoundError as e:
            raise AppUsageException(
                f"Bot name '{bot_name}' not found at {file_path}. Try one of: {cls.get_all_valid_bot_names()}"
            ) from e
        except TypeError as e:
            raise AppUsageException(
                f"Bot file {file_path} has incorrect parameters set: {e}. Please fix and run again."
            ) from e
