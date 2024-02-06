import copy
import inspect

from llmvsllm.arena.bot_base import BotBase
from llmvsllm.bots.generic_llm_bots import GenericLLMBots
from llmvsllm.bots.system_bots import SystemBots
from llmvsllm.library.classes import AppUsageException


class AllBots(
    GenericLLMBots,
    SystemBots,
):
    pass


class BotPair:
    def get_all_bot_names(self) -> list[str]:
        result = [
            m[0] for m in inspect.getmembers(AllBots()) if not m[0].startswith("_") and not inspect.ismethod(m[1])
        ]
        return sorted(result)

    def get_bot(self, bot_name) -> BotBase:
        try:
            found_bot = getattr(AllBots(), bot_name)
            found_bot.attr_name = bot_name
            return copy.deepcopy(found_bot)
        except AttributeError as e:
            # print(f"Bot name {bot_name} not found. Try one of: {self.get_all_bot_names()}")
            raise AppUsageException(f"Bot name {bot_name} not found. Try one of: {self.get_all_bot_names()}") from e

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
