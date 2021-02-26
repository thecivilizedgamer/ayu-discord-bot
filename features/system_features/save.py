import asyncio

from base.feature import BaseFeature
from data import Data


class SaveFeature(BaseFeature):

    @property
    def feature_name(self):
        return 'save'

    @property
    def feature_hidden(self):
        return True

    @property
    def can_be_disabled(self):
        return False

    @property
    def background_tasks(self):
        return [save]


async def save():
    while True:
        _ = await Data.save_queue.get()
        while Data.save_queue.qsize() > 0:
            _ = await Data.save_queue.get()  # If multiple requested saves since the last one, "process" all saves at once
        await Data.save_to_disk()
        await asyncio.sleep(10)  # Add minimum time in between saves
