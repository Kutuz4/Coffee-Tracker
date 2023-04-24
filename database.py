from utils import *
from datetime import datetime
import pickle
import os


class Drink:

    def __init__(self, name, volume, price):

        self.volume = volume
        self.price = price
        self.name = name
        self.key = f"{self.name}, {self.volume}"
        self.used = 0
        self.used_history = []

    def __str__(self):
        if self.volume != "":
            return f"{self.name}, {self.volume}"
        return self.name
    

class Coffeshop:

    def __init__(self, name):

        self.drinks = {}
        self.name = name
        self.used = 0
        self.used_history = []

    def add_drink(self, drink):
        self.drinks[drink.key] = drink
    
    def get_drink_price(self, key):
        return self.drinks[key].price
    

    def __str__(self):
        return self.name
    
class User:

    def __init__(self):

        self.coffeshops = {}
        self.spent = 0
        self.last_message = None
        self.used_history = []

    async def add_coffeshop(self, coffeshop_name):

        self.coffeshops[coffeshop_name] = Coffeshop(coffeshop_name)

    def get_drinks(self, current_coffeshop):
        return self.coffeshops[current_coffeshop].drinks.values()

    async def add_new_drink(self, drink, current_coffeshop):
        self.coffeshops[current_coffeshop].add_drink(drink)
    
    def track_coffee(self, key, current_coffeshop):
        self.spent += self.coffeshops[current_coffeshop].get_drink_price(key)
        used_time = datetime.now()

        self.coffeshops[current_coffeshop].drinks[key].used_history.append(used_time)
        self.coffeshops[current_coffeshop].used_history.append(used_time)
        self.used_history.append(used_time)

        self.coffeshops[current_coffeshop].drinks[key].used += 1
        self.coffeshops[current_coffeshop].used += 1


class UsersDB:

    def __init__(self, backup_path=None, update_ths=5):
        self.users = {}
        self.to_update_count = 0
        self.backup_path = backup_path
        self.update_ths = update_ths
        if backup_path in os.listdir() and backup_path is not None:
            with open(backup_path, "rb") as f:
                self.users = pickle.load(f)
        print(self.users)

    def check_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User()

    async def do_backup(self):
        with open(self.backup_path, "wb") as f:
            pickle.dump(self.users, f)

    def __contains__(self, key):
        return key in self.users

    def __getitem__(self, key):
        return self.users[key]
    
    def __setitem__(self, key, value):
        self.users[key] = value
    
    def usage_sort(self, list_of_used):
        return sorted(list_of_used, reverse=True, key=lambda x: x.used)

    def get_coffeshops(self, user_id):
        return self.usage_sort(self.users[user_id].coffeshops.values())
    
    def get_drinks(self, user_id, current_coffeshop):
        return self.usage_sort(self.users[user_id].get_drinks(current_coffeshop))
    
    async def add_new_drink(self, user_id, drink, current_coffeshop):
        await self.users[user_id].add_new_drink(drink, current_coffeshop)
        await self.do_backup()

    async def add_new_coffeshop(self, user_id, coffeshop_name):
        await self.users[user_id].add_coffeshop(coffeshop_name)

    async def track_coffee(self, user_id, key, current_coffeshop):
        self.to_update_count += 1
        self.users[user_id].track_coffee(key, current_coffeshop)
        if self.to_update_count >= self.update_ths:
            await self.do_backup()