import asyncio
import time
import traceback
from datetime import timedelta

from base_feature import BaseFeature
from client import Client
from data import Data
from interface import prompt
from misc import remove_all_punctuation, seconds_to_string, uncapitalize
from static_data import StaticData
from user import User

client = Client.get_client()


class TimerAddFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'timer-add'

    @property
    def command_keyword(self):
        return 'timer'

    @property
    def data_access_key(self):
        return 'timer'

    def get_brief_description(self, user_id, guild_id):
        return 'Set a timer'

    @property
    def background_tasks(self):
        return [process_timers]

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        timer_name = await prompt(message.author.id, message.channel, "What is the timer for?")
        if timer_name is None:
            await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
            return
        if timer_name.lower() in [x.lower() for x in Data.get_user_data_for_feature(message.author.id, 'timer').keys()]:
            await message.channel.send(f"You already have a timer with that name! Check your existing timers with \"!{StaticData.get_value('config.command_word')} list-timers\"")
            return

        timer_args = await prompt(message.author.id, message.channel, "How soon do you want the timer to go off? For example, \"in 5 hours and 30 min\"")
        if timer_args is None:
            await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
            return

        if timer_args.strip().startswith('in '):
            timer_args = timer_args.strip()[3:]
        timer_args = timer_args.replace('and', '').replace(',', '')
        timer_args = remove_all_punctuation(timer_args).split()
        if len(timer_args) % 2 != 0:
            raise RuntimeError('Timer args not divisible by 2')

        i = 0
        delta = timedelta()
        for _ in range(len(timer_args) // 2):
            val = int(timer_args[i])
            denom = timer_args[i + 1].lower()
            i += 2
            if denom in ['week', 'weeks', 'wks']:
                delta += timedelta(weeks=val)
            elif denom in ['day', 'days']:
                delta += timedelta(days=val)
            elif denom in ['hour', 'hours', 'hr', 'hrs']:
                delta += timedelta(hours=val)
            elif denom in ['minute', 'minutes', 'min', 'mins']:
                delta += timedelta(minutes=val)
            elif denom in ['second', 'seconds', 'sec', 'secs']:
                delta += timedelta(seconds=val)
        end = time.time() + delta.total_seconds()

        Data.get_user_data_for_feature(message.author.id, 'timer')[timer_name] = end
        await Data.request_save()
        remaining_time_str = seconds_to_string(round(end - time.time()))
        await message.channel.send(f"OK, I'll tell you to {uncapitalize(timer_name)} in {remaining_time_str}!")


async def process_timers():
    await client.wait_until_ready()
    while True:
        try:
            for user_id, user_timers in Data.get_all_users_data_for_feature('timer').items():
                timers_to_delete = []
                for timer_name, timer_end in user_timers.items():
                    if time.time() >= timer_end:
                        await User.send_dm(user_id, f"{StaticData.get_random_choice('phrases.timer')}\nIt's time to **{uncapitalize(timer_name)}**!")
                        timers_to_delete.append(timer_name)
                for expired_timer_name in timers_to_delete:
                    mapping = {name.lower(): name for name in user_timers.keys()}
                    actual_name = mapping[expired_timer_name.lower()]
                    if actual_name in user_timers:
                        del user_timers[actual_name]
                    await Data.request_save()
            await asyncio.sleep(1)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failure while processing timer tasks: {traceback.format_exc()}')
            await asyncio.sleep(5)
