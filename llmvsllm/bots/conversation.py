import hashlib
import os
from datetime import datetime
from pathlib import Path

from loguru import logger
from omegaconf import DictConfig
from rich import print
from rich.console import Console

from llmvsllm.bots.bot_base import BotBase
from llmvsllm.bots.bot_pair import BotPair
from llmvsllm.library.sound import Sound


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
        print(text)
        logger.info(text)

    def _initialise_bots(self):
        return BotPair(self.bot1, self.bot2, self.model1, self.model2, self.temperature1, self.temperature2)

    def _parse_pause_input(self, bots: BotPair):
        if not bots.bot1.is_human() and not bots.bot2.is_human():
            while True:
                pause_input = input("...")  # Pause if both bots are non-human
                # Parse pause input
                if pause_input == "%human1":
                    print("Switching bot1 to human...")
                    human_bot = BotBase.get_human_bot()
                    human_bot.system = bots.bot1.system
                    human_bot.conversation = bots.bot1.conversation
                    human_bot.first_bot = bots.bot1.first_bot
                    bots.bot1 = human_bot
                    break
                elif pause_input == "%human2":
                    print("Switching bot2 to human...")
                    human_bot = BotBase.get_human_bot()
                    human_bot.system = bots.bot2.system
                    human_bot.conversation = bots.bot2.conversation
                    human_bot.first_bot = bots.bot2.first_bot
                    bots.bot2 = human_bot
                    break
                elif pause_input == "%system1":
                    self._pprint(f"Bot 1 system:\n{bots.bot1.augmented_conversation_system()}")
                elif pause_input == "%system1":
                    self._pprint(f"Bot 2 system:\n{bots.bot2.augmented_conversation_system()}")
                else:
                    break

    def _get_conversation_details(self, bots) -> tuple[Path, str, str]:
        transcript_header = f"{bots.bot1.filename} '{bots.bot1.name}' {bots.bot1.model}@{bots.bot1.temperature} <-> {bots.bot2.filename} '{bots.bot2.name}' {bots.bot2.model}@{bots.bot2.temperature}"
        hash = hashlib.md5(transcript_header.encode("utf-8")).hexdigest()[0:7]
        folder = Path("./conversation_transcripts/")
        folder.mkdir(parents=True, exist_ok=True)
        filename = (
            folder
            / f"{bots.bot1.filename}#{bots.bot1.model}@{bots.bot1.temperature}___{bots.bot2.filename}#{bots.bot2.model}@{bots.bot2.temperature}_{hash}_{datetime.today().strftime('%Y%m%d.%H%M%S')}.txt"
        )
        return filename, hash, transcript_header

    def start(self):
        if self.model1.startswith("gpt-4") or self.model2.startswith("gpt-4"):
            self._pprint("[red]WARNING: GPT-4 model activated, watch your costs.[/red]")

        api_key = os.environ.get("OPENAI_API_KEY", None)
        assert api_key, "OPENAI_API_KEY environment variable must be set"

        console = Console()
        spinner = "layer"

        bots = self._initialise_bots()
        self._pprint("Conversation set up:")
        self._pprint(f"{bots.bot1=}")
        self._pprint(f"{bots.bot2=}")
        print()

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
                if bots.bot2.is_human():
                    i, response2 = bots.bot2.respond_to(response1)
                else:
                    with console.status(
                        f"[u][white]{bots.bot2.display_name}:[/white][/u]", spinner=spinner, spinner_style="magenta1"
                    ):
                        i, response2 = bots.bot2.respond_to(response1)

                self._pprint(f"[u][white]{bots.bot2.display_name}:[/white][/u] [magenta1]{response2}[/magenta1]")
                f.write(f"\n{'-'*80}\n{bots.bot2.display_name}: {response2}\n")
                f.flush()
                if self.speak and not bots.bot2.is_human():
                    mp3_file2, estimated_cost_cents2, mp3_from_cache2 = Sound.to_mp3(
                        response2, bots.bot2.voice, bots.bot2.clean_name
                    )
                    Sound.play_mp3(mp3_file2)
                    total_mp3_cents += estimated_cost_cents2

                # Debug info
                total_llm_cents = bots.bot1.cost_estimate_cents() + bots.bot2.cost_estimate_cents()
                total_cents = total_mp3_cents + total_llm_cents
                if self.show_costs:
                    total_prompt_tokens = bots.bot1.total_prompt_tokens + bots.bot2.total_prompt_tokens
                    total_completion_tokens = bots.bot1.total_completion_tokens + bots.bot2.total_completion_tokens
                    total_chars = bots.bot1.total_chars + bots.bot2.total_chars

                    self._pprint(
                        f"[bright_black]({total_prompt_tokens=}, {total_completion_tokens=}, {total_chars=}, "
                        f"{total_mp3_cents=:.1f}, {total_llm_cents=:.2f}, {total_cents=:.2f}) "
                        f"{'*' if mp3_from_cache2 else ''}{'^' if mp3_from_cache1 else ''}[/bright_black]"
                    )

                # Pause if both bots are non-human
                self._parse_pause_input(bots)

                print()
                self._pprint(f"[white]{i+1}.[/white]")

                # Bot 1 responds to Bot 2
                if bots.bot1.is_human():
                    i, response1 = bots.bot1.respond_to(response2)
                else:
                    with console.status(
                        f"[u][white]{bots.bot1.display_name}:[/white][/u]", spinner=spinner, spinner_style="cyan2"
                    ):
                        i, response1 = bots.bot1.respond_to(response2)
                self._pprint(f"[u][white]{bots.bot1.display_name}:[/white][/u] [cyan2]{response1}[/cyan2]")

                f.write(f"\n{'-'*80}\n{bots.bot1.display_name}: {response1}\n")
                f.flush()
                if self.speak and not bots.bot1.is_human():
                    mp3_file1, estimated_cost_cents1, mp3_from_cache1 = Sound.to_mp3(
                        response1, bots.bot1.voice, bots.bot1.clean_name
                    )
                    Sound.play_mp3(mp3_file1)
                    total_mp3_cents += estimated_cost_cents1
