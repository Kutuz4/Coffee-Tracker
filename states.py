from aiogram.dispatcher.filters.state import State, StatesGroup


class States(StatesGroup):
    MEETING = State()
    WORK = State()
    NEW_COFFESHOP = State()
    CHOOSE_DRINK = State()
    NEW_DRINK = State()
    NEW_DRINK_NAME = State()
    NEW_DRINK_VOLUME = State()
    NEW_DRINK_PRICE = State()
    ADD_DRINK = State()
    STAT = State()