import asyncio
import datetime
import time
from asyncio.queues import QueueEmpty

from bot_data_store import ConvoSubscription, ReactionSubscription
from enums import Emoji
from misc import month_str_to_number, remove_all_punctuation, str_to_time


async def get_next_response(subscriber_queue, timeout_s=60):
    start = time.time()
    while True:
        try:
            response = subscriber_queue.get_nowait()
        except QueueEmpty:
            if time.time() - start > timeout_s:
                break
            await asyncio.sleep(.25)
        else:
            return response.content
    return None


async def prompt(user_id, channel, prompt_str, timeout_s=60):
    with ConvoSubscription(user_id, channel.id) as queue:
        await channel.send(prompt_str)
        response = await get_next_response(queue, timeout_s=timeout_s)
    return response


async def get_menu_selections(user_id, channel, menu_str, options, timeout_s=60):
    if len(options) > 9:
        raise RuntimeError("Can't have more than 9 menu options")

    emoji_numbers = [Emoji.ONE,
                     Emoji.TWO,
                     Emoji.THREE,
                     Emoji.FOUR,
                     Emoji.FIVE,
                     Emoji.SIX,
                     Emoji.SEVEN,
                     Emoji.EIGHT,
                     Emoji.NINE]

    menu_str += '```'
    for i, option in enumerate(options):
        menu_str += f'\n   {i + 1}. {option}'
    menu_str += '```'

    message = await channel.send(menu_str)
    with ReactionSubscription(user_id, message.id) as queue:
        for i in range(len(options)):
            await message.add_reaction(emoji_numbers[i])
        await message.add_reaction(Emoji.CHECK_MARK)

        selections = []
        start = time.time()
        timed_out = False
        while True:
            try:
                item = queue.get_nowait()
            except QueueEmpty:
                if time.time() - start > timeout_s:
                    timed_out = True
                    break
                await asyncio.sleep(.25)
            else:
                if item['reaction'].emoji.name == Emoji.CHECK_MARK and item['action'] == 'add':
                    break
                else:
                    if item['reaction'].emoji.name in emoji_numbers:
                        number = emoji_numbers.index(item['reaction'].emoji.name)
                        if number < len(options):
                            option = options[number]
                            if item['action'] == 'add' and option not in selections:
                                selections.append(option)
                            if item['action'] == 'remove' and option in selections:
                                selections.remove(option)
    if timed_out:
        return None
    return selections


async def get_menu_selection(user_id, channel, menu_str, options, timeout_s=60):
    if len(options) > 9:
        raise RuntimeError("Can't have more than 9 menu options")

    emoji_numbers = [Emoji.ONE,
                     Emoji.TWO,
                     Emoji.THREE,
                     Emoji.FOUR,
                     Emoji.FIVE,
                     Emoji.SIX,
                     Emoji.SEVEN,
                     Emoji.EIGHT,
                     Emoji.NINE]

    menu_str += '```'
    for i, option in enumerate(options):
        menu_str += f'\n   {i + 1}. {option}'
    menu_str += '```'
    message = await channel.send(menu_str)
    with ReactionSubscription(user_id, message.id) as queue:
        for i in range(len(options)):
            await message.add_reaction(emoji_numbers[i])

        selection = None
        start = time.time()
        while True:
            try:
                item = queue.get_nowait()
            except QueueEmpty:
                if time.time() - start > timeout_s:
                    break
                await asyncio.sleep(.25)
            else:
                if item['action'] == 'add' and item['reaction'].emoji.name in emoji_numbers:
                    number = emoji_numbers.index(item['reaction'].emoji.name)
                    if number < len(options):
                        selection = options[number]
                        break
    return selection


async def get_yes_no(user_id, channel, prompt_str, timeout_s=60):
    message = await channel.send(prompt_str)
    with ReactionSubscription(user_id, message.id) as queue:
        await message.add_reaction(Emoji.CHECK_MARK)
        await message.add_reaction(Emoji.X_MARK)

        response = None
        start = time.time()
        while True:
            try:
                item = queue.get_nowait()
            except QueueEmpty:
                if time.time() - start > timeout_s:
                    break
                await asyncio.sleep(.25)
            else:
                if item['action'] == 'add':
                    if item['reaction'].emoji.name == Emoji.CHECK_MARK:
                        response = True
                        break
                    if item['reaction'].emoji.name == Emoji.X_MARK:
                        response = False
                        break
    return response


async def get_utc_offset_mins(user_id, channel, message_time):
    local_time = await prompt(user_id, channel, "What's your current local "
                              "time? For example, 3:05 PM. This is the only time I'll ask!")
    if local_time is None:
        await channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return
    local_hours, local_mins = str_to_time(local_time)

    local_date = await prompt(user_id, channel, "And what's today's date? For example, \"Jan 19, 2021\"")
    if local_date is None:
        await channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return

    month, day, year = remove_all_punctuation(local_date).split()
    if len(year) < 4:
        raise RuntimeError('Year must be 4 digits')

    month = month_str_to_number(month)

    local_time = datetime.datetime(int(year), month, int(day), local_hours, local_mins)
    offset_mins = (local_time - message_time).total_seconds() / 60

    # Round offset minutes to the nearest 15 min, since some timezones have
    # weird 15-min offsets due to DST
    offset_mins = 15 * round(offset_mins / 15)

    expected_local_time = message_time + datetime.timedelta(minutes=offset_mins)
    disparity_mins = (expected_local_time - local_time).total_seconds() / 15
    if disparity_mins > 5:  # If off by more than 5 min, something must be wrong with the calculation
        raise RuntimeError('Failed to infer correct UTC time offset')

    return offset_mins
