import asyncio
import datetime
import time
import traceback

from bot_data_store import BotData
from chat import get_responses
from client import Client
from data_store import Data
from db import DB
from enums import Days, Emoji
from handlers.command_handler import handle_command
from misc import uncapitalize
from user import User

client = Client.get_client()


@client.event
async def on_ready():
    await DB.load_from_disk()
    await client.get_channel(Data.config.debug_channel_id).send('Bot is online!')


@client.event
async def on_message(message):
    # Ignore own messages
    if message.author.id == client.user.id:
        return

    # profanity_present = check_for_profanity(message)
    # If profanity present, either report to mods (if that's enabled) or ignore the message

    if message.guild is None:\
            # For features that are only applicable in DMs
        pass
    else:
        # For features that are only applicable in servers
        pass

        # Do profanity checks here, once implemented. Must be before processing commands

    if len(BotData.convo_subscribers.get(message.author.id, [])) > 0 and \
            message.channel.id in BotData.convo_subscribers[message.author.id]:
        BotData.convo_subscribers[message.author.id][message.channel.id].put_nowait(message)
    else:
        if message.content.startswith(f'!{Data.config.command_word}'):
            await handle_command(message)
        elif message.guild is None:
            # If not sure what else to do with message, and if in DMs, then try to respond intelligently
            responses = get_responses(message.content)
            for response in responses:
                await message.channel.send(response)


@client.event
async def on_raw_reaction_add(reaction):
    # Ignore own reactions
    if reaction.user_id == client.user.id:
        return

    if reaction.guild_id is None:
        # For features that are only applicable in DMs
        await check_if_alarm_was_acknowledged(reaction)
    else:
        # For features that are only applicable in servers
        await handle_pins(reaction)

    # For features that are applicable in both servers and DMs

    # Handle reaction subscribers
    if len(BotData.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in BotData.reaction_subscribers[reaction.user_id]:
            BotData.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'add', 'reaction': reaction})


@client.event
async def on_raw_reaction_remove(reaction):
    # Ignore own reactions
    if reaction.user_id == client.user.id:
        return

    if len(BotData.reaction_subscribers.get(reaction.user_id, [])) > 0:
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if message.id in BotData.reaction_subscribers[reaction.user_id]:
            BotData.reaction_subscribers[reaction.user_id][message.id].put_nowait(
                {'action': 'remove', 'reaction': reaction})


async def timer_task():
    await client.wait_until_ready()
    while True:
        try:
            for user_id, timers in DB.get_all_timers().items():
                timers_to_delete = []
                for timer_name, timer_end in timers.items():
                    if time.time() >= timer_end:
                        await User.send_dm(user_id, f"{Data.phrases.get_timer_message()}\nIt's time to **{uncapitalize(timer_name)}**!")
                        timers_to_delete.append(timer_name)
                for expired_timer_name in timers_to_delete:
                    await DB.delete_timer(user_id, expired_timer_name)
            await asyncio.sleep(1)
        except Exception:
            await client.get_channel(Data.config.debug_channel_id).send(
                f'ERROR: Failure while processing timer tasks: {traceback.format_exc()}')
            await asyncio.sleep(5)


async def alarm_task():
    await client.wait_until_ready()
    while True:
        try:
            now = datetime.datetime.utcnow()
            alarms_to_process = []
            for user_id, alarms in DB.get_all_alarms().items():
                for alarm_name, alarm_data in alarms.items():
                    for day in alarm_data['days']:
                        for alarm_hour, alarm_min in alarm_data['times']:
                            utc_day_min = 60 * alarm_hour + alarm_min - DB.get_utc_time_offset_mins(user_id)
                            while utc_day_min > 60 * 24:
                                utc_day_min -= 60 * 24
                                day += 1
                            while utc_day_min < 0:
                                utc_day_min += 60 * 24
                                day -= 1
                            utc_hour = utc_day_min // 60
                            utc_min = utc_day_min % 60

                            day %= 7

                            recent_alarm_datetime = datetime.datetime(now.year, now.month, now.day, utc_hour, utc_min)
                            while Days.str_to_int(recent_alarm_datetime.strftime('%A')) != day:
                                recent_alarm_datetime -= datetime.timedelta(days=1)

                            # Find out if datetime is from the past 4 hours, and if so queue for processing
                            if recent_alarm_datetime < now and \
                                    recent_alarm_datetime > alarm_data['created_at'] and \
                                    now - recent_alarm_datetime < datetime.timedelta(hours=Data.config.max_alarm_snooze_hours):
                                alarms_to_process.append((user_id, alarm_name, recent_alarm_datetime))

            alarms_to_ring = []
            # Now, narrow down to alarms we actually need to set off
            for user_id, alarm_name, alarm_datetime in alarms_to_process:
                if DB.alarm_is_acknowledged(user_id, alarm_name, alarm_datetime):
                    continue
                last_ring_time = DB.get_ringing_alarm_time(user_id, alarm_name, alarm_datetime)
                if time.time() - last_ring_time < Data.config.alarm_snooze_sec:
                    continue
                alarms_to_ring.append((user_id, alarm_name, alarm_datetime))

            # Set off the alarms
            for user_id, alarm_name, alarm_datetime in alarms_to_ring:
                dm_channel = await User.get_dm_channel(user_id)
                message = await dm_channel.send(f"{Data.phrases.get_timer_message()}\nIt's time to **{uncapitalize(alarm_name)}**!\n\nClick the checkmark to reset the alarm :)")
                await message.add_reaction(Emoji.CHECK_MARK)
                await DB.reset_ringing_alarm_time(user_id, alarm_name, alarm_datetime)
                await DB.add_ringing_alarm_message(user_id, alarm_name, alarm_datetime, message.id)
            await asyncio.sleep(5)
        except Exception:
            await client.get_channel(Data.config.debug_channel_id).send(
                f'ERROR: Failure while processing alarm tasks: ```{traceback.format_exc()}```')
            await asyncio.sleep(5)


async def check_if_alarm_was_acknowledged(reaction):
    if reaction.emoji.name != Emoji.CHECK_MARK:
        return

    channel = await client.fetch_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)

    alarm_tuple = DB.lookup_alarm_from_message(message.id)
    if alarm_tuple is not None and alarm_tuple[0] == reaction.user_id:
        if DB.alarm_is_ringing(*alarm_tuple):
            await DB.acknowledge_alarm(*alarm_tuple)
            await message.remove_reaction(Emoji.CHECK_MARK, client.user)


async def handle_pins(reaction):
    if reaction.emoji.name in [Emoji.PIN, Emoji.X_MARK]:
        # Don't retrieve the message unless it will actually be needed
        channel = await client.fetch_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

    if reaction.emoji.name == Emoji.PIN:
        for msg_reaction in message.reactions:
            if msg_reaction.emoji == Emoji.PIN and msg_reaction.count >= Data.config.pin_threshold:
                await message.pin()
    elif reaction.emoji.name == Emoji.X_MARK and reaction.member.guild_permissions.administrator:
        # Only allow admins to unpin messages
        await message.unpin()
