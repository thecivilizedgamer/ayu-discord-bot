from base_feature import BaseFeature
from client import Client
from data import Data

client = Client.get_client()


class DemoteAdminFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'demote-admin'

    @property
    def command_keyword(self):
        return 'demote-admin'

    @property
    def admin_only(self):
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
            if target == message.author.id:
                await message.channel.send(f"You can't demote yourself!")
            elif target == client.user.id:
                await message.channel.send(f"You can't demote me!")
            else:
                administrators = Data.get_server_data(message.guild.id)['administrators']
                if target not in administrators:
                    await message.channel.send(f"That user is not an administrator in this server")
                else:
                    administrators.remove(target)
                    await Data.request_save()
                    await message.channel.send(f"Successfully demoted user from administrator")
