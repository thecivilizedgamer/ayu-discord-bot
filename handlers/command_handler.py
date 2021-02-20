"""
Ideas:
    Snooze timers automatically, repeat until acknowledged - just add another timer for 5 min later, and add emoji to react and acknowledge
    Reminders have option of whether they need to be acknowledged
    Filter naughty words
"""

import logging
import traceback

from chat import get_responses
from client import Client
from data_store import Data
from handlers.alarm_handlers import (alarm_command, delete_alarm_command,
                                     list_alarms_command)
from handlers.backup_handlers import (backup_command, list_backups_command,
                                      restore_command)
from handlers.chat_handlers import checkin_command, dm_command, quote_command
from handlers.debug_handlers import debug_command, ping_command, reload_command
from handlers.timer_handlers import (delete_timer_command, list_timers_command,
                                     timer_command)
from misc import remove_trailing_punctuation
from user import User

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

COMMAND_DESCRIPTIONS = {
    "(nothing)":    "Show this help message",
    "ping":         "Check that I\'m listening",
    "timer":        "Set a timer",
    "list timers":  "List all of your timers",
    "delete timer": "Delete an existing timer",
    "alarm":        "Set an alarm",
    "list alarms":  "List all of your alarms",
    "delete alarm": "Delete an existing alarm",
    "quote": "I'll tell you an inspiring quote!",
    "checkin": "I'll ask you how you're doing!"
}


client = Client.get_client()


async def help_command(message, command_arg):
    if command_arg is None:
        max_command_width = max([len(x) for x in COMMAND_DESCRIPTIONS.keys()])

        help_str = ''
        for key in sorted(list(COMMAND_DESCRIPTIONS.keys())):
            description_lines = COMMAND_DESCRIPTIONS[key].split('\n')
            separator = '\n' + ''.join([' ' for _ in range(max_command_width + 2)])
            description_lines = separator.join(description_lines)
            help_str += f'{key:>{max_command_width}}: {description_lines}\n'
        help_str = help_str.rstrip()

        await message.channel.send(
            f"Hi, I'm {Data.config.bot_name}! I'm here to help!\n\n"
            f"Here's what I can do (make sure you say `!{Data.config.command_word}` first!):"
            f"```{help_str}```\n"
            f"If you want to know about a single command, you can say `!{Data.config.command_word} help <command>`\n\n"
            "I've also got a few hidden commands ^-^"
        )
    else:
        command_arg = remove_trailing_punctuation(command_arg).lower()
        if command_arg in command_handlers:
            if command_arg not in COMMAND_DESCRIPTIONS:
                await message.channel.send(
                    "Shhhhhh, that's a secret command!"
                )
            else:
                help_str = f"Here's what you need to know about the `{command_arg}` command!\n\n```" + \
                    COMMAND_DESCRIPTIONS[command_arg] + "```"
                await message.channel.send(help_str)
        else:
            await message.channel.send("I'm sorry, I don't know that command! ^^'")


async def admin_help(message, command_arg):
    normal_commands = ''
    for key in sorted(list(command_handlers.keys())):
        normal_commands += key + '\n'
    normal_commands = normal_commands.rstrip()

    admin_commands = ''
    for key in sorted(list(admin_command_handlers.keys())):
        admin_commands += key + '\n'
    admin_commands = admin_commands.rstrip()

    await message.channel.send(
        'Available normal commands:'
        f'```\n{normal_commands}``` \n'  # Leading newline needed to avoid losing the first line for some reason
        'Available admin commands:'
        f'```\n{admin_commands}```'
    )


command_handlers = {
    'ping': ping_command,
    'help': help_command,
    'dm': dm_command,
    'timer': timer_command,
    'delete': {
        'timer': delete_timer_command,
        'alarm': delete_alarm_command
    },
    'alarm': alarm_command,
    'list': {
        'timers': list_timers_command,
        'alarms': list_alarms_command
    },
    'quote': quote_command,
    'checkin': checkin_command
}

admin_command_handlers = {
    'reload': reload_command,
    'admin': admin_help,
    'debug': debug_command,
    'backup': backup_command,
    'restore': restore_command,
    'list-backups': list_backups_command
}


async def handle_command(message):
    command = message.content.split(f'!{Data.config.command_word}', maxsplit=1)[1].strip()
    command_arg = None
    if len(command) == 0:
        await help_command(message, command_arg)
    else:
        command_segments = command.split(maxsplit=1)
        first_word = remove_trailing_punctuation(command_segments[0]).lower()
        if len(command_segments) > 1:
            command_arg = command_segments[1]

        if first_word in admin_command_handlers and message.author.id == Data.config.owner_user_id:
            await admin_command_handlers[first_word](message, command_arg)
        elif first_word in command_handlers:
            try:
                # Handle nested commands
                val = command_handlers[first_word]
                while isinstance(val, dict):
                    if ' ' in command_arg:
                        next_index, command_arg = command_arg.split(' ', maxsplit=1)
                        next_index = next_index.strip()
                        command_arg = command_arg.strip()
                    else:
                        next_index = command_arg
                        command_arg = None
                    val = val[next_index]
            except:
                await message.channel.send(
                    "Sorry, I don't know how to help with that ^^' "
                    f"if you want to know what I can do, simply type `!{Data.config.command_word}`")
            else:
                try:
                    await val(message, command_arg)
                except Exception:
                    user = await User.get_user(message.author.id)
                    await client.get_channel(Data.config.debug_channel_id).send(
                        f'ERROR: Failed while processing command `{message.content}` from user {user}: ```{traceback.format_exc()}```')
                    await message.channel.send(
                        "I'm sorry, something went wrong! Double-check what you typed and try again?")
        else:
            responses = get_responses(command)
            if len(responses) > 0:
                for response in responses:
                    await message.channel.send(response)
            else:
                await message.channel.send(
                    "Sorry, I don't know how to help with that ^^' "
                    f"if you want to know what I can do, simply type `!{Data.config.command_word}`")
