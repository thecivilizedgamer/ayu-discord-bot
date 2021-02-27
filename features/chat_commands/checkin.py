from base_feature import BaseFeature
from bot import ConvoSubscription
from interface import get_menu_selections, get_next_response, get_yes_no
from misc import list_to_str, remove_all_punctuation
from static_data import StaticData


class CheckinFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'wellness-check'

    @property
    def command_keyword(self):
        return 'checkin'

    def get_brief_description(self, user_id, guild_id):
        return "Check how you're doing"

    async def command_execute(self, message, arguments):
        await message.channel.send(StaticData.get_random_choice('phrases.checkin'))
        with ConvoSubscription(message.author.id, message.channel.id) as queue:
            response = await get_next_response(queue, timeout_s=120)
            if response is None:
                await message.channel.send("If you don't want to talk right now, that's fine! I'll be right here if you need anything :)")
                return

            emotions_identified = []
            overall_mood = 0
            response_segments = ' '.join(remove_all_punctuation(response).lower().split())
            for emotion, emotion_data in StaticData.get_value('chat.emotion_map').items():
                for keyword in emotion_data['keywords']:
                    if keyword in response_segments:
                        ignore = False
                        for anti_keyword in emotion_data.get('anti-keywords', []):
                            if anti_keyword in response_segments:
                                ignore = True
                        if not ignore:
                            overall_mood += emotion_data['positivity']
                            emotions_identified.append(emotion)
                            break

            need_manual_selection = False

            if len(emotions_identified) > 0:
                feelings = list_to_str([f'**{x}**' for x in emotions_identified])
                await message.channel.send(f"Based on what you said, it sounds like you're feeling {feelings}.")
                correct = await get_yes_no(message.author.id, message.channel, "Is that right?")
                if not correct:
                    await message.channel.send("I'm sorry, I'm only a bot, so I'm not very good at this!")
                    need_manual_selection = True
            else:
                await message.channel.send("I'm sorry, I'm only a bot, so I couldn't tell how you're doing from what you said!")
                need_manual_selection = True

            if need_manual_selection:
                emotions_identified = await get_menu_selections(
                    message.author.id, message.channel,
                    "Can you tell me what you're feeling right now?", list(StaticData.get_value('chat.emotion_map').keys()), timeout_s=120)
                if len(emotions_identified) == 0:
                    await message.channel.send(
                        "It sounds like you're not feeling much of anything right now. That can be good or it can be bad, "
                        "so please take care of yourself! Maybe you can try and find something fun, rewarding or productive to do!")
                    return
                for emotion in emotions_identified:
                    overall_mood += StaticData.get_value(f'chat.emotion_map.{emotion}.positivity')

            if overall_mood > 0:
                await message.channel.send("It seems like you're doing pretty good right now! I'm really glad to hear it!")
            elif overall_mood == 0:
                await message.channel.send("It seems like you're having both ups and downs right now. I hope that things "
                                           "get a little better soon!")
            elif overall_mood > -2:
                await message.channel.send("It sounds like things are rough right now. I'm sorry to hear that :( How about "
                                           "doing something to cheer yourself up?")
            elif overall_mood > -4:
                await message.channel.send("It sounds like things are really bad right now. I'm really sorry you're going "
                                           "through that :( How about reaching out to a friend, and talking to them about it?")
            elif overall_mood > -6:
                await message.channel.send("It sounds like things are terrible right now! If you have anyone you can talk "
                                           "to about it, I really think you should talk to them as soon as you can!")
            else:
                await message.channel.send("It sounds like you really need some help! I'm only a bot, so there's only so "
                                           "much I can do... Please talk to someone as soon as possible!")
