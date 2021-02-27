import asyncio
import datetime
import time
import traceback

from base.feature import BaseFeature
from client import Client
from data import Data
from enums import Days, Emoji
from interface import (get_menu_selections, get_utc_offset_mins, get_yes_no,
                       prompt)
from misc import (get_alarm_description, get_formatted_datetime,
                  get_local_time_from_offset, str_to_time, uncapitalize)
from static_data import StaticData
from user import User

client = Client.get_client()


class AlarmAddFeature(BaseFeature):

    def initialize_feature(self):
        feature_data = Data.get_feature_data('alarm')
        if 'ringing_alarms' not in feature_data:
            feature_data['ringing_alarms'] = {}
        if 'alarm_message_mappings' not in feature_data:
            feature_data['alarm_message_mappings'] = {}
        if 'acknowledged_alarms' not in feature_data:
            feature_data['acknowledged_alarms'] = []

    @staticmethod
    def get_user_alarms(user_id):
        return Data.get_user_data_for_feature(user_id, 'alarm')

    @property
    def feature_name(self):
        return 'alarm-add'

    @property
    def command_keyword(self):
        return 'alarm'

    @property
    def data_access_key(self):
        return 'alarm'

    def get_brief_description(self, user_id, guild_id):
        return 'Set an alarm'

    @property
    def background_tasks(self):
        return [process_alarms]

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        alarm_name = await prompt(message.author.id, message.channel, "What is the alarm for?")
        if alarm_name is None:
            await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
            return
        if alarm_name.lower() in [x.lower() for x in AlarmAddFeature.get_user_alarms(message.author.id).keys()]:
            await message.channel.send(f"You already have an alarm with that name! Check your existing alarms with \"!{StaticData.get_value('config.command_word')} list-alarms\"")
            return

        times = await prompt(message.author.id, message.channel, "What times do you want the alarm to go off? (for example, \"10 AM and 5:30 PM\")")
        if times is None:
            await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
            return

        if times.strip().startswith('at '):
            times = times.strip()[3:]
        time_segments = times.replace('and', '').replace(',', '').split()

        if len(time_segments) % 2 != 0:
            raise RuntimeError('Time args not divisible by 2')

        normalized_times = []
        i = 0
        for _ in range(len(time_segments) // 2):
            hours, mins = str_to_time(time_segments[i], time_segments[i + 1])
            normalized_times.append((hours, mins))
            i += 2

        if Data.get_user_data(message.author.id).get('utc_offset_mins') is None:
            offset_mins = await get_utc_offset_mins(message.author.id, message.channel, message.created_at)
            Data.get_user_data(message.author.id)['utc_offset_mins'] = offset_mins
            await Data.request_save()
        else:
            local_time = get_local_time_from_offset(Data.get_user_data(message.author.id).get('utc_offset_mins'))
            confirmed = await get_yes_no(
                message.author.id,
                message.channel,
                f"Based on what I know, I think your local time is {get_formatted_datetime(local_time)}. Is that right?")
            if confirmed is None:
                await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
                return
            if not confirmed:
                offset_mins = await get_utc_offset_mins(message.author.id, message.channel, message.created_at)
                Data.get_user_data(message.author.id)['utc_offset_mins'] = offset_mins
                await Data.request_save()

        days = await get_menu_selections(
            message.author.id,
            message.channel,
            "What days should the alarm go off? Select the numbers corresponding\n"
            "to the days you want, then select the checkmark when you're done!",
            Days.ordered_days())

        if days is None:
            await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
            return

        # Convert to ints
        days = [Days.str_to_int(x) for x in days]

        alarm_data = {'times': normalized_times, 'days': days, 'created_at': datetime.datetime.utcnow()}

        confirmed = await get_yes_no(
            message.author.id,
            message.channel,
            "I'm setting an alarm for you to " +
            get_alarm_description(uncapitalize(alarm_name), days, normalized_times) +
            "! Does that look right?")

        if confirmed is None:
            await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        elif not confirmed:
            await message.channel.send("Ok, if you still want to set an alarm then ask me again!")
        else:
            await message.channel.send(" All right, you're all set!")
            self.get_user_data(message.author.id)[alarm_name] = alarm_data
            await Data.request_save()


async def process_alarms():
    await client.wait_until_ready()
    while True:
        try:
            now = datetime.datetime.utcnow()
            alarms_to_process = []
            for user_id, user_data in Data.get_all_users_data_for_feature('alarm').items():
                for alarm_name, alarm_data in user_data.items():
                    for day in alarm_data['days']:
                        for alarm_hour, alarm_min in alarm_data['times']:
                            utc_day_min = 60 * alarm_hour + alarm_min - \
                                Data.get_user_data(user_id).get('utc_offset_mins')
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
                                    now - recent_alarm_datetime < datetime.timedelta(hours=StaticData.get_value('config.max_alarm_snooze_hours')):
                                alarms_to_process.append((user_id, alarm_name, recent_alarm_datetime))

            alarms_to_ring = []
            # Now, narrow down to alarms we actually need to set off
            for user_id, alarm_name, alarm_datetime in alarms_to_process:
                if (user_id, alarm_name, alarm_datetime) in Data.get_feature_data('alarm')['acknowledged_alarms']:
                    continue
                last_ring_time = Data.get_feature_data('alarm')['ringing_alarms'].get(
                    (user_id, alarm_name, alarm_datetime), {}).get('last_ring', 0)
                if time.time() - last_ring_time < StaticData.get_value('config.alarm_snooze_sec'):
                    continue
                alarms_to_ring.append((user_id, alarm_name, alarm_datetime))

            # Set off the alarms
            for user_id, alarm_name, alarm_datetime in alarms_to_ring:
                dm_channel = await User.get_dm_channel(user_id)
                message = await dm_channel.send(f"{StaticData.get_value('phrases.timer')}\nIt's time to **{uncapitalize(alarm_name)}**!\n\nClick the checkmark to reset the alarm :)")
                await message.add_reaction(Emoji.CHECK_MARK)

                if (user_id, alarm_name, alarm_datetime) not in Data.get_feature_data('alarm')['ringing_alarms']:
                    Data.get_feature_data('alarm')['ringing_alarms'][(user_id, alarm_name, alarm_datetime)] = {
                        'last_ring': time.time(),
                        'messages': []
                    }
                Data.get_feature_data('alarm')['ringing_alarms'][(
                    user_id, alarm_name, alarm_datetime)]['last_ring'] = time.time()
                await Data.request_save()

                if (user_id, alarm_name, alarm_datetime) not in Data.get_feature_data('alarm')['ringing_alarms']:
                    Data.get_feature_data('alarm')['ringing_alarms'][(user_id, alarm_name, alarm_datetime)] = {
                        'last_ring': time.time(),
                        'messages': []
                    }
                Data.get_feature_data('alarm')['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]['messages'].append(
                    message.id)
                Data.get_feature_data('alarm')['alarm_message_mappings'][message.id] = (
                    user_id, alarm_name, alarm_datetime)
                await Data.request_save()

            await asyncio.sleep(30)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failure while processing alarm tasks: ```{traceback.format_exc()}```')
            await asyncio.sleep(30)


async def remove_old_acknowledged_alarms(user_id, alarm_name, alarm_datetime):
    while True:
        try:
            alarms_to_remove = []
            now = datetime.datetime.utcnow()
            for alarm_id in Data.get_feature_data('alarm')['acknowledged_alarms']:
                if now - alarm_id[2] > datetime.timedelta(hours=StaticData.get_value('config.max_alarm_snooze_hours'), minutes=5):
                    alarms_to_remove.append(alarm_id)
            if len(alarms_to_remove) > 0:
                for alarm_id in alarms_to_remove:
                    Data.get_feature_data('alarm')['ringing_alarms'].remove(alarm_id)
                await Data.request_save()
            await asyncio.sleep(300)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failure while removing acknowledged alarms: ```{traceback.format_exc()}```')
            await asyncio.sleep(300)
