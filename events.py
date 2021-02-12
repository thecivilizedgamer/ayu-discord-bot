import asyncio
import time

from client import Client
from data_store import Data
from handlers.command_handler import handle_command
from misc import uncapitalize
from user import User
from user_data_store import UserData

client = Client.get_client()


@client.event
async def on_ready():
    await User.send_dm(Data.config.admin_user_id, 'Bot is online!')


@client.event
async def on_message(message):
    if message.content.startswith('!ayu'):
        await handle_command(message)


async def timer_task():
    await client.wait_until_ready()
    while True:
        for user_id, timers in UserData.timers.items():
            timers_to_delete = []
            for timer_name, timer_end in timers.items():
                if time.time() >= timer_end:
                    await User.send_dm(user_id, f"{Data.phrases.get_timer_message()}\nIt's time to **{uncapitalize(timer_name)}**!")
                    timers_to_delete.append(timer_name)
            for expired_timer_name in timers_to_delete:
                UserData.delete_timer(user_id, expired_timer_name)
        await asyncio.sleep(1)
