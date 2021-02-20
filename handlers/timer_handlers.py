import random
import time
from datetime import timedelta

from data_store import Data
from db import DB
from interface import prompt
from misc import (capitalize, remove_all_punctuation, seconds_to_string,
                  uncapitalize)


async def timer_command(message, command_arg):
    timer_name = await prompt(message.author.id, message.channel, "What is the timer for?")
    if timer_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return
    if timer_name.lower() in [x.lower() for x in DB.get_timers(message.author.id).keys()]:
        await message.channel.send(f"You already have a timer with that name! Check your existing timers with \"!{Data.config.command_word} list timers\"")
        return

    timer_args = await prompt(message.author.id, message.channel, "How soon do you want the timer to go off? For example, \"in 5 hours and 30 min\"")
    if timer_args is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return

    if timer_args.strip().startswith('in '):
        timer_args = timer_args.strip()[3:]
    timer_args = timer_args.replace('and', '').replace(',', '')
    timer_args = remove_all_punctuation(timer_args).split()
    if len(timer_args) % 2 != 0:
        raise RuntimeError('Timer args not divisible by 2')

    i = 0
    delta = timedelta()
    for _ in range(len(timer_args) // 2):
        val = int(timer_args[i])
        denom = timer_args[i + 1].lower()
        i += 2
        if denom in ['week', 'weeks', 'wks']:
            delta += timedelta(weeks=val)
        elif denom in ['day', 'days']:
            delta += timedelta(days=val)
        elif denom in ['hour', 'hours', 'hr', 'hrs']:
            delta += timedelta(hours=val)
        elif denom in ['minute', 'minutes', 'min', 'mins']:
            delta += timedelta(minutes=val)
        elif denom in ['second', 'seconds', 'sec', 'secs']:
            delta += timedelta(seconds=val)
    end = time.time() + delta.total_seconds()

    await DB.add_timer(message.author.id, timer_name, end)
    remaining_time_str = seconds_to_string(round(end - time.time()))
    await message.channel.send(f"OK, I'll tell you to {uncapitalize(timer_name)} in {remaining_time_str}!")


async def list_timers_command(message, command_arg):
    timers = DB.get_timers(message.author.id)
    if len(timers) == 0:
        await message.channel.send(f"You don't have any timers right now... But you could make some! Say `!{Data.config.command_word} help timer` to find out how!")
    else:
        msg = ''
        for timer_name, timer_end in timers.items():
            remaining_time = timer_end - time.time()
            if remaining_time <= 0:
                msg += f'{timer_name} right now!\n'
            else:
                remaining_time_str = seconds_to_string(remaining_time)
                msg += f'{capitalize(timer_name)} in {remaining_time_str}\n'
        msg = msg.strip()
        await message.channel.send(f"Here's all of your timers!\n```{msg}```")


async def delete_timer_command(message, command_arg):
    await list_timers_command(message, None)
    random_timer_name = random.choice(list(DB.get_timers(message.author.id).keys()))
    prompt_str = f"Which timer would you like to delete? For example, \"{random_timer_name}\""
    timer_name = await prompt(message.author.id, message.channel, prompt_str)
    if timer_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return
    if timer_name.lower() not in [x.lower() for x in DB.get_timers(message.author.id)]:
        await message.channel.send(f"You don't have a timer for that! Check your current timers with `!{Data.config.command_word} list timers`")
    else:
        await DB.delete_timer(message.author.id, timer_name)
        await message.channel.send(f"Ok, I'll forget about that timer :)")
