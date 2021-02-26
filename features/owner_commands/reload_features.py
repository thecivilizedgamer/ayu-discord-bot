from base.feature import BaseFeature
from bot import Bot


class ReloadFeaturesFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'reload-features'

    @property
    def command_keyword(self):
        return 'reload-features'

    @property
    def owner_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Reload all features'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        Bot.load_features()
        await message.channel.send('Reloaded features. Be advised that new or modified background tasks will not '
                                   'be processed until the bot is restarted. Also, some code elements may not have '
                                   'been fully reloaded.')
