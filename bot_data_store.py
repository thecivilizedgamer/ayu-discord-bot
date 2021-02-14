from asyncio.queues import Queue

from client import Client

client = Client.get_client()


class BotData:
    reaction_subscribers = {}

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
        if message_id in BotData.reaction_subscribers[user_id][message_id]:
            del BotData.reaction_subscribers[user_id][message_id]
