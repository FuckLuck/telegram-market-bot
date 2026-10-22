from aiogram.fsm.state import State, StatesGroup


class SellStates(StatesGroup):
    waiting_for_ad = State()


class BuyStates(StatesGroup):
    waiting_for_ad_number = State()
