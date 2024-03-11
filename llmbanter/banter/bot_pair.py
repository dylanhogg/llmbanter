from llmbanter.banter.bot_base import BotBase


class BotPair:
    def __init__(
        self, bot1_name: str, bot2_name: str, model1: str, model2: str, temperature1: float, temperature2: float
    ):
        assert bot1_name, "bot1_name required"
        assert bot2_name, "bot2_name required"
        assert model1, "model1 required"
        assert model2, "model2 required"

        # Initialization
        self.bot1 = BotBase.get_bot(bot1_name)
        self.bot1.model = model1
        if self.bot1.temperature is None:
            self.bot1.temperature = temperature1
        assert isinstance(self.bot1.system, str), f"system must be a string, not {type(self.bot1.system)=}"

        self.bot2 = BotBase.get_bot(bot2_name)
        self.bot2.model = model2
        if self.bot2.temperature is None:
            self.bot2.temperature = temperature2
        assert isinstance(self.bot2.system, str), f"system must be a string, not {type(self.bot1.system)=}"

        # Pair bots
        self.bot1.pair_with(self.bot2)
