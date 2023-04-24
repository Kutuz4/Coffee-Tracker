from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from datetime import datetime
from states import States
from database import UsersDB, Drink
from utils import DrinkParser, form_inline_keyboard, error_message, IncorrectPrice, IncorrectVolume



class BotHandler:

    def __init__(self, token, database, messages):
        self.database = database
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.current_coffeshops = {}
        self.messages = messages
        self.parser = DrinkParser()

    async def send_message(self, msg, text, reply_markup=None):
        if reply_markup is not None:
            await self.bot.send_message(msg.from_user.id, text, reply_markup=reply_markup)
        else:
            await self.bot.send_message(msg.from_user.id, text)

    async def choose_coffeshop(self, msg):
        await States.WORK.set()
        await self.send_message(msg, self.messages["start"],
                                 reply_markup=form_inline_keyboard("choose_coffeshop", self.database.get_coffeshops(msg.from_user.id) + ["Добавить новую"]))

    async def choose_drink(self, msg: types.Message): 
        await States.CHOOSE_DRINK.set()

        await self.send_message(msg, self.messages["choose_drink"],
                                reply_markup=form_inline_keyboard("choose_drink",
                                                                   self.database.get_drinks(msg.from_user.id, self.current_coffeshops[msg.from_user.id]) + ["Добавить новый", "Вернуться к кофейням"]))
        
    async def track_coffee(self, callback):
        await States.WORK.set()
        await self.database.track_coffee(callback.from_user.id, callback.data.split("__")[-1], self.current_coffeshops[callback.from_user.id])
        response_text = self.messages["stat"].format(self.database[callback.from_user.id].spent)
        await self.send_message(callback, response_text,
                           reply_markup=form_inline_keyboard("choose_coffeshop",
                                                              self.database.get_coffeshops(callback.from_user.id) + ["Добавить новую"]))
        
    async def new_drink_volume(self, msg, is_prob=False, is_error=False):
        await States.NEW_DRINK_VOLUME.set()
        await self.send_message(msg,
                                error_message * int(is_error) + self.messages["new_drink_volume_prob"],
                                reply_markup=form_inline_keyboard("new_drink_volume",
                                                                   [0.2, 0.25, 0.3, 0.4, 0.45, 0.6, "Пропустить"] + ["Это не имя, вернуться"] * int(is_prob)))
        
    async def new_drink(self, callback):
        await States.NEW_DRINK.set()
        await self.send_message(callback, self.messages["new_drink"], 
                                reply_markup=form_inline_keyboard("new_drink", ["Добавить пошагово"]))
        
    
    async def new_coffeshop(self, callback):
        await States.NEW_COFFESHOP.set()
        print("New coffeshop added")
        await self.send_message(callback, self.messages["new_coffeshop"])
        
    async def welcome_handler(self, msg: types.Message):
        self.database.check_user(msg.from_user.id)
        await self.choose_coffeshop(msg)
        
    async def choose_coffeshop_handler(self, callback: types.CallbackQuery, state: FSMContext):
        await self.choose_coffeshop(callback)

    async def handle_coffeshop_handler(self, callback: types.CallbackQuery, state: FSMContext):

        if "Добавить новую" in callback.data:
            await self.new_coffeshop(callback)
        else:
            print(callback.data)

            self.current_coffeshops[callback.from_user.id] = callback.data.split("__")[-1]

            await self.choose_drink(callback)

    async def new_coffeshop_handler(self, msg: types.Message, state: FSMContext):

        await self.database.add_new_coffeshop(msg.from_user.id, msg.text.capitalize())
        await self.choose_coffeshop(msg)

    async def choose_drink_handler(self, callback: types.CallbackQuery, state: FSMContext):

        if "Добавить новый" in callback.data:
            await self.new_drink(callback)
            return None
        
        if "Вернуться к кофейням" not in callback.data:
            await self.track_coffee(callback)
        else:
            await self.choose_coffeshop(callback)
    
    async def new_drink_handler(self, msg: types.Message, state: FSMContext):

        try:
            new_drink = Drink(*self.parser.parse_drink(msg.text))
        except IncorrectVolume:
            await self.send_message(msg, self.messages["new_drink_volume_error"])
        except IncorrectPrice:
            await self.send_message(msg, self.messages["new_drink_price_error"])
        except:
            if "," not in msg.text:
                async with state.proxy() as data:
                    data["name"] = self.parser.parse_name(msg.text)
                await self.new_drink_volume(msg, is_prob=True)
            else:
                await self.send_message(msg, self.messages["new_drink_error"])
            return None
        
        await self.database.add_new_drink(msg.from_user.id, new_drink, self.current_coffeshops[msg.from_user.id])
        await self.choose_drink(msg)


    async def new_drink_steps_handler(self, callback: types.CallbackQuery, state: FSMContext):

        await States.NEW_DRINK_NAME.set()
        await self.send_message(callback, self.messages["new_drink_name"])


    async def new_drink_name_handler(self, msg: types.Message, state: FSMContext):
        print(msg.text, 'name')

        async with state.proxy() as data:
            data["name"] = self.parser.parse_name(msg.text)

        await self.new_drink_volume(msg)


    async def new_drink_volume_handler(self, msg: types.Message, state: FSMContext):
        try:
            volume = self.parser.parse_volume(msg.text)

            async with state.proxy() as data:
                data["volume"] = volume

            await States.NEW_DRINK_PRICE.set()
            await self.send_message(msg, self.messages["new_drink_price"])
        except:
            await self.new_drink_volume(msg, is_prob=False, is_error=True)


    async def new_drink_price_msg_handler(self, msg: types.Message, state: FSMContext):
        price = self.parser.parse_price(msg.text)

        async with state.proxy() as data:
            name, volume, price = data["name"], data["volume"], price
            new_drink = Drink(name, volume, price)

        await self.database.add_new_drink(msg.from_user.id, new_drink, self.current_coffeshops[msg.from_user.id])
        await self.choose_drink(msg)

    
    async def new_drink_volume_keyboard_handler(self, callback: types.CallbackQuery, state: FSMContext):
        volume = callback.data.split("__")[-1]

        if "имя" in volume:
            await States.NEW_DRINK_NAME.set()
            await self.send_message(callback, self.messages["new_drink_name"])

        volume = volume if volume != "Пропустить" else ""

        async with state.proxy() as data:
            data["volume"] = volume

        await States.NEW_DRINK_PRICE.set()
        await self.send_message(callback,
                            self.messages["new_drink_price"])


    def start(self):

        self.dp.register_message_handler(self.welcome_handler, commands=["start"], state="*")

        self.dp.register_callback_query_handler(self.choose_coffeshop_handler,
                                                  lambda c: c.data and c.data.startswith("add_drink"), state=States.WORK)
        
        self.dp.register_callback_query_handler(self.handle_coffeshop_handler, lambda c: c.data and c.data.startswith("choose_coffeshop"), state=States.WORK)

        self.dp.register_message_handler(self.new_coffeshop_handler, state=States.NEW_COFFESHOP)

        self.dp.register_callback_query_handler(self.choose_drink_handler, lambda c: c.data and c.data.startswith("choose_drink"), state=States.CHOOSE_DRINK)

        self.dp.register_message_handler(self.new_drink_handler, state=States.NEW_DRINK)

        self.dp.register_callback_query_handler(self.new_drink_steps_handler, lambda c: c.data and c.data.startswith("new_drink"), state=States.NEW_DRINK)

        self.dp.register_message_handler(self.new_drink_name_handler, state=States.NEW_DRINK_NAME)

        self.dp.register_message_handler(self.new_drink_volume_handler, state=States.NEW_DRINK_VOLUME)

        self.dp.register_message_handler(self.new_drink_price_msg_handler, state=States.NEW_DRINK_PRICE)

        self.dp.register_callback_query_handler(self.new_drink_volume_keyboard_handler,
                                                 lambda c: c.data and c.data.startswith("new_drink_volume"), state=States.NEW_DRINK_VOLUME)
        
        executor.start_polling(self.dp)