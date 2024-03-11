import typer

from llmbanter.banter.bot_base import BotBase
from llmbanter.banter.bot_pair import BotPair


class Commands:
    command_indicator = "/"

    @classmethod
    def _get_commands(cls) -> list[str]:
        methods = [
            method
            for method in dir(Commands)
            # NOTE: ignore methods starting with _ and ending with _
            if callable(getattr(Commands, method)) and not method.startswith("_") and not method.endswith("_")
        ]
        return methods

    @classmethod
    def _is_valid_command(cls, input_command: str) -> bool:
        if not cls.is_command_(input_command):
            return False

        command = input_command.strip().lstrip(cls.command_indicator)
        commands = cls._get_commands()
        return command in commands

    @classmethod
    def is_command_(cls, response: str) -> bool:
        command = response.strip()
        return command.startswith(cls.command_indicator)

    @classmethod
    def process_command_(cls, response: str, bots: BotPair) -> str:
        if not cls.is_command_(response):
            return ""

        if not cls._is_valid_command(response):
            return f"Unknown command: {response}"

        command = response.strip()
        found_command = getattr(Commands(), command.lstrip(cls.command_indicator))
        command_response = found_command(bots)
        return command_response + "\n"

    def human1(self, bots: BotPair) -> str:
        human_bot = BotBase.get_human_bot()
        human_bot.system = bots.bot1.system
        human_bot.conversation = bots.bot1.conversation
        human_bot.first_bot = bots.bot1.first_bot
        bots.bot1 = human_bot
        return "Switching bot1 to human..."

    def human2(self, bots: BotPair) -> str:
        human_bot = BotBase.get_human_bot()
        human_bot.system = bots.bot2.system
        human_bot.conversation = bots.bot2.conversation
        human_bot.first_bot = bots.bot2.first_bot
        bots.bot2 = human_bot
        return "Switching bot2 to human..."

    def system1(self, bots: BotPair) -> str:
        return f"Bot 1 system:\n{bots.bot1.system_message()}"

    def system2(self, bots: BotPair) -> str:
        return f"Bot 2 system:\n{bots.bot2.system_message()}"

    def conversation1(self, bots: BotPair) -> str:
        return str(bots.bot1.conversation_without_system)

    def conversation2(self, bots: BotPair) -> str:
        return str(bots.bot2.conversation_without_system)

    def debug1(self, bots: BotPair) -> str:
        bots.bot1.debug = not bots.bot1.debug
        return "Debug mode is now " + ("on" if bots.bot1.debug else "off") + " for bot1."

    def debug2(self, bots: BotPair) -> str:
        bots.bot1.debug = not bots.bot1.debug
        return "Debug mode is now " + ("on" if bots.bot2.debug else "off") + " for bot2."

    def help(self, bots: BotPair) -> str:
        methods = [self.command_indicator + command for command in Commands._get_commands()]
        return "List of user commands:\n" + "\n".join(sorted(methods))

    def quit(self, bots: BotPair) -> str:
        raise typer.Exit()
