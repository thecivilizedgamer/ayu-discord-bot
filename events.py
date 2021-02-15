import asyncio
import time

from bot_data_store import BotData
from client import Client
from data_store import Data
from db import DB
from handlers.command_handler import handle_command
from misc import uncapitalize
from user import User

client = Client.get_client()


@client.event
async def on_ready():
    await User.send_dm(Data.config.admin_user_id, 'Bot is online!')


@client.event
async def on_message(message):
    # Do profanity checks here, once implemented. Must be first

    if len(BotData.convo_subscribers.get(message.author.id, [])) > 0 and \
            message.channel.id in BotData.convo_subscribers[message.author.id]:
        BotData.convo_subscribers[message.author.id][message.channel.id].put_nowait(message)
    elif message.content.startswith('!ayu'):
        await handle_command(message)


@client.event
async def on_raw_reaction_add(reaction):
    print(reaction.emoji.name.encode())
    if len(BotData.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in BotData.reaction_subscribers[reaction.user_id]:
            BotData.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'add', 'reaction': reaction})


@client.event
async def on_raw_reaction_remove(reaction):
    if len(BotData.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in BotData.reaction_subscribers[reaction.user_id]:
            BotData.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'remove', 'reaction': reaction})


async def timer_task():
    await client.wait_until_ready()
    while True:
        for user_id, timers in DB.get_all_timers().items():
            timers_to_delete = []
            for timer_name, timer_end in timers.items():
                if time.time() >= timer_end:
                    await User.send_dm(user_id, f"{Data.phrases.get_timer_message()}\nIt's time to **{uncapitalize(timer_name)}**!")
                    timers_to_delete.append(timer_name)
            for expired_timer_name in timers_to_delete:
                DB.delete_timer(user_id, expired_timer_name)
        await asyncio.sleep(1)
