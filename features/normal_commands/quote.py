from base_feature import BaseFeature
from misc import capitalize
from static_data import StaticData


class QuoteFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'quote'

    @property
    def command_keyword(self):
        return 'quote'

    def get_brief_description(self, user_id, guild_id):
        return 'Say an inspiring quote'

    async def command_execute(self, message, arguments):
        quote, _, author = StaticData.get_random_choice('quotes.quotes').rpartition(';')
        await message.channel.send(f'"{capitalize(quote)}"\n   -{capitalize(author)}')
