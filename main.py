from bot import Bot
from client import Client
from events import (on_message, on_raw_reaction_add, on_raw_reaction_remove,
                    on_ready)
from static_data import StaticData

client = Client.get_client()


def main():
    StaticData.load_static_data(initialized=False)
    Bot.load_features()
    Bot.start_tasks()
    Bot.running = True
    client.run(StaticData.get_value('config.bot_token'))


if __name__ == '__main__':
    main()


'''
IDEAS

Command to show values in the static_data json files (but not the config.json values, because bot token)
'''
