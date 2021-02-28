import random
import re
import time
import traceback

from base_feature import BaseFeature
from client import Client
from data import Data
from enums import CallbackResponse
from static_data import StaticData

TAG_PREFACE = '!'


client = Client.get_client()


class TagAddFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'tag-processing'

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
        return 'Respond to custom tags'

    @property
    def on_message_first_callbacks(self):
        return [process_tags]


async def process_tags(message):
    if message.guild is None:
        return CallbackResponse.CONTINUE

    tags = Data.get_server_data_for_feature(message.guild.id, 'tag').get('tags', {})
    if len(tags) == 0:
        return CallbackResponse.CONTINUE

    message_str = message.content.strip()
    if not message_str.startswith(TAG_PREFACE):
        return CallbackResponse.CONTINUE

    start = time.time() + 10000000

    genericized_message = re.sub(r'<@!\d+>', r'<>', message_str[1:])
    for tag, data_tuple in tags.items():
        tag_vars, response = data_tuple
        genericized_tag = re.sub(r'<[^ ]*?>', r'<>', tag)
        if genericized_tag.lower() == genericized_message.lower():
            tag_mentions = []
            match = re.search(r'<(@!\d+)>', message_str)
            while match:
                assert time.time() - start < 10  # Prevent infinite loop
                tag_mentions.append(match.group(1))
                message_str = message_str.replace(match.group(1), '', 1)
                match = re.search(r'<(@!\d+)>', message_str)
            if len(tag_mentions) != len(tag_vars):
                await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                    f'Unexpected failure while processing tag `{tag}` for message `{message.content.strip()}`')
                return CallbackResponse.CONTINUE
            mapping = {tag_vars[i]: tag_mentions[i] for i in range(len(tag_vars))}
            for initial, replacement in mapping.items():
                response = response.replace(f'<{initial}>', f'<{replacement}>')
            response = response.replace('<source>', f'<@!{message.author.id}>')
            response = response.replace('<bot>', f'<@!{client.user.id}>')

            # Replace static data replacements
            match = re.search(r'\[(.+)\]', response)
            while match:
                assert time.time() - start < 10  # Prevent infinite loop
                try:
                    data = StaticData.get_value(match.group(1))
                    if isinstance(data, list):
                        data = random.choice(data)
                    response = response.replace(f'[{match.group(1)}]', data)
                except Exception:
                    await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                        f'Unexpected failure while processing tag `{tag}` for message `{message.content.strip()}`:\n{traceback.format_exc()}')
                    return CallbackResponse.CONTINUE
                match = re.search(r'\[(.+)\]', response)

            await message.channel.send(response)
            return
    return CallbackResponse.CONTINUE
