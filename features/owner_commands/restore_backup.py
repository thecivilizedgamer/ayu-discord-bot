import os
import shutil
import time

from base.feature import BaseFeature
from bot import Bot
from data import Data


class RestoreBackupFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'backup-restore'

    @property
    def command_keyword(self):
        return 'restore'

    @property
    def owner_only(self):
        return True

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Restore config from a file'

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
        backup_filename = f'save-{time.time()}.dmp'
        shutil.copy('save.dmp', backup_filename)  # Backup old save file
        await message.channel.send(f'Backed up current save file to {backup_filename}')
        await Data.load_from_disk(filename)
        # Run initialization code for features. Necessary to, for example, fix
        # inconsistencies that may be in data structs
        for feature in Bot.features:
            feature.initialize_feature()
        await message.channel.send(f'Successfully restored backup from {filename}')
