from base.feature import BaseFeature
from client import Client
from data import Data
from enums import Emoji

client = Client.get_client()


class AddAlarmFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'alarm-add'

    @property
    def server_only(self):
        return False

    @property
    def data_access_key(self):
        return 'alarm'

    @property
    def dm_only(self):
        return False

    @property
    def get_brief_description(self, user_id, guild_id):
        return 'Add an alarm'

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
        if DB.alarm_is_ringing(*alarm_tuple):
            await DB.acknowledge_alarm(*alarm_tuple)
            await message.remove_reaction(Emoji.CHECK_MARK, client.user)


def lookup_alarm_from_message(message_id):
    return Data.data['alarm']['alarm_message_mappings'].get(message_id)


def get_utc_time_offset_mins(user_id):
    return Data.data['alarm'][user_id].get('utc_offset_mins')


async def set_utc_time_offset_mins(user_id, utc_offset):
    DB.ensure_user_id(user_id)
    DB.db[user_id]['utc_offset_mins'] = utc_offset
    await DB.request_save()
