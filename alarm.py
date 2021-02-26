import asyncio
import datetime
import time
import traceback

from client import Client
from enums import Days, Emoji
from misc import uncapitalize
from static_data import StaticData
from user import User

client = Client.get_client()


async def task():
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
                                    now - recent_alarm_datetime < datetime.timedelta(hours=StaticData.get_value('config.max_alarm_snooze_hours')):
                                alarms_to_process.append((user_id, alarm_name, recent_alarm_datetime))

            alarms_to_ring = []
            # Now, narrow down to alarms we actually need to set off
            for user_id, alarm_name, alarm_datetime in alarms_to_process:
                if DB.alarm_is_acknowledged(user_id, alarm_name, alarm_datetime):
                    continue
                last_ring_time = DB.get_ringing_alarm_time(user_id, alarm_name, alarm_datetime)
                if time.time() - last_ring_time < StaticData.get_value('config.alarm_snooze_sec'):
                    continue
                alarms_to_ring.append((user_id, alarm_name, alarm_datetime))

            # Set off the alarms
            for user_id, alarm_name, alarm_datetime in alarms_to_ring:
                dm_channel = await User.get_dm_channel(user_id)
                message = await dm_channel.send(f"{StaticData.get_value('phrases.timer')}\nIt's time to **{uncapitalize(alarm_name)}**!\n\nClick the checkmark to reset the alarm :)")
                await message.add_reaction(Emoji.CHECK_MARK)
                await DB.reset_ringing_alarm_time(user_id, alarm_name, alarm_datetime)
                await DB.add_ringing_alarm_message(user_id, alarm_name, alarm_datetime, message.id)
            await asyncio.sleep(5)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failure while processing alarm tasks: ```{traceback.format_exc()}```')
            await asyncio.sleep(5)
