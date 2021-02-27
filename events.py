import traceback

from bot import Bot
from client import Client
from data import Data
from enums import CallbackResponse
from misc import capitalize, remove_trailing_punctuation
from static_data import StaticData
from user import User

client = Client.get_client()


@client.event
async def on_ready():
    await Data.load_from_disk()
    # Run initialization code for features. Necessary to, for example, fix inconsistencies that may be in data structs
    for feature in Bot.features:
        feature.initialize_feature()
    await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
        f"{capitalize(StaticData.get_value('config.command_word'))} is online!")


@client.event
async def on_message(message):
    # Ignore own messages
    if message.author.id == client.user.id:
        return

    is_dm = message.guild is None
    is_admin = False if is_dm else message.author.id in Data.get_server_data(message.guild.id)['administrators']
    is_owner = message.author.id == StaticData.get_value('config.owner_user_id')

    # PRE-COMMAND ON-MESSAGE CALLBACKS
    if message.guild is None:
        # For features that are only applicable in DMs
        for feature in Bot.get_dm_only_features(is_owner):
            for callback in feature.on_message_first_callbacks:
                if await callback(message) != CallbackResponse.CONTINUE:
                    return
    else:
        # For features that are only applicable in servers
        for feature in Bot.get_server_only_features(message.guild.id, is_admin, is_owner):
            for callback in feature.on_message_first_callbacks:
                if await callback(message) != CallbackResponse.CONTINUE:
                    return

    # For features that are applicable in both servers and DMs
    for feature in Bot.get_global_features(None if message.guild is None else message.guild.id, is_admin, is_owner):
        for callback in feature.on_message_first_callbacks:
            if await callback(message) != CallbackResponse.CONTINUE:
                return

    # If message is part of bot conversation
    if len(Bot.convo_subscribers.get(message.author.id, [])) > 0 and \
            message.channel.id in Bot.convo_subscribers[message.author.id]:
        Bot.convo_subscribers[message.author.id][message.channel.id].put_nowait(message)
    else:
        # Process command
        if message.content.startswith(f"!{StaticData.get_value('config.command_word')}"):
            command = message.content.split(f"!{StaticData.get_value('config.command_word')}", maxsplit=1)[1].strip()
            command_arg = None

            if len(command) == 0:
                await Bot.display_help(message)
            else:
                command_segments = command.split(maxsplit=1)
                first_word = remove_trailing_punctuation(command_segments[0]).lower()
                if len(command_segments) > 1:
                    command_arg = command_segments[1]

                command = Bot.get_available_commands(
                    is_dm, is_admin, is_owner, None if message.guild is None else message.guild.id).get(first_word)

                if command is None:
                    await message.channel.send(
                        "Sorry, I don't know how to help with that! "
                        f"If you want to know what I can do, simply type `!{StaticData.get_value('config.command_word')}`")
                    return
                else:
                    try:
                        if await command.command_execute(message, command_arg) != CallbackResponse.CONTINUE:
                            return
                    except Exception:
                        user = await User.get_user(message.author.id)
                        await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                            f'ERROR: Failed while processing command `{message.content}` from user {user}: ```{traceback.format_exc()}```')
                        await message.channel.send(
                            "I'm sorry, something went wrong! Double-check what you typed and try again?")
                        return

    if message.guild is None:
        # For features that are only applicable in DMs
        for feature in Bot.get_dm_only_features(is_owner):
            for callback in feature.on_message_last_callbacks:
                if await callback(message) != CallbackResponse.CONTINUE:
                    return
    else:
        # For features that are only applicable in servers
        for feature in Bot.get_server_only_features(message.guild.id, is_admin, is_owner):
            for callback in feature.on_message_last_callbacks:
                if await callback(message) != CallbackResponse.CONTINUE:
                    return

    # For features that are applicable in both servers and DMs
    for feature in Bot.get_global_features(None if message.guild is None else message.guild.id, is_admin, is_owner):
        for callback in feature.on_message_last_callbacks:
            if await callback(message) != CallbackResponse.CONTINUE:
                return


@client.event
async def on_raw_reaction_add(reaction):
    # Ignore own reactions
    if reaction.user_id == client.user.id:
        return

    is_dm = reaction.guild_id is None
    is_admin = False if is_dm else reaction.user_id in Data.get_server_data(reaction.guild_id)['administrators']
    is_owner = reaction.user_id == StaticData.get_value('config.owner_user_id')

    if reaction.guild_id is None:
        # For features that are only applicable in DMs
        for feature in Bot.get_dm_only_features(is_owner):
            for callback in feature.add_reaction_callbacks:
                if await callback(reaction) != CallbackResponse.CONTINUE:
                    return
    else:
        # For features that are only applicable in servers
        for feature in Bot.get_server_only_features(reaction.guild_id, is_admin, is_owner):
            for callback in feature.add_reaction_callbacks:
                if await callback(reaction) != CallbackResponse.CONTINUE:
                    return

    # For features that are applicable in both servers and DMs
    for feature in Bot.get_global_features(reaction.guild_id, is_admin, is_owner):
        for callback in feature.add_reaction_callbacks:
            if await callback(reaction) != CallbackResponse.CONTINUE:
                return

    # Handle reaction subscribers
    if len(Bot.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in Bot.reaction_subscribers[reaction.user_id]:
            Bot.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'add', 'reaction': reaction})


@client.event
async def on_raw_reaction_remove(reaction):
    # Ignore own reactions
    if reaction.user_id == client.user.id:
        return

    is_dm = reaction.guild_id is None
    is_admin = False if is_dm else reaction.user_id in Data.get_server_data(reaction.guild_id)['administrators']
    is_owner = reaction.user_id == StaticData.get_value('config.owner_user_id')

    if reaction.guild_id is None:
        # For features that are only applicable in DMs
        for feature in Bot.get_dm_only_features(is_owner):
            for callback in feature.remove_reaction_callbacks:
                if await callback(reaction) != CallbackResponse.CONTINUE:
                    return
    else:
        # For features that are only applicable in servers
        for feature in Bot.get_server_only_features(reaction.guild_id, is_admin, is_owner):
            for callback in feature.remove_reaction_callbacks:
                if await callback(reaction) != CallbackResponse.CONTINUE:
                    return

    # For features that are applicable in both servers and DMs
    for feature in Bot.get_global_features(reaction.guild_id, is_admin, is_owner):
        for callback in feature.remove_reaction_callbacks:
            if await callback(reaction) != CallbackResponse.CONTINUE:
                return

    if len(Bot.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in Bot.reaction_subscribers[reaction.user_id]:
            Bot.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'remove', 'reaction': reaction})
