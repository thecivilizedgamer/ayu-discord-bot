from base.feature import BaseFeature
from client import Client
from data import Data
from enums import Emoji

client = Client.get_client()


class AcknowledgeAlarmFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'alarm-acknowledge'

    @property
    def data_access_key(self):
        return 'alarm'

    @property
    def can_be_disabled(self):
        return False

    @property
    def add_reaction_callbacks(self):
        return [check_if_alarm_was_acknowledged]


async def check_if_alarm_was_acknowledged(reaction):
    if reaction.emoji.name != Emoji.CHECK_MARK:
        return

    channel = await client.fetch_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)

    alarm_tuple = lookup_alarm_from_message(message.id)
    if alarm_tuple is not None and alarm_tuple[0] == reaction.user_id:
        if alarm_is_ringing(*alarm_tuple):
            await acknowledge_alarm(*alarm_tuple)
            await message.remove_reaction(Emoji.CHECK_MARK, client.user)


async def acknowledge_alarm(user_id, alarm_name, alarm_datetime):
    alarm_data = Data.get_feature_data('alarm')
    if 'acknowledged_alarms' not in alarm_data:
        alarm_data['acknowledged_alarms'] = []
    if 'ringing_alarms' not in alarm_data:
        alarm_data['ringing_alarms'] = {}
    if 'alarm_message_mappings' not in alarm_data:
        alarm_data['alarm_message_mappings'] = {}
    alarm_data['acknowledged_alarms'].append((user_id, alarm_name, alarm_datetime))
    if (user_id, alarm_name, alarm_datetime) in alarm_data['ringing_alarms']:
        messages = alarm_data['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]['messages']
        del alarm_data['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]
        for message_id in messages:
            del alarm_data['alarm_message_mappings'][message_id]
    await Data.request_save()


def alarm_is_ringing(user_id, alarm_name, alarm_datetime):
    return (user_id, alarm_name, alarm_datetime) in Data.get_feature_data('alarm').get('ringing_alarms', {})


def lookup_alarm_from_message(message_id):
    return Data.get_feature_data('alarm').get('alarm_message_mappings', {}).get(message_id)
