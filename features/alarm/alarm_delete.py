import random

from base.feature import BaseFeature
from bot import ConvoSubscription
from data import Data
from interface import get_next_response
from misc import capitalize, get_alarm_description
from static_data import StaticData


class AlarmDeleteFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'alarm-delete'

    @property
    def command_keyword(self):
        return 'delete-alarm'

    @property
    def data_access_key(self):
        return 'alarm'

    def get_brief_description(self, user_id, guild_id):
        return 'Delete an alarm'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        alarms = Data.get_user_data_for_feature(message.author.id, 'alarm').get('alarms', {})
        if len(alarms) == 0:
            await message.channel.send(f"You don't have any alarms for me to delete!")
            return
        with ConvoSubscription(message.author.id, message.channel.id) as queue:
            msg = "Here's the alarms I'm keeping for you!```"
            for alarm_name, alarm_data in alarms.items():
                msg += '\n' + get_alarm_description(capitalize(alarm_name), alarm_data['days'], alarm_data['times'])
            msg += '```'
            await message.channel.send(msg)
            alarm_names = list(alarms.keys())
            random_alarm_name = random.choice(alarm_names)
            await message.channel.send(f"Which alarm would you like to delete? For example, \"{random_alarm_name}\"")
            alarm_name = await get_next_response(queue)
        if alarm_name.lower() not in [x.lower() for x in alarm_names]:
            await message.channel.send(f"You don't have an alarm for that! Check your current alarms with `!{StaticData.get_value('config.command_word')} list-alarms`")
        else:
            await delete_alarm(message.author.id, alarm_name)
            await message.channel.send(f"Ok, I'll forget about that alarm :)")


async def delete_alarm(user_id, alarm_name):
    alarms = Data.get_user_data_for_feature(user_id, 'alarm').get('alarms', {})
    mapping = {name.lower(): name for name in alarms.keys()}
    actual_name = mapping[alarm_name.lower()]
    if actual_name in alarms:
        del alarms[actual_name]
    await Data.request_save()