import typer

from llmbanter.bots.bot_base import BotBase


class Commands:
    def human1(self, bots) -> str:
        human_bot = BotBase.get_human_bot()
        human_bot.system = bots.bot1.system
        human_bot.conversation = bots.bot1.conversation
        human_bot.first_bot = bots.bot1.first_bot
        bots.bot1 = human_bot
        return "Switching bot1 to human..."

    def human2(self, bots) -> str:
        human_bot = BotBase.get_human_bot()
        human_bot.system = bots.bot2.system
        human_bot.conversation = bots.bot2.conversation
        human_bot.first_bot = bots.bot2.first_bot
        bots.bot2 = human_bot
        return "Switching bot2 to human..."

    def system1(self, bots) -> str:
        return f"Bot 1 system:\n{bots.bot1.system_message()}"

    def system2(self, bots) -> str:
        return f"Bot 2 system:\n{bots.bot2.system_message()}"

    def conversation1(self, bots) -> str:
        filtered_conversation = [x for x in bots.bot1.conversation if x["role"] == "user" or x["role"] == "assistant"]
        return str(filtered_conversation)

    def conversation2(self, bots) -> str:
        filtered_conversation = [x for x in bots.bot2.conversation if x["role"] == "user" or x["role"] == "assistant"]
        return str(filtered_conversation)

    def debug1(self, bots) -> str:
        bots.bot1.debug = not bots.bot1.debug
        return "Debug mode is now " + ("on" if bots.bot1.debug else "off") + " for bot1."

    def debug2(self, bots) -> str:
        bots.bot1.debug = not bots.bot1.debug
        return "Debug mode is now " + ("on" if bots.bot2.debug else "off") + " for bot2."

    def help(self, bots) -> str:
        command_indicator = "/"
        methods = [
            command_indicator + method
            for method in dir(Commands)
            if callable(getattr(Commands, method)) and not method.startswith("_")
        ]
        return "List of user commands:\n" + "\n".join(methods)

    def quit(self, bots) -> str:
        raise typer.Exit()
