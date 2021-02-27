from base.feature import BaseFeature
from data import Data
from misc import capitalize, get_alarm_description


class AlarmListFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'alarm-list'

    @property
    def command_keyword(self):
        return 'list-alarms'

    @property
    def data_access_key(self):
        return 'alarm'

    def get_brief_description(self, user_id, guild_id):
        return 'List your alarms'

    @property
    def background_tasks(self):
        return []

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        alarms = Data.get_user_data_for_feature(message.author.id, 'alarm')
        if len(alarms) == 0:
            await message.channel.send(f"You don't have any alarms set yet!")
        else:
            msg = "Here's the alarms I'm keeping for you!```"
            for alarm_name, alarm_data in alarms.items():
                msg += '\n' + get_alarm_description(capitalize(alarm_name), alarm_data['days'], alarm_data['times'])
            msg += '```'
            await message.channel.send(msg)
