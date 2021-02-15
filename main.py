from client import Client
from data_store import Data
from db import save_task
from events import alarm_task, timer_task


def main():
    client = Client.get_client()
    client.loop.create_task(timer_task())
    client.loop.create_task(alarm_task())
    client.loop.create_task(save_task())
    client.run(Data.config.bot_token)


if __name__ == '__main__':
    main()
