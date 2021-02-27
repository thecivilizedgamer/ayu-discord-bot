import time

from base_feature import BaseFeature
from data import Data
from misc import capitalize, seconds_to_string


class TimerDeleteFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'timer-list'

    @property
    def command_keyword(self):
        return 'list-timers'

    @property
    def data_access_key(self):
        return 'timer'

    def get_brief_description(self, user_id, guild_id):
        return 'List your timers'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        timers = self.get_user_data(message.author.id)
        if len(timers) == 0:
            await message.channel.send(f"You don't have any timers yet!")
        else:
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
