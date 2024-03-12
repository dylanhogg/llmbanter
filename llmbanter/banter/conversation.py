import hashlib
import json
from datetime import datetime
from pathlib import Path

from loguru import logger
from omegaconf import DictConfig
from rich import print as rprint
from rich.console import Console

from llmbanter.banter.bot_base import BotBase
from llmbanter.banter.bot_pair import BotPair
from llmbanter.library import consts
from llmbanter.library.classes import Response
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

    def _get_conversation_details(self, bots: BotPair) -> tuple[Path, str, str]:
        transcript_header = f"{bots.bot1.filename} '{bots.bot1.name}' {bots.bot1.model}@{bots.bot1.temperature} <-> {bots.bot2.filename} '{bots.bot2.name}' {bots.bot2.model}@{bots.bot2.temperature}"
        hash = hashlib.md5(transcript_header.encode("utf-8")).hexdigest()[0:7]
        folder = Path(f"./{consts.package_name}_conversations/")
        folder.mkdir(parents=True, exist_ok=True)
        filename = (
            folder / f"{datetime.today().strftime('%Y%m%d-%H%M%S')}_"
            f"{bots.bot1.filename}#{bots.bot1.model}@{bots.bot1.temperature}_"
            f"{bots.bot2.filename}#{bots.bot2.model}@{bots.bot2.temperature}_{hash}.txt"
        )
        return filename, hash, transcript_header

    def _respond_to(self, bot: BotBase, other_response: Response, color: str) -> tuple[Response, float, bool]:
        mp3_cost_cents = 0.0
        mp3_from_cache = True
        response = ""

        # Bot responds to text input
        console = Console()
        spinner = "layer"
        if bot.is_human():
            response = bot.respond_to(other_response.chat_response)
        else:
            with console.status(f"[u][white]{bot.display_name}:[/white][/u]", spinner=spinner, spinner_style=color):
                response = bot.respond_to(other_response.chat_response)

        # Log conversation
        if not bot.is_human():
            self._pprint(
                f"[u][white]{bot.display_name}:[/white][/u] "
                f"{RichTerminalFormatter().format_response(response.chat_response, color)}"
            )

        # Play mp3
        if self.speak and not bot.is_human():
            mp3_file, mp3_cost_cents, mp3_from_cache = Sound.to_mp3(response.chat_response, bot.voice, bot.clean_name)
            Sound.play_mp3(mp3_file)

        return response, mp3_cost_cents, mp3_from_cache

    def _pause_input(self, bots: BotPair):
        while True:
            rprint("[i][bright_black]press ↵ to continue conversation...[/bright_black][/i]", end=" ")
            user_input = input("").strip()
            if Commands.is_command_(user_input):
                command_response = Commands.process_command_(user_input, bots)
                self._pprint(command_response)
            else:
                break

    def _log_conversation(self, bots: BotPair, filename: Path):
        with open(filename.with_suffix(".json"), "w") as f:
            # Write serialised bots object
            j = json.dumps(bots, default=lambda o: o.__dict__, sort_keys=True, indent=4)
            f.write(j)

        with open(filename.with_suffix(".txt"), "w") as f:
            # Write readable conversation
            f.write(f"{bots.bot1.name} talking with {bots.bot2.name}\n")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            f.write(f"{bots.bot1}\n")
            f.write(f"{bots.bot2}\n")
            f.write("\n")
            convo_list = [x["role"] + ": " + x["content"] for i, x in enumerate(bots.bot1.conversation_without_system)]
            convo = "\n\n".join(convo_list)
            f.write(convo)
            f.write("\n")

    def start(self):
        if self.model1.startswith("gpt-4") or self.model2.startswith("gpt-4"):
            self._pprint("[red]WARNING: GPT-4 model activated, watch your costs.[/red]")

        bots = self._initialise_bots()
        self._pprint("Conversation set up:")
        self._pprint(f"{bots.bot1=}")
        self._pprint(f"{bots.bot2=}")
        print()
        self._pprint(Commands().help(bots))  # TODO: include a decription with each command
        print()

        i = 1
        response2 = ""
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_chars = 0
        total_mp3_cents = 0

        # Bot1 opener
        # TODO: remove this and replace with bot1.respond_to() to get opener
        response1 = bots.bot1.get_opener()
        self._pprint(f"Conversation:\n[bright_black]{i}.[/bright_black]")
        self._pprint(f"[u][white]{bots.bot1.display_name}:[/white][/u] [cyan2]{response1.chat_response}[/cyan2]")
        if self.speak and not bots.bot1.is_human():
            mp3_file, total_mp3_cents, mp3_from_cache = Sound.to_mp3(
                response1.chat_response, bots.bot1.voice, bots.bot1.clean_name
            )
            Sound.play_mp3(mp3_file)

        # Start conversation
        mp3_from_cache1, mp3_from_cache2 = False, False
        filename, hash, transcript_header = self._get_conversation_details(bots)
        while True:
            i += 1

            # Bot 2 responds to Bot 1 opener
            while True:
                response2, mp3_cost_cents2, mp3_from_cache2 = self._respond_to(bots.bot2, response1, "magenta1")
                if Commands.is_command_(response2.chat_response):
                    command_response = Commands.process_command_(response2.chat_response, bots)
                    self._pprint(command_response)
                else:
                    total_mp3_cents += mp3_cost_cents2
                    break

            self._log_conversation(bots, filename)

            # Debug info
            total_llm_cents = bots.bot1.cost_estimate_cents() + bots.bot2.cost_estimate_cents()
            total_cents = total_mp3_cents + total_llm_cents
            if self.show_costs:
                total_prompt_tokens = bots.bot1.total_prompt_tokens + bots.bot2.total_prompt_tokens
                total_completion_tokens = bots.bot1.total_completion_tokens + bots.bot2.total_completion_tokens
                total_chars = bots.bot1.total_chars + bots.bot2.total_chars
                self._pprint(
                    "[i][bright_black]"
                    f"{total_prompt_tokens=}, {total_completion_tokens=}, {total_chars=}"
                    f", {total_mp3_cents=:.1f}, {total_llm_cents=:.2f}, {total_cents=:.2f}"
                    f", model1={self.model1}, model2={self.model2}"
                    f"{' (llm from cache)' if response1.cache_hit or response2.cache_hit else ''}"
                    f"{' (mp3 from cache)' if self.speak and (mp3_from_cache2 or mp3_from_cache1) else ''}"
                    "[/bright_black][i]"
                )

            # Pause if both bots are non-human
            if not bots.bot1.is_human() and not bots.bot2.is_human():
                self._pause_input(bots)

            print()
            self._pprint(f"[bright_black]{i}.[/bright_black]")

            # Bot 1 responds to Bot 2
            while True:
                response1, mp3_cost_cents1, mp3_from_cache1 = self._respond_to(bots.bot1, response2, "cyan2")
                if Commands.is_command_(response1.chat_response):
                    command_response = Commands.process_command_(response1.chat_response, bots)
                    self._pprint(command_response)
                else:
                    total_mp3_cents += mp3_cost_cents1
                    break

            self._log_conversation(bots, filename)
