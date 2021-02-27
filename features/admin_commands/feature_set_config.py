from base_feature import BaseFeature
from bot import Bot
from data import Data


class ServerConfigSetFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'server-feature-configure-set'

    @property
    def command_keyword(self):
        return 'feature-config-set'

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
        return 'Set a config option for a specified feature'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        if arguments is None:
            await message.channel.send(f"You must specify a feature and config to set")
            return

        feature_name, config = arguments.split(maxsplit=1)
        server_features = Bot.get_server_only_features(message.guild.id, include_admin=True, include_owner=False)
        feature_names = [x.feature_name for x in server_features if not x.feature_hidden]  # Ignore hidden features

        if feature_name not in feature_names:
            await message.channel.send(f"I'm sorry, either feature \"{feature_name}\" is disabled, or it doesn't exist")
        else:
            feature = server_features[feature_names.index(feature_name)]
            data = feature.get_server_data(message.guild.id)
            key, val = config.split('=')
            if key not in data:
                await message.channel.send(f"Warning: config option \"{key}\" does not already exist for feature \"{feature_name}\" on this server")
            data[key] = val
            await Data.request_save()
