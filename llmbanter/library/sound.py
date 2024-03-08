import contextlib
import hashlib
import os
import time
from pathlib import Path
from typing import Literal

from loguru import logger
from openai import OpenAI

from llmbanter.library import consts

with contextlib.redirect_stdout(None):
    # https://stackoverflow.com/questions/51464455/how-to-disable-welcome-message-when-importing-pygame
    import pygame


class Sound:
    male_voice1 = "male_voice1"
    male_voice2 = "male_voice2"
    female_voice1 = "female_voice1"
    female_voice2 = "female_voice2"

    @staticmethod
    def openai_voice(voice) -> Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        if voice == "male_voice1":
            return "onyx"
        elif voice == "male_voice2":
            return "echo"
        elif voice == "female_voice1":
            return "shimmer"
        elif voice == "female_voice2":
            return "nova"
        else:
            raise ValueError(f"voice {voice} is not valid")

    @staticmethod
    def _write_tts_mp3(tts_service, voice, text, filepath):
        char_count = len(text)
        # NOTE: AWS is $0.016 per 1,000 input characters for Neural
        # NOTE: AWS is $0.004 per 1,000 input characters for Standard
        # NOTE: OpenAI is $0.015 per 1,000 input characters
        estimated_cost_cents = char_count * 0.015  # TODO: this is OpenAI cost, not AWS Polly
        warn_length = 800  # 250
        if char_count > warn_length:
            msg = f"Text length ({char_count}) exceeds {warn_length} characters, this may result in costly TTS. Press Ctrl-C to cancel."
            logger.warning(msg)
            input(msg)

        if tts_service == "openai":
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            response = client.audio.speech.create(model="tts-1", voice=Sound.openai_voice(voice), input=text)
            response.stream_to_file(filepath)
            return estimated_cost_cents

        else:
            raise ValueError(f"tts_service must be 'aws' or 'openai', not {tts_service=}")

    # TODO: Consider integrating with https://github.com/myshell-ai/openvoice
    # TODO: Consider integrating with https://github.com/Vaibhavs10/insanely-fast-whisper
    @staticmethod
    def to_mp3(
        text: str,
        voice: str,
        bot_name: str,
        tts_service: str = "openai",
        delay_on_cache_hit: float = 0.3,
        cache_folder: str = consts.default_cache_folder_mp3,
    ) -> tuple[Path, float, bool]:
        def get_valid_filename(s):
            s = s.replace(" ", "_").strip()
            return "".join(x for x in s if (x.isalnum() or x in "_-"))

        args = f"{text}-{voice}-{bot_name}"
        args_hash = hashlib.sha256(args.encode()).hexdigest()
        short_text = get_valid_filename(text[0:30].lower().replace(" ", "_").strip())
        filename_hash = f"{bot_name}_{tts_service}_{voice}_{short_text}_{args_hash}.mp3"

        folder = Path(cache_folder)
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / filename_hash

        if filepath.exists():
            time.sleep(delay_on_cache_hit)
            return filepath, 0, True  # Load from cache

        estimated_cost_cents = Sound._write_tts_mp3(tts_service, voice, text, filepath)
        return filepath, estimated_cost_cents, False

    @staticmethod
    def play_mp3(mp3_filepath):
        pygame.mixer.init()
        pygame.mixer.music.load(mp3_filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
