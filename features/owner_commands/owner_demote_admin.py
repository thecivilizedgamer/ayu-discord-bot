from base.feature import BaseFeature
from data import Data


class OwnerDemoteAdminFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'owner-demote-admin'

    @property
    def command_keyword(self):
        return 'owner-demote-admin'

    @property
    def owner_only(self):
        return True

    @property
    def server_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Demote an admin for the current server'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            await message.channel.send(f"You must specify a user to demote (use @ notation)")
            return

        target = arguments.strip()
        if not target.startswith('<@!') or not target.endswith('>'):
            await message.channel.send(f"I'm sorry, that doesn't look like a mentioned user")
        else:
            target = int(target[3:-1])
            administrators = Data.get_server_data(message.guild.id)['administrators']
            if target not in administrators:
                await message.channel.send(f"That user is not an administrator in this server")
            else:
                administrators.remove(target)
                await Data.request_save()
                await message.channel.send(f"Successfully demoted user from administrator")
