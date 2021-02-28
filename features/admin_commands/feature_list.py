from base_feature import BaseFeature
from bot import Bot


class ServerFeatureListFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'server-feature-list'

    @property
    def command_keyword(self):
        return 'feature-list'

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
        return 'List enabled and disabled features for this server'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        server_features = Bot.get_server_only_features(
            message.guild.id, include_admin=True, include_owner=False, include_disabled=True)
        features = [x for x in server_features if not x.feature_hidden]  # Ignore hidden features

        enabled_features = [x for x in features if x.enabled_for_server(message.guild.id)]
        disabled_features = [x for x in features if not x.enabled_for_server(message.guild.id)]

        msg = ''

        if len(enabled_features) > 0:
            msg += f'Enabled Features:\n```'
            for feature in enabled_features:
                msg += f'\n{feature.feature_name}: {feature.get_brief_description(message.author.id, message.guild.id)}'
            msg += '```\n'

        if len(disabled_features) > 0:
            msg += f'Disabled Features:\n```'
            for feature in disabled_features:
                msg += f'\n{feature.feature_name}'
            msg += '```'

        if msg == '':
            await message.channel.send(f"There are no features available for use in this server")
        else:
            await message.channel.send(msg)
