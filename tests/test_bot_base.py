import pytest

from llmbanter.banter.bot_base import BotBase
from llmbanter.library.classes import AppUsageException


def test_get_bot_system0():
    bot = BotBase.get_bot("human")
    print(bot)


def test_get_bot_system1():
    bot = BotBase.get_bot("system/interrogator")
    print(bot)


def test_get_bot_system2():
    bot = BotBase.get_bot("system/jailbreaker")
    print(bot)


def test_get_bot_system3():
    bot = BotBase.get_bot("system/questioner")
    print(bot)


# def test_get_bot_custom1():
#     bot = BotBase.get_bot("evangelist/python_language")
#     print(bot)


def test_get_bot_exception():
    with pytest.raises(AppUsageException):
        bot = BotBase.get_bot("i_dont_exist")
        print(bot)
