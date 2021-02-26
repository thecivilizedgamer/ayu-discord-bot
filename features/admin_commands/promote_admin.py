from base.feature import BaseFeature
from client import Client
from data import Data

client = Client.get_client()


class PromoteAdminFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'promote-admin'

    @property
    def command_keyword(self):
        return 'promote-admin'

    @property
    def admin_only(self):
        return True

    @property
    def server_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Promote user to admin for the current server'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            await message.channel.send(f"You must specify a user to promote (use @ notation)")
            return

        target = arguments.strip()
        if not target.startswith('<@!') or not target.endswith('>'):
            await message.channel.send(f"I'm sorry, that doesn't look like a mentioned user")
        else:
            target = int(target[3:-1])
            if target == message.author.id:
                await message.channel.send(f"You can't promote yourself, you're already an administrator")
            elif target == client.user.id:
                await message.channel.send(f"You can't promote me!")
            else:
                administrators = Data.get_server_data(message.guild.id)['administrators']
                if target in administrators:
                    await message.channel.send(f"That user is already an administrator in this server")
                else:
                    administrators.append(target)
                    await Data.request_save()
                    await message.channel.send(f"Successfully promoted user to administrator")
