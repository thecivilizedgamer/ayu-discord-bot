from base_feature import BaseFeature
from data import Data


class OwnerListAdminsFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'owner-list-admins'

    @property
    def command_keyword(self):
        return 'owner-list-admins'

    @property
    def owner_only(self):
        return True

    @property
    def server_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'List admins for the current server'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        administrators = Data.get_server_data(message.guild.id)['administrators']
        if len(administrators) == 0:
            await message.channel.send('There are no administrators defined for this server yet')
        else:
            msg = 'Administrators defined for this server:\n'
            for user_id in administrators:
                msg += f'<@!{user_id}>\n'
            await message.channel.send(msg.rstrip())
