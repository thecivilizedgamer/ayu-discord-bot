from client import Client

client = Client.get_client()


class User:
    _users = {}

    @staticmethod
    async def get_dm_channel(user_id):
        if user_id not in User._users:
            User._users[user_id] = await client.fetch_user(user_id)
        channel = User._users[user_id].dm_channel
        if channel is None:
            channel = await User._users[user_id].create_dm()
        return channel

    @staticmethod
    async def get_user(user_id):
        if user_id not in User._users:
            User._users[user_id] = await client.fetch_user(user_id)
        return User._users[user_id]

    @staticmethod
    async def send_dm(user_id, message):
        channel = await User.get_dm_channel(user_id)
        return await channel.send(message)
