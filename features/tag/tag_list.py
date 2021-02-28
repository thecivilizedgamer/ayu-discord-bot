from base_feature import BaseFeature
from client import Client

RESERVED_VAR_NAMES = ['source', 'bot']
TAG_PREFACE = '!'


client = Client.get_client()


class TagListFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'tag-list'

    @property
    def command_keyword(self):
        return 'tags'

    @property
    def data_access_key(self):
        return 'tag'

    @property
    def enable_state_key(self):
        return self.feature_name

    @property
    def server_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'List custom tags for this server'

    async def command_execute(self, message, arguments):
        tags = self.get_server_data(message.guild.id).get('tags', {})

        if len(tags) == 0:
            await message.channel.send('No custom tags defined for this server')
            return

        msg = 'Here are the tags available in this server:\n```'
        for tag, data_tuple in tags.items():
            msg += f'{tag} -> {data_tuple[1]}\n'
        msg = msg.rstrip() + '```'

        await message.channel.send(msg)
