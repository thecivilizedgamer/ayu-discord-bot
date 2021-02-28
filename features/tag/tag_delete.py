
from base_feature import BaseFeature
from client import Client
from data import Data
from interface import prompt

RESERVED_VAR_NAMES = ['source', 'bot']
TAG_PREFACE = '!'


client = Client.get_client()


class TagDeleteFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'tag-delete'

    @property
    def command_keyword(self):
        return 'delete-tag'

    @property
    def data_access_key(self):
        return 'tag'

    @property
    def enable_state_key(self):
        return self.feature_name

    @property
    def server_only(self):
        return True

    @property
    def admin_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Delete a custom tag'

    @property
    def can_be_disabled(self):
        return False

    @property
    def feature_hidden(self):
        return True

    async def command_execute(self, message, arguments):
        tags = self.get_server_data(message.guild.id).get('tags', {})

        if len(tags) == 0:
            await message.channel.send('No custom tags defined for this server')
            return

        msg = 'Here are the tags available in this server:\n```'
        i = 1

        tag_keys = list(tags.keys())

        for i, tag, in enumerate(tag_keys):
            msg += f'{i + 1}. {tag} -> {tags[tag_keys[i]][1]}\n'
        msg = msg.rstrip() + '```'
        msg += 'Which tag would you like to delete? Enter the number.'
        tag_to_delete = await prompt(message.author.id, message.channel, msg)
        if tag_to_delete is None:
            await message.channel.send('I got tired of waiting for you to respond! If you still want to delete a tag, then use the command again!')
            return

        try:
            del tags[tag_keys[int(tag_to_delete) - 1]]
            await Data.request_save()
        except Exception:
            await message.channel.send('Hmmm, something went wrong. Did you type in a number corresponding to one of the tags?')
        else:
            await message.channel.send('Successfully deleted tag')
