import pytest

from llmvsllm.bots.bot_base import BotBase
from llmvsllm.library.classes import AppUsageException


def test_get_bot_system1():
    bot = BotBase.get_bot("system/_system_interrogator")
    print(bot)


def test_get_bot_system2():
    bot = BotBase.get_bot("system/_system_jailbreaker")
    print(bot)


def test_get_bot_system3():
    bot = BotBase.get_bot("system/_system_questioner")
    print(bot)


def test_get_bot_custom1():
    bot = BotBase.get_bot("evangelist/python_language")
    print(bot)


def test_get_bot_exception():
    with pytest.raises(AppUsageException):
        bot = BotBase.get_bot("i_dont_exist")
        print(bot)
