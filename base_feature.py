from data import Data


class BaseFeature:

    def initialize_feature(self):
        # Post-data-load feature initialization
        pass

    def get_feature_data(self):
        if self.data_access_key not in Data.data:
            Data.data[self.data_access_key] = {'users': {}, 'servers': {}, 'global': {}}
        return Data.data[self.data_access_key]['global']

    def get_user_data(self, user_id):
        if self.data_access_key not in Data.data:
            Data.data[self.data_access_key] = {'users': {}, 'servers': {}, 'global': {}}
        if user_id not in Data.data[self.data_access_key]['users']:
            Data.data[self.data_access_key]['users'][user_id] = {}
        return Data.data[self.data_access_key]['users'][user_id]

    def get_server_data(self, guild_id):
        if self.data_access_key not in Data.data:
            Data.data[self.data_access_key] = {'users': {}, 'servers': {}, 'global': {}}
        if guild_id not in Data.data[self.data_access_key]['servers']:
            Data.data[self.data_access_key]['servers'][guild_id] = {'enabled': True}
        return Data.data[self.data_access_key]['servers'][guild_id]

    def get_global_user_data(self, user_id):
        if user_id not in Data.data['global']:
            Data.data['global'][user_id] = {}
        return Data.data['global'][user_id]

    def enabled_for_server(self, guild_id):
        if self.enable_state_key not in Data.data:
            Data.data[self.enable_state_key] = {'users': {}, 'servers': {}, 'global': {}}
        if guild_id not in Data.data[self.enable_state_key]['servers']:
            Data.data[self.enable_state_key]['servers'][guild_id] = {'enabled': True}
        return Data.data[self.enable_state_key]['servers'][guild_id]['enabled']

    def enable_feature_for_server(self, guild_id):
        if self.enable_state_key not in Data.data:
            Data.data[self.enable_state_key] = {'users': {}, 'servers': {}, 'global': {}}
        if guild_id not in Data.data[self.enable_state_key]['servers']:
            Data.data[self.enable_state_key]['servers'][guild_id] = {'enabled': True}
        else:
            Data.data[self.enable_state_key]['servers'][guild_id]['enabled'] = True

    def disable_feature_for_server(self, guild_id):
        if self.enable_state_key not in Data.data:
            Data.data[self.enable_state_key] = {'users': {}, 'servers': {}, 'global': {}}
        if guild_id not in Data.data[self.enable_state_key]['servers']:
            Data.data[self.enable_state_key]['servers'][guild_id] = {'enabled': False}
        else:
            Data.data[self.enable_state_key]['servers'][guild_id]['enabled'] = False

    @property
    def feature_name(self):
        raise NotImplementedError()

    @property
    def command_keyword(self):
        return None

    @property
    def data_access_key(self):
        return self.feature_name

    @property
    def enable_state_key(self):
        return self.data_access_key

    @property
    def admin_only(self):
        return False

    @property
    def owner_only(self):
        return False

    @property
    def server_only(self):
        return False

    @property
    def dm_only(self):
        return False

    def get_brief_description(self, user_id, guild_id):
        raise NotImplementedError()

    @property
    def add_reaction_callbacks(self):
        return []

    @property
    def remove_reaction_callbacks(self):
        return []

    @property
    def on_message_first_callbacks(self):
        return []

    @property
    def on_message_last_callbacks(self):
        return []

    @property
    def background_tasks(self):
        return []

    @property
    def feature_hidden(self):
        return False

    @property
    def command_hidden(self):
        return False

    @property
    def priority(self):
        """
        Higher-priority will be executed before lower-priority. If priority values are equal, features will be 
        processed alphabetically by the feature name
        """
        return 50

    @property
    def can_be_disabled(self):
        return True

    async def command_execute(self, message, arguments):
        pass
