import os

from base_feature import BaseFeature


class ListBackupsFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'backup-list'

    @property
    def command_keyword(self):
        return 'list-backups'

    @property
    def owner_only(self):
        return True

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'List available config backups'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        available_backups = []
        for filename in os.listdir('.'):
            if filename.lower().endswith('.dmp') and filename != 'save.dmp':
                available_backups.append(filename)
        if len(available_backups) > 0:
            available_backups = '\n'.join(available_backups)
            await message.channel.send(f"Available backups:```\n{available_backups}```")
        else:
            await message.channel.send(f"No available backups")
