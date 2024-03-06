import hashlib
import os
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path

from loguru import logger
from omegaconf import DictConfig
from rich import print as rprint
from rich.console import Console

from llmbanter.bots.bot_base import BotBase
from llmbanter.bots.bot_pair import BotPair
from llmbanter.library.commands import Commands
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

    def _is_valid_command(self, command: str) -> bool:
        command_indicator = "%"
        command = command.strip()
        if not command.startswith(command_indicator):
            return False

        try:
            getattr(Commands(), command.lstrip(command_indicator))
            return True
        except AttributeError:
            return False

    def _process_command(self, command: str, bots: BotPair) -> str:
        if not self._is_valid_command(command):
            return ""

        command_indicator = "%"
        command = command.strip()
        found_command = getattr(Commands(), command.lstrip(command_indicator))
        print(f"XXXX TEMP: Running command: {found_command.__name__=}")
        command_response = found_command(bots)
        return command_response

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
        if not bot.is_human():
            self._pprint(
                f"[u][white]{bot.display_name}:[/white][/u] "
                f"{RichTerminalFormatter().format_response(response, color)}"
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
        # TODO: generate this help from commands.py? or at least manually refresh it.
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

        i = 0
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
                if self._is_valid_command(response1):
                    # TODO: fix missing bot response retry
                    command_response = self._process_command(response1, bots)
                    self._pprint(command_response)
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
                        # f"{' c2' if mp3_from_cache2 else ''}{' c1' if mp3_from_cache1 else ''}[/bright_black]"
                    )

                # Pause if both bots are non-human
                if not bots.bot1.is_human() and not bots.bot2.is_human():
                    while True:
                        user_input = input("...")
                        valid_command = self._is_valid_command(user_input)
                        if not valid_command:
                            break
                        command_response = self._process_command(user_input, bots)
                        self._pprint(command_response)

                print()
                self._pprint(f"[white]{i+1}.[/white]")

                # Bot 1 responds to Bot 2
                if self._is_valid_command(response2):
                    # TODO: fix missing bot response retry
                    command_response = self._process_command(response2, bots)
                    self._pprint(command_response)
                else:
                    i, response1, mp3_cost_cents1, mp3_from_cache1 = self._respond_to(bots.bot1, response2, "cyan2", f)
                    total_mp3_cents += mp3_cost_cents1
