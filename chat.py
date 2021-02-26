from statistics import mean

from misc import remove_all_punctuation
from static_data import StaticData


def get_responses(message_str):
    cleansed_message_segments = remove_all_punctuation(message_str).lower().split()

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
    return [x[1] for x in sorted(responses, key=lambda x: x[0])]
