import discord


bot_intents = discord.Intents.default()
bot_intents.reactions = True


class Client:
    client = None

    @staticmethod
    def get_client():
        if Client.client is None:
            Client.client = discord.Client(intents=bot_intents)
        return Client.client
