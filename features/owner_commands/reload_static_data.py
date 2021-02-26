from base.feature import BaseFeature
from static_data import StaticData


class ReloadStaticDataFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'reload-static-data'

    @property
    def command_keyword(self):
        return 'reload-static-data'

    @property
    def owner_only(self):
        return True

    def get_brief_description(self, user_id, guild_id):
        return 'Reload static data files'

    @property
    def can_be_disabled(self):
        return False

    async def command_execute(self, message, arguments):
        msg = StaticData.load_static_data()
        if msg == '':
            await message.channel.send("Something went wrong, didn't get any output from reload command")
        else:
            await message.channel.send(msg)
