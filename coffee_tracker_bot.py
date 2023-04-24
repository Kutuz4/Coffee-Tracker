from database import UsersDB
from bot import BotHandler
from json import load
import os


class MainLoop:

    def __init__(self, config_path="config.json"):

        print(os.listdir())

        with open("config.json", "r") as f:
            self.config = load(f)

        self.bot = BotHandler(self.config["token"], UsersDB(self.config["backup_path"]), self.config["messages"])

    def start(self):

        self.bot.start()

if __name__ == "__main__":

    loop = MainLoop()
    loop.start()