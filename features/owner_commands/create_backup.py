import asyncio
import shutil
import time

from base_feature import BaseFeature
from data import Data


class CreateBackupFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'backup-create'

    @property
    def command_keyword(self):
        return 'create-backup'

    @property
    def owner_only(self):
        return True

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Backup config to a file'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            filename = f'save-{int(time.time())}'
        else:
            filename = arguments.split()[0]
            if filename.lower().endswith('.dmp'):
                filename = filename[:-4]
        # Make sure all pending changes saved
        while Data.save_queue.qsize() > 0:
            await asyncio.sleep(.5)
        shutil.copy('save.dmp', f'{filename}.dmp')
        await message.channel.send(f'Saved backup to {filename}.dmp')
