class UserData:
    timers = {}

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
