from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class DrinkParser:

    def parse_volume(self, volume):
        try:
            volume = volume.strip(" лЛм.")
            volume = float(volume)
            
            if volume > 1:
                volume /= 100
            return volume
        except:
            raise IncorrectVolume
        
    def parse_price(self, price):
        try:
            price = price.strip(" рР.")
            price = float(price)
            return price
        except:
            raise IncorrectPrice
        
    def parse_name(self, name):
        return name.strip().capitalize()
        
    def parse_drink(self, string):
        name, volume, price = string.split(",")

        name = self.parse_name(name)
        volume = self.parse_volume(volume)
        price = self.parse_price(price)

        return name, volume, price

class IncorrectVolume(BaseException):
    pass

class IncorrectPrice(BaseException):
    pass

def form_inline_keyboard(name, buttons_info):
    keyboard = InlineKeyboardMarkup()
    print(buttons_info, name)
    for i in range(len(buttons_info)):
        keyboard.row(InlineKeyboardButton(str(buttons_info[i]), callback_data=name + '__' + str(buttons_info[i])))
        
    return keyboard

error_message = "Я вас не понял :( Кажется, вы ввели что-то не то\n"