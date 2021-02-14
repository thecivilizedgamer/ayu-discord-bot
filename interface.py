import asyncio
import time
from asyncio.queues import QueueEmpty

from bot_data_store import BotData
from click.termui import prompt
from enums import Emoji


async def get_menu_selections(user_id, channel, menu_str, options):
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
    queue = BotData.subscribe_to_message(user_id, message.id)
    for i in range(len(options)):
        await message.add_reaction(emoji_numbers[i])
    await message.add_reaction(Emoji.CHECK)

    selections = []
    start = time.time()
    timed_out = False
    while True:
        try:
            item = queue.get_nowait()
        except QueueEmpty:
            if time.time() - start > 300:
                timed_out = True
                break
            await asyncio.sleep(.25)
        else:
            if item['reaction'].emoji.name == Emoji.CHECK and item['action'] == 'add':
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


async def get_menu_selection(user_id, channel, menu_str, options):
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
    queue = BotData.subscribe_to_message(user_id, message.id)
    for i in range(len(options)):
        await message.add_reaction(emoji_numbers[i])

    selection = None
    start = time.time()
    while True:
        try:
            item = queue.get_nowait()
        except QueueEmpty:
            if time.time() - start > 300:
                break
            await asyncio.sleep(.25)
        else:
            if item['action'] == 'add' and item['reaction'].emoji.name in emoji_numbers:
                number = emoji_numbers.index(item['reaction'].emoji.name)
                if number < len(options):
                    selection = options[number]
                    break
    return selection


async def get_yes_no(user_id, channel, prompt_str):
    message = await channel.send(prompt_str)
    queue = BotData.subscribe_to_message(user_id, message.id)
    await message.add_reaction(Emoji.CHECK)
    await message.add_reaction(Emoji.X)

    response = None
    start = time.time()
    while True:
        try:
            item = queue.get_nowait()
        except QueueEmpty:
            if time.time() - start > 300:
                break
            await asyncio.sleep(.25)
        else:
            if item['action'] == 'add':
                if item['reaction'].emoji.name == Emoji.CHECK:
                    response = True
                    break
                if item['reaction'].emoji.name == Emoji.X:
                    response = False
                    break
    return response
