import importlib
import os
from pathlib import Path

import yaml

from llmvsllm.bots.bot_base import BotBase
from llmvsllm.library.classes import AppUsageException


class BotPair:
    bot_folder = Path("./bots_json")

    def get_all_bot_filenames(self) -> list[Path]:
        suffix = ".yaml"
        files = []
        for root, _, filenames in os.walk(self.bot_folder):
            for filename in filenames:
                if filename.endswith(suffix):
                    files.append(Path(os.path.join(root, filename)))

        return files

    def get_all_valid_bot_names(self, include_system: bool = False) -> list[str]:
        all_bot_filenames = self.get_all_bot_filenames()
        filenames = [
            f.parent.name + "/" + f.name.replace(".yaml", "")
            for f in all_bot_filenames
            if include_system or not f.name.startswith("_")
        ]
        filenames = sorted(filenames)
        filenames = [f.replace(f"{self.bot_folder}/", "") for f in filenames]  # TODO: HACK: make this better
        return filenames

    def get_bot(self, bot_name) -> BotBase:
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
                bot_types_module = importlib.import_module("llmvsllm.bots.bot_types")
                DynamicBotClass = getattr(bot_types_module, bot_type)
                found_bot = DynamicBotClass(**data)
                found_bot.filename = bot_name
                return found_bot
        except FileNotFoundError as e:
            raise AppUsageException(
                f"Bot name '{bot_name}' not found at {file_path}. Try one of: {self.get_all_valid_bot_names()}"
            ) from e
        except TypeError as e:
            raise AppUsageException(
                f"Bot file {file_path} has incorrect parameters set: {e}. Please fix and run again."
            ) from e

    def get_human_bot(self) -> BotBase:
        return self.get_bot("human")

    def __init__(
        self, bot1_name: str, bot2_name: str, model1: str, model2: str, temperature1: float, temperature2: float
    ):
        assert bot1_name, "bot1_name required"
        assert bot2_name, "bot2_name required"
        assert model1, "model1 required"
        assert model2, "model2 required"

        # Initialization
        self.bot1 = self.get_bot(bot1_name)
        self.bot1.model = model1
        if self.bot1.temperature is None:
            self.bot1.temperature = temperature1
        assert isinstance(self.bot1.system, str), f"system must be a string, not {type(self.bot1.system)=}"

        self.bot2 = self.get_bot(bot2_name)
        self.bot2.model = model2
        if self.bot2.temperature is None:
            self.bot2.temperature = temperature2
        assert isinstance(self.bot2.system, str), f"system must be a string, not {type(self.bot1.system)=}"

        # Pair bots
        self.bot1.pair_with(self.bot2)
