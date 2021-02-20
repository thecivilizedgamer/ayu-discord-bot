import pprint

from data_store import Data
from db import DB


async def reload_command(message, command_arg):
    await message.channel.send('Reloading resources...')
    Data.reload_all()
    await message.channel.send('Finished reloading resources!')


async def debug_command(message, command_arg):
    await message.channel.send(f'```{pprint.pformat(DB.db)}```')


async def ping_command(message, command_arg):
    await message.channel.send(Data.phrases.get_greeting_phrase())
