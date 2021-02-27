import random
import time

from base_feature import BaseFeature
from data import Data
from interface import prompt
from misc import capitalize, seconds_to_string


class TimerDeleteFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'timer-delete'

    @property
    def command_keyword(self):
        return 'delete-timer'

    @property
    def data_access_key(self):
        return 'timer'

    def get_brief_description(self, user_id, guild_id):
        return 'Delete a timer'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        timers = Data.get_user_data_for_feature(message.author.id, 'timer')
        if len(timers) == 0:
            await message.channel.send(f"You don't have any timers for me to delete!")
            return

        # List timers
        msg = ''
        for timer_name, timer_end in timers.items():
            remaining_time = timer_end - time.time()
            if remaining_time <= 0:
                msg += f'{timer_name} right now!\n'
            else:
                remaining_time_str = seconds_to_string(remaining_time)
                msg += f'{capitalize(timer_name)} in {remaining_time_str}\n'
        msg = msg.strip()
        await message.channel.send(f"Here's all of your timers!\n```{msg}```")

        random_timer_name = random.choice(list(timers.keys()))
        prompt_str = f"Which timer would you like to delete? For example, \"{random_timer_name}\""
        timer_name = await prompt(message.author.id, message.channel, prompt_str)
        if timer_name is None:
            await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
            return
        if timer_name.lower() not in [x.lower() for x in timers]:
            await message.channel.send(f"You don't have a timer for that!")
        else:
            mapping = {name.lower(): name for name in timers.keys()}
            del timers[mapping[timer_name.lower()]]
            await Data.request_save()

            await message.channel.send(f"Ok, I'll forget about that timer :)")
