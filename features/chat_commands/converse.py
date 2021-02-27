from statistics import mean

from base.feature import BaseFeature
from misc import remove_all_punctuation
from static_data import StaticData


class ConverseFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'converse'

    @property
    def dm_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return "Semi-intelligently respond to a message"

    @property
    def can_be_disabled(self):
        return False

    @property
    def on_message_last_callbacks(self):
        return [respond]


async def respond(message):
    cleansed_message_segments = remove_all_punctuation(message.content).lower().split()

    responses = []
    for response_key, triggers in StaticData.get_value('chat.response_map').items():
        for trigger in triggers:
            trigger_words = trigger.split(' ')
            try:
                trigger_indices = [cleansed_message_segments.index(word) for word in trigger_words]
            except ValueError:
                pass
            else:
                if trigger_indices == sorted(trigger_indices):
                    responses.append([mean(trigger_indices), StaticData.get_random_choice(f'phrases.{response_key}')])
                break

    # Sort by average index of where words found, to sort of respond in the same order as the message was composed
    for response in [x[1] for x in sorted(responses, key=lambda x: x[0])]:
        await message.channel.send(response)
