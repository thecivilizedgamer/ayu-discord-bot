import asyncio
import time
import traceback

from client import Client
from misc import uncapitalize
from static_data import StaticData
from user import User

client = Client.get_client()


async def task():
    await client.wait_until_ready()
    while True:
        try:
            for user_id, timers in DB.get_all_timers().items():
                timers_to_delete = []
                for timer_name, timer_end in timers.items():
                    if time.time() >= timer_end:
                        await User.send_dm(user_id, f"{StaticData.get_random_choice('phrases.timer')}\nIt's time to **{uncapitalize(timer_name)}**!")
                        timers_to_delete.append(timer_name)
                for expired_timer_name in timers_to_delete:
                    await DB.delete_timer(user_id, expired_timer_name)
            await asyncio.sleep(1)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failure while processing timer tasks: {traceback.format_exc()}')
            await asyncio.sleep(5)
