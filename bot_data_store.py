from asyncio.queues import Queue

from client import Client

client = Client.get_client()


class ReactionSubscription:
    def __init__(self, user_id, message_id):
        self.user_id = user_id
        self.message_id = message_id
        self.queue = BotData.subscribe_to_message(user_id, message_id)

    def __enter__(self):
        return self.queue

    def __exit__(self, exc_type, value, traceback):
        BotData.unsubscribe_from_message(self.user_id, self.message_id)


class ConvoSubscription:
    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.queue = BotData.subscribe_to_convo(user_id, channel_id)

    def __enter__(self):
        return self.queue

    def __exit__(self, exc_type, value, traceback):
        BotData.unsubscribe_from_convo(self.user_id, self.channel_id)


class BotData:
    reaction_subscribers = {}
    convo_subscribers = {}

    @staticmethod
    def subscribe_to_message(user_id, message_id):
        if user_id not in BotData.reaction_subscribers:
            BotData.reaction_subscribers[user_id] = {}
        queue = Queue(loop=client.loop)
        BotData.reaction_subscribers[user_id][message_id] = queue
        return queue

    @staticmethod
    def unsubscribe_from_message(user_id, message_id):
        if user_id not in BotData.reaction_subscribers:
            BotData.reaction_subscribers[user_id] = {}
        if message_id in BotData.reaction_subscribers[user_id]:
            del BotData.reaction_subscribers[user_id][message_id]

    @staticmethod
    def subscribe_to_convo(user_id, channel_id):
        if user_id not in BotData.convo_subscribers:
            BotData.convo_subscribers[user_id] = {}
        queue = Queue(loop=client.loop)
        if channel_id in BotData.convo_subscribers[user_id]:
            raise RuntimeError('User is already subscribed to that conversation')
        BotData.convo_subscribers[user_id][channel_id] = queue
        return queue

    @staticmethod
    def unsubscribe_from_convo(user_id, channel_id):
        if user_id not in BotData.convo_subscribers:
            BotData.convo_subscribers[user_id] = {}
        if channel_id in BotData.convo_subscribers[user_id]:
            del BotData.convo_subscribers[user_id][channel_id]
