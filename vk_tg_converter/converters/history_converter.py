import abc
from typing import Optional

import tg_importer.types as tg
import vk_exporter.types as vk
from vk_tg_converter.converters.media_converter import MediaConverter
from vk_tg_converter.converters.message_converter import MessageConverter


class IHistoryConverter(abc.ABC):
    @abc.abstractmethod
    async def convert(self, vk_history: vk.ChatHistory) -> tg.ChatHistory: ...


class HistoryConverter(IHistoryConverter):
    def __init__(self, message_converter: MessageConverter, media_converter: MediaConverter):
        self.message_converter = message_converter
        self.media_converter = media_converter

    async def convert(self, vk_history: vk.ChatHistory) -> tg.ChatHistory:
        photo_opt: Optional[tg.Photo] = None
        if vk_history.photo_opt is not None:
            [media] = await self.media_converter.try_convert([vk_history.photo_opt])
            assert media is None or isinstance(media, tg.Photo), type(media)
            photo_opt = media
        return tg.ChatHistory(
            messages=await self.message_converter.convert(vk_history.messages),
            title_opt=vk_history.title_opt,
            photo_opt=photo_opt,
        )
