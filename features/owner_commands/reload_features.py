import traceback

from base_feature import BaseFeature
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
        try:
            results = Bot.load_features()
        except Exception:
            await message.channel.send(f'Failed to reload features. Error message:\n{traceback.format_exc()}')
        else:
            msg = '```'
            if len(results['added']) > 0:
                msg += 'Added:'
                for feature in results['added']:
                    msg += f'\n   {feature}'
            if len(results['removed']) > 0:
                msg += 'Removed:'
                for feature in results['removed']:
                    msg += f'\n   {feature}'
            if len(results['modified']) > 0:
                msg += 'Modified:'
                for feature in results['modified']:
                    msg += f'\n   {feature}'
            msg += '```'
            if msg == '``````':
                await message.channel.send('It looks like no features were changed, added or removed, '
                                           'although changes in dependent packages could have been imported and '
                                           'could affect feature behavior.')
            else:
                await message.channel.send(f'Finished reloading features:\n{msg}\nBe advised that new or modified '
                                           'background tasks will not be processed until the bot is restarted. Also, '
                                           'some code elements may not have been fully reloaded.')
