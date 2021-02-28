import asyncio

from base_feature import BaseFeature
from data import Data


class ImmediateSaveFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'immediate-save'

    @property
    def command_keyword(self):
        return 'save-now'

    @property
    def owner_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Perform immediate save'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        await Data.request_save()
        await message.channel.send('Please wait while a save is performed...')
        while Data.save_queue.qsize() > 0:
            await asyncio.sleep(1)
        await message.channel.send('Save complete!')
