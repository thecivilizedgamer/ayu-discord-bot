from client import Client
from data_store import Data
from events import timer_task


def main():
    client = Client.get_client()
    client.loop.create_task(timer_task())
    client.run(Data.config.bot_token)


if __name__ == '__main__':
    main()
