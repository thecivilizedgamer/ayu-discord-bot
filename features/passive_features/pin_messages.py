from base_feature import BaseFeature
from client import Client
from data import Data
from enums import Emoji
from static_data import StaticData

client = Client.get_client()


class PinFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'auto-pin'

    @property
    def server_only(self):
        return True

    @property
    def dm_only(self):
        return False

    def get_brief_description(self, user_id, guild_id):
        return f"Automatically pin messages that receive {self.get_server_data(guild_id)['pin_threshold']} or more " \
            ":pushpin: reactions. Admins can unpin using the :x: reaction"

    @property
    def add_reaction_callbacks(self):
        return [handle_pins]


async def handle_pins(reaction):
    if reaction.emoji.name in [Emoji.PIN, Emoji.X_MARK]:
        # Don't retrieve the message unless it will actually be needed
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

    if reaction.emoji.name == Emoji.PIN:
        server_data = Data.get_server_data_for_feature(reaction.guild_id, 'auto-pin')
        if 'pin_threshold' not in server_data:
            server_data['pin_threshold'] = 3
        for msg_reaction in message.reactions:
            if msg_reaction.emoji == Emoji.PIN and msg_reaction.count >= server_data['pin_threshold']:
                await message.pin()
    elif reaction.emoji.name == Emoji.X_MARK and reaction.member.id in Data.get_server_data(reaction.guild_id)['administrators']:
        # Only allow admins to unpin messages
        await message.unpin()
