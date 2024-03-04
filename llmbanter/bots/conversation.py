import hashlib
import os
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path

import typer
from loguru import logger
from omegaconf import DictConfig
from rich import print as rprint
from rich.console import Console

from llmbanter.bots.bot_base import BotBase
from llmbanter.bots.bot_pair import BotPair
from llmbanter.library.format import RichTerminalFormatter
from llmbanter.library.sound import Sound


class Conversation:
    def __init__(
        self,
        config: DictConfig,
        debug: bool = False,
    ):
        self.bot1 = config.bot1
        self.bot2 = config.bot2
        self.model1 = config.model1
        self.model2 = config.model2
        self.temperature1 = config.temperature1
        self.temperature2 = config.temperature2
        self.speak = config.speak
        self.show_costs = config.show_costs
        self.debug = debug

    def _pprint(self, text: str):
        rprint(text)
        logger.info(text)

    def _initialise_bots(self) -> BotPair:
        return BotPair(self.bot1, self.bot2, self.model1, self.model2, self.temperature1, self.temperature2)

    def _process_command(self, command: str, bots: BotPair) -> str:  # noqa: C901
        command = command.strip()
        while True:
            # Parse pause input
            if command == "%human1":
                human_bot = BotBase.get_human_bot()
                human_bot.system = bots.bot1.system
                human_bot.conversation = bots.bot1.conversation
                human_bot.first_bot = bots.bot1.first_bot
                bots.bot1 = human_bot
                return "Switching bot1 to human..."
            elif command == "%human2":
                human_bot = BotBase.get_human_bot()
                human_bot.system = bots.bot2.system
                human_bot.conversation = bots.bot2.conversation
                human_bot.first_bot = bots.bot2.first_bot
                bots.bot2 = human_bot
                return "Switching bot2 to human..."
            elif command == "%system1":
                return f"Bot 1 system:\n{bots.bot1.system_message()}"
            elif command == "%system2":
                return f"Bot 2 system:\n{bots.bot2.system_message()}"
            elif command == "%conversation1":
                filtered_conversation = [
                    x for x in bots.bot1.conversation if x["role"] == "user" or x["role"] == "assistant"
                ]
                return str(filtered_conversation)
            elif command == "%sconversation2":
                filtered_conversation = [
                    x for x in bots.bot2.conversation if x["role"] == "user" or x["role"] == "assistant"
                ]
                return str(filtered_conversation)
            elif command == "%debug1":
                bots.bot1.debug = not bots.bot1.debug
                return "Debug mode is now " + ("on" if bots.bot1.debug else "off") + " for bot1."
            elif command == "%debug2":
                bots.bot1.debug = not bots.bot1.debug
                return "Debug mode is now " + ("on" if bots.bot2.debug else "off") + " for bot2."
            elif command == "%quit" or command == "%q":
                self._pprint("Quitting...")
                raise typer.Exit()
            elif command.startswith("%"):
                return f"Unknown command: {command}"
            else:
                # break
                return ""

    def _get_conversation_details(self, bots: BotPair) -> tuple[Path, str, str]:
        transcript_header = f"{bots.bot1.filename} '{bots.bot1.name}' {bots.bot1.model}@{bots.bot1.temperature} <-> {bots.bot2.filename} '{bots.bot2.name}' {bots.bot2.model}@{bots.bot2.temperature}"
        hash = hashlib.md5(transcript_header.encode("utf-8")).hexdigest()[0:7]
        folder = Path("./conversation_transcripts/")
        folder.mkdir(parents=True, exist_ok=True)
        filename = (
            folder
            / f"{bots.bot1.filename}#{bots.bot1.model}@{bots.bot1.temperature}___{bots.bot2.filename}#{bots.bot2.model}@{bots.bot2.temperature}_{hash}_{datetime.today().strftime('%Y%m%d.%H%M%S')}.txt"
        )
        return filename, hash, transcript_header

    def _respond_to(self, bot: BotBase, text_input: str, color: str, f: TextIOWrapper) -> tuple[int, str, float, bool]:
        mp3_cost_cents = 0.0
        mp3_from_cache = True
        response = ""
        i = bot.i

        # TODO: actually need to bring _process_command() back here to redo input for real user response!

        # Bot responds to text input
        console = Console()
        spinner = "layer"
        if bot.is_human():
            i, response = bot.respond_to(text_input)
        else:
            with console.status(f"[u][white]{bot.display_name}:[/white][/u]", spinner=spinner, spinner_style=color):
                i, response = bot.respond_to(text_input)

        # Log conversation
        self._pprint(
            f"[u][white]{bot.display_name}:[/white][/u] " f"{RichTerminalFormatter().format_response(response, color)}"
        )
        f.write(f"\n{'-'*80}\n{bot.display_name}: {response}\n")
        f.flush()

        # Play mp3
        if self.speak and not bot.is_human():
            mp3_file, mp3_cost_cents, mp3_from_cache = Sound.to_mp3(response, bot.voice, bot.clean_name)
            Sound.play_mp3(mp3_file)

        return i, response, mp3_cost_cents, mp3_from_cache

    def start(self):
        if self.model1.startswith("gpt-4") or self.model2.startswith("gpt-4"):
            self._pprint("[red]WARNING: GPT-4 model activated, watch your costs.[/red]")

        api_key = os.environ.get("OPENAI_API_KEY", None)
        assert api_key, "OPENAI_API_KEY environment variable must be set"

        bots = self._initialise_bots()
        self._pprint("Conversation set up:")
        self._pprint(f"{bots.bot1=}")
        self._pprint(f"{bots.bot2=}")
        print()
        self._pprint("Available commands:")
        self._pprint("'%human1': Switch bot1 to human input")
        self._pprint("'%human2': Switch bot2 to human input")
        self._pprint("'%system1': Show bot1 system setup")
        self._pprint("'%system2': Show bot2 system setup")
        self._pprint("'%debug': Debug mode on/off")
        self._pprint("'%system_conversation': Show system setup and conversation transcript")
        self._pprint("'%conversation': Show conversation transcript")
        self._pprint("'%quit' or '%q': Quit conversation")
        print()

        # i = 0
        response2 = ""
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_chars = 0
        total_mp3_cents = 0

        # Bot1 opener
        response1 = bots.bot1.get_opener()
        self._pprint("Conversation:\n[white]1.[/white]")
        self._pprint(f"[u][white]{bots.bot1.display_name} (opener):[/white][/u] [cyan2]{response1}[/cyan2]")
        if self.speak and not bots.bot1.is_human():
            mp3_file, total_mp3_cents, mp3_from_cache = Sound.to_mp3(response1, bots.bot1.voice, bots.bot1.clean_name)
            Sound.play_mp3(mp3_file)

        # Start conversation
        mp3_from_cache1, mp3_from_cache2 = False, False
        filename, hash, transcript_header = self._get_conversation_details(bots)
        with open(filename, "w") as f:
            f.write(f"Conversation {datetime.today().strftime('%Y-%m-%d %H:%M:%S')} @{hash}\n")
            f.write(f"{transcript_header}\n")
            while True:
                # Bot 2 responds to Bot 1 opener
                command_reponse = self._process_command(response1, bots)
                if command_reponse:
                    self._pprint(command_reponse)
                else:
                    i, response2, mp3_cost_cents2, mp3_from_cache2 = self._respond_to(
                        bots.bot2, response1, "magenta1", f
                    )
                    total_mp3_cents += mp3_cost_cents2

                # Debug info
                total_llm_cents = bots.bot1.cost_estimate_cents() + bots.bot2.cost_estimate_cents()
                total_cents = total_mp3_cents + total_llm_cents
                if self.show_costs:
                    total_prompt_tokens = bots.bot1.total_prompt_tokens + bots.bot2.total_prompt_tokens
                    total_completion_tokens = bots.bot1.total_completion_tokens + bots.bot2.total_completion_tokens
                    total_chars = bots.bot1.total_chars + bots.bot2.total_chars

                    self._pprint(
                        f"[bright_black]({total_prompt_tokens=}, {total_completion_tokens=}, {total_chars=}, "
                        f"{total_mp3_cents=:.1f}, {total_llm_cents=:.2f}, {total_cents=:.2f})"
                        f"{' c2' if mp3_from_cache2 else ''}{' c1' if mp3_from_cache1 else ''}[/bright_black]"
                    )

                # Pause if both bots are non-human
                if not bots.bot1.is_human() and not bots.bot2.is_human():
                    command = input("...")  # Pause if both bots are non-human
                    command_response = self._process_command(command, bots)
                    if command_response:
                        self._pprint(command_response)

                print()
                self._pprint(f"[white]{i+1}.[/white]")

                # Bot 1 responds to Bot 2
                command_reponse = self._process_command(response2, bots)
                if command_reponse:
                    self._pprint(command_reponse)
                else:
                    i, response1, mp3_cost_cents1, mp3_from_cache1 = self._respond_to(bots.bot1, response2, "cyan2", f)
                    total_mp3_cents += mp3_cost_cents1
