class DB:
    db = {}

    @staticmethod
    def ensure_user_id(user_id):
        if user_id not in DB.db:
            DB.db[user_id] = {
                'timers': {},
                'alarms': {}
            }

    @staticmethod
    def get_utc_time_offset_mins(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id].get('utc_offset_mins')

    @staticmethod
    def set_utc_time_offset_mins(user_id, utc_offset):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['utc_offset_mins'] = utc_offset

    @staticmethod
    def get_timers(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id]['timers']

    @staticmethod
    def get_all_timers():
        return {key: val['timers'] for key, val in DB.db.items()}

    @staticmethod
    def add_timer(user_id, timer_name, timer_end):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['timers'][timer_name] = timer_end

    @staticmethod
    def delete_timer(user_id, timer_name):
        DB.ensure_user_id(user_id)
        mapping = {name.lower(): name for name in DB.db[user_id]['timers'].keys()}
        actual_name = mapping[timer_name.lower()]
        if actual_name in DB.db[user_id]['timers']:
            del DB.db[user_id]['timers'][actual_name]

    @staticmethod
    def get_alarms(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id]['alarms']

    @staticmethod
    def get_all_alarms():
        return {key: val['alarms'] for key, val in DB.db.items()}

    @staticmethod
    def add_alarm(user_id, alarm_name, alarm_data):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['alarms'][alarm_name] = alarm_data

    @staticmethod
    def delete_alarm(user_id, alarm_name):
        DB.ensure_user_id(user_id)
        mapping = {name.lower(): name for name in DB.db[user_id]['alarms'].keys()}
        actual_name = mapping[alarm_name.lower()]
        if actual_name in DB.db[user_id]['alarms']:
            del DB.db[user_id]['alarms'][actual_name]
