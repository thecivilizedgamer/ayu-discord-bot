import importlib
import os
from asyncio.queues import Queue

from base_feature import BaseFeature
from client import Client
from data import Data
from static_data import StaticData

client = Client.get_client()


class ReactionSubscription:
    def __init__(self, user_id, message_id):
        self.user_id = user_id
        self.message_id = message_id
        self.queue = Bot.subscribe_to_message(user_id, message_id)

    def __enter__(self):
        return self.queue

    def __exit__(self, exc_type, value, traceback):
        Bot.unsubscribe_from_message(self.user_id, self.message_id)


class ConvoSubscription:
    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.queue = Bot.subscribe_to_convo(user_id, channel_id)

    def __enter__(self):
        return self.queue

    def __exit__(self, exc_type, value, traceback):
        Bot.unsubscribe_from_convo(self.user_id, self.channel_id)


class Bot:
    running = False
    reaction_subscribers = {}
    convo_subscribers = {}
    features = []
    feature_footprints = {}

    @staticmethod
    def get_server_only_features(guild_id, include_admin, include_owner, include_disabled=False):
        features = []
        for feature in Bot.features:
            if not feature.server_only:
                continue
            if feature.admin_only and not include_admin:
                continue
            if feature.owner_only and not include_owner:
                continue
            if feature.enabled_for_server(guild_id) or include_disabled:
                features.append(feature)
        features.sort(key=lambda x: x.feature_name)
        features.sort(key=lambda x: x.priority)
        return features

    @staticmethod
    def get_dm_only_features(include_owner):
        features = []
        for feature in Bot.features:
            if not feature.dm_only:
                continue
            if feature.admin_only:  # admin-only features not processed in DMs because they are server-related
                continue
            if feature.owner_only and not include_owner:
                continue
            features.append(feature)
        features.sort(key=lambda x: x.feature_name)
        features.sort(key=lambda x: x.priority)
        return features

    @staticmethod
    def get_global_features(guild_id, include_admin, include_owner):
        # Pass guild id in unconditionally. It will be None if DM
        features = []
        for feature in Bot.features:
            if feature.dm_only:
                continue
            if feature.server_only:
                continue
            if feature.admin_only and not include_admin:
                continue
            if feature.owner_only and not include_owner:
                continue
            if guild_id is not None and not feature.enabled_for_server(guild_id):
                continue
            features.append(feature)
        features.sort(key=lambda x: x.feature_name)
        features.sort(key=lambda x: x.priority)
        return features

    @staticmethod
    def get_available_commands(is_dm, is_admin, is_owner, guild_id):
        if is_dm:
            commands = {x.command_keyword: x for x in Bot.get_dm_only_features(
                is_owner) if x.command_keyword is not None}
        else:
            commands = {x.command_keyword: x for x in Bot.get_server_only_features(
                guild_id, is_admin, is_owner) if x.command_keyword is not None}
        commands.update({x.command_keyword: x for x in Bot.get_global_features(guild_id, is_admin, is_owner)})
        return commands

    @staticmethod
    async def display_help(message):
        normal_features = []
        admin_features = []
        owner_features = []

        is_dm = message.guild is None
        is_admin = False if is_dm else message.author.id in Data.get_server_data(message.guild.id)['administrators']
        is_owner = message.author.id == StaticData.get_value('config.owner_user_id')

        for feature in Bot.features:
            if feature.command_keyword is None or feature.command_hidden:
                continue
            if message.guild is None and feature.server_only:
                continue
            if message.guild is not None and (feature.dm_only or not feature.enabled_for_server(message.guild.id)):
                continue
            if feature.admin_only:
                admin_features.append(feature)
            elif feature.owner_only:
                owner_features.append(feature)
            else:
                normal_features.append(feature)

        guild_id = None if message.guild is None else message.guild.id
        msg = 'Here are all the commands available to you:\n```'
        for feature in normal_features:
            msg += f'{feature.command_keyword}: {feature.get_brief_description(message.author.id, guild_id)}\n'

        if is_admin and len(admin_features) > 0:
            msg += '\n'
            msg += 'Admin-only features:\n'
            for feature in admin_features:
                msg += f'   {feature.command_keyword}: {feature.get_brief_description(message.author.id, guild_id)}\n'

        if is_owner and len(owner_features) > 0:
            msg += '\n'
            msg += 'Owner-only features:\n'
            for feature in owner_features:
                msg += f'   {feature.command_keyword}: {feature.get_brief_description(message.author.id, guild_id)}\n'

        msg = msg.rstrip() + '```'

        await message.channel.send(msg)

    @staticmethod
    def subscribe_to_message(user_id, message_id):
        if user_id not in Bot.reaction_subscribers:
            Bot.reaction_subscribers[user_id] = {}
        queue = Queue(loop=client.loop)
        Bot.reaction_subscribers[user_id][message_id] = queue
        return queue

    @staticmethod
    def unsubscribe_from_message(user_id, message_id):
        if user_id not in Bot.reaction_subscribers:
            Bot.reaction_subscribers[user_id] = {}
        if message_id in Bot.reaction_subscribers[user_id]:
            del Bot.reaction_subscribers[user_id][message_id]

    @staticmethod
    def subscribe_to_convo(user_id, channel_id):
        if user_id not in Bot.convo_subscribers:
            Bot.convo_subscribers[user_id] = {}
        queue = Queue(loop=client.loop)
        if channel_id in Bot.convo_subscribers[user_id]:
            raise RuntimeError('User is already subscribed to that conversation')
        Bot.convo_subscribers[user_id][channel_id] = queue
        return queue

    @staticmethod
    def unsubscribe_from_convo(user_id, channel_id):
        if user_id not in Bot.convo_subscribers:
            Bot.convo_subscribers[user_id] = {}
        if channel_id in Bot.convo_subscribers[user_id]:
            del Bot.convo_subscribers[user_id][channel_id]

    @staticmethod
    def start_tasks():
        if Bot.running:
            raise RuntimeError('Cannot start tasks when bot is already running')

        for feature in Bot.features:
            for task in feature.background_tasks:
                client.loop.create_task(task())

    @staticmethod
    def load_features():
        # Import feature modules
        feature_modules = []
        new_feature_footprints = {}
        for root, _, filenames in os.walk('features'):
            for filename in filenames:
                if filename.lower().endswith('.py') and not filename.lower().startswith('_'):
                    feature_modules.append(
                        importlib.import_module(os.path.join(root, filename[:-3]).replace(os.sep, '.')))
                    new_feature_footprints[os.path.join(root, filename)] = hash(
                        open(os.path.join(root, filename)).read())

        # Instantiate new features
        new_features = []
        new_feature_names = []
        new_command_keywords = []
        for feature_module in feature_modules:
            feature_initialized = False
            for element in dir(feature_module):
                if element == 'BaseFeature':
                    continue
                try:
                    feature = getattr(feature_module, element)()
                except Exception:
                    continue
                if isinstance(feature, BaseFeature):
                    if feature.feature_name.lower() in new_feature_names:
                        raise RuntimeError(f'Duplicate feature {feature.feature_name}')
                    if feature.command_keyword is not None and feature.command_keyword.lower() in new_command_keywords:
                        raise RuntimeError(f'Duplicate command keyword {feature.command_keyword}')
                    new_features.append(feature)
                    new_feature_names.append(feature.feature_name.lower())
                    if feature.command_keyword is not None:
                        new_command_keywords.append(feature.command_keyword.lower())
                    feature_initialized = True
                    break
            if not feature_initialized:
                raise RuntimeError(
                    f'Unable to instantiate feature defined in {feature_module}')

        # Replace old features, since all new features were loaded successfully
        Bot.features = new_features

        # Analyze which features changed
        load_results = {
            'added': [x for x in new_feature_footprints if x not in Bot.feature_footprints],
            'removed': [x for x in Bot.feature_footprints if x not in new_feature_footprints],
            'modified': [x for x in new_feature_footprints
                         if x in Bot.feature_footprints and new_feature_footprints[x] != Bot.feature_footprints[x]]
        }

        Bot.feature_footprints = new_feature_footprints
        return load_results
