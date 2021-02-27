from base_feature import BaseFeature
from static_data import StaticData


class PingFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'ping'

    @property
    def command_keyword(self):
        return 'ping'

    def get_brief_description(self, user_id, guild_id):
        return "Check if I'm listening"

    async def command_execute(self, message, arguments):
        await message.channel.send(StaticData.get_random_choice('phrases.greeting'))
