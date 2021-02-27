import pprint

from base_feature import BaseFeature
from data import Data


class DebugFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'debug-print'

    @property
    def command_keyword(self):
        return 'debug'

    @property
    def owner_only(self):
        return True

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Print debug output'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        await message.channel.send(f'```{pprint.pformat(Data.data)}```')
