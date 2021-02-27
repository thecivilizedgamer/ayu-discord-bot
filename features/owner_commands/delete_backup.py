import os
import shutil
import time

from base_feature import BaseFeature
from bot import Bot
from data import Data


class RestoreBackupFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'backup-delete'

    @property
    def command_keyword(self):
        return 'delete-backup'

    @property
    def owner_only(self):
        return True

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Delete backup config'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            await message.channel.send('Must specify a backup file. Use `list-backups` to see available backups')
            return
        filename = arguments.split()[0]
        if not filename.endswith('.dmp'):
            filename += '.dmp'
        if not os.path.isfile(filename):
            await message.channel.send(f'File {filename} does not exist')
            return
        os.remove(filename)
        await message.channel.send(f'Successfully deleted backup {filename}')
