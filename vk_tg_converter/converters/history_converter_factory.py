import abc
from pathlib import Path
from typing import Optional

from vk_api.vk_api import VkApiMethod

from config import Config
from vk_tg_converter.contacts import UsernameManagerV1
from vk_tg_converter.contacts.username_manager import ContactInfo
from vk_tg_converter.converters.media_converter import MediaConverterV1
from vk_tg_converter.converters.message_converter import MessageConverterV1
from vk_tg_converter.converters.history_converter import IHistoryConverter, HistoryConverter


class IHistoryConverterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, contacts: Optional[list[ContactInfo]],
               media_export_dir: Path, disable_progress_bar: bool) -> IHistoryConverter: ...


class HistoryConverterFactory(IHistoryConverterFactory):
    def __init__(self, vk_api: VkApiMethod, vk_config: Config.Vk) -> None:
        self.vk_api = vk_api
        self.vk_config = vk_config

    def create(self, contacts: Optional[list[ContactInfo]],
               media_export_dir: Path, disable_progress_bar: bool) -> IHistoryConverter:
        username_manager = UsernameManagerV1(self.vk_api, contacts)
        media_converter = MediaConverterV1(self.vk_api, media_export_dir, self.vk_config, disable_progress_bar)
        message_converter = MessageConverterV1(self.vk_config.timezone, username_manager, media_converter)
        return HistoryConverter(message_converter, media_converter)
