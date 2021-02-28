import random
import re
import time

from base_feature import BaseFeature
from client import Client
from data import Data

RESERVED_VAR_NAMES = ['source', 'bot']


client = Client.get_client()


class TagAddFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'tag-add'

    @property
    def command_keyword(self):
        return 'tag'

    @property
    def data_access_key(self):
        return 'tag'

    @property
    def enable_state_key(self):
        return self.feature_name

    @property
    def admin_only(self):
        return True

    @property
    def server_only(self):
        return True

    @property
    def can_be_disabled(self):
        return False

    def get_brief_description(self, user_id, guild_id):
        return 'Define a custom tag'

    @property
    def feature_hidden(self):
        return True

    async def command_execute(self, message, arguments):
        if arguments is None:
            msg = 'You need to define a tag. Format is "!tag tag | response"\n' \
                'For example, "!tag wave at <person> | <source> waves at <person>" or ' \
                '"!tag hug <a> | <source> hugs <a>"\n' \
                'Variables correspond to mentionable users. Any variable name can be used in the tag, as long as it ' \
                'matches what is used in the response and does not conflict with a builtin variable.\nValid builtin ' \
                'variables in the output are <bot> and <source>, which are mentions of the bot and the messager, ' \
                'respectively.\n' \
                'You can also use something like [phrases.greeting] in the response to choose randomly from a list of values defined in the static_data json files'
            await message.channel.send(msg)
            return
        start = time.time()
        tag, response = arguments.split('|')

        tag = tag.strip()
        response = response.strip()

        server_data = self.get_server_data(message.guild.id)
        if 'tags' not in server_data:
            server_data['tags'] = {}

        # Check if existing tag looks too similar
        genericized = re.sub(r'<[^ ]*?>', r'<>', tag)
        all_genericized = [re.sub(r'<[^ ]?>', r'<>', x) for x in server_data['tags'].keys()]
        if genericized in all_genericized:
            await message.channel.send('Tag looks too similar to an existing tag!')
            return

        tag_vars = []
        stripped_tag = tag
        match = re.search(r'<([^ ]+?)>', stripped_tag)
        while match:
            assert time.time() - start < 10  # Prevent infinite loop
            var_name = match.group(1)
            if var_name in RESERVED_VAR_NAMES:
                await message.channel.send(f'Reserved var name {var_name} cannot be used in tag')
                return
            tag_vars.append(var_name)
            stripped_tag = stripped_tag.replace(f'<{var_name}>', '', 1)
            match = re.search(r'<([^ ]+?)>', stripped_tag)

        response_vars = []
        response_stripped = response
        match = re.search(r'<([^ ]+?)>', response_stripped)
        while match:
            assert time.time() - start < 10  # Prevent infinite loop
            var_name = match.group(1)
            if var_name not in RESERVED_VAR_NAMES:
                response_vars.append(var_name)
            response_stripped = response_stripped.replace(f'<{var_name}>', '', 1)
            match = re.search(r'<([^ ]+?)>', response_stripped)

        for tag_var in tag_vars:
            if tag_var not in response_vars:
                await message.channel.send(f'Tag var {tag_var} is not used in the response')
                return
        for response_var in response_vars:
            if response_var not in tag_vars:
                await message.channel.send(f'Response var {response_var} is not used in the tag')
                return

        server_data['tags'][tag] = (tag_vars, response)
        await Data.request_save()
        await message.channel.send('Successfully saved tag')
