from base_feature import BaseFeature
from bot import Bot
from data import Data


class ServerFeatureEnableFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'server-feature-enable'

    @property
    def command_keyword(self):
        return 'feature-enable'

    @property
    def server_only(self):
        return True

    @property
    def admin_only(self):
        return True

    @property
    def feature_hidden(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Enable a feature for the current server'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            await message.channel.send(f"You must specify a feature to enable")
            return

        feature_name = arguments.strip()

        server_features = Bot.get_server_only_features(
            message.guild.id, include_admin=True, include_owner=False, include_disabled=True)

        # Ignore hidden features and features that can't be disabled
        feature_names = [x.feature_name for x in server_features if not x.feature_hidden and x.can_be_disabled]

        if feature_name not in feature_names:
            await message.channel.send(f"I'm sorry, either feature \"{feature_name}\" doesn't exist, or it can't be disabled in the first place")
        else:
            feature = server_features[feature_names.index(feature_name)]
            data = feature.get_server_data(message.guild.id)
            if data['enabled']:
                await message.channel.send(f"Feature is already enabled")
            else:
                data['enabled'] = True
                await Data.request_save()
                await message.channel.send(f"Feature has been enabled")
