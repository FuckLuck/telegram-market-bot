import pytest
from aiogram import Dispatcher
from bot.handlers import routers


def test_routers_registration():
    dp = Dispatcher()
    for router in routers:
        dp.include_router(router)
    assert len(dp.sub_routers) == 3
