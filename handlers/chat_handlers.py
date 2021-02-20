from data_store import Data
from misc import capitalize
from user import User


async def dm_command(message, command_arg):
    await User.send_dm(message.author.id, Data.phrases.get_dm_message())


async def quote_command(message, command_arg):
    quote, _, author = Data.quotes.get_quote().rpartition(';')
    await message.channel.send(f'"{capitalize(quote)}"\n   -{capitalize(author)}')
