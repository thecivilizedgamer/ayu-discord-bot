from misc import hours_and_minutes_to_str, list_to_str


def get_alarm_description(alarm_name, days, times):
    description = f'{alarm_name} at '
    description += list_to_str([hours_and_minutes_to_str(x[0], x[1]) for x in times])
    description += ' on ' + list_to_str([x + 's' for x in days])
    return description


class UserData:
    timers = {}
    alarms = {}

    @staticmethod
    def get_timers(user_id):
        if user_id not in UserData.timers:
            UserData.timers[user_id] = {}
        return UserData.timers[user_id]

    @staticmethod
    def add_timer(user_id, timer_name, timer_end):
        if user_id not in UserData.timers:
            UserData.timers[user_id] = {}
        UserData.timers[user_id][timer_name] = timer_end

    @staticmethod
    def delete_timer(user_id, timer_name):
        if user_id not in UserData.timers:
            UserData.timers[user_id] = {}
        mapping = {name.lower(): name for name in UserData.timers[user_id].keys()}
        actual_name = mapping[timer_name.lower()]
        if actual_name in UserData.timers[user_id]:
            del UserData.timers[user_id][actual_name]

    @staticmethod
    def get_alarms(user_id):
        if user_id not in UserData.alarms:
            UserData.alarms[user_id] = {}
        return UserData.alarms[user_id]

    @staticmethod
    def add_alarm(user_id, alarm_name, alarm_data):
        if user_id not in UserData.alarms:
            UserData.alarms[user_id] = {}
        UserData.alarms[user_id][alarm_name] = alarm_data

    @staticmethod
    def delete_alarm(user_id, alarm_name):
        if user_id not in UserData.alarms:
            UserData.alarms[user_id] = {}
        mapping = {name.lower(): name for name in UserData.alarms[user_id].keys()}
        actual_name = mapping[alarm_name.lower()]
        if actual_name in UserData.alarms[user_id]:
            del UserData.alarms[user_id][actual_name]
