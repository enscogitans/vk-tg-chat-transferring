import abc
from pathlib import Path
from typing import Optional

from vk_api.vk_api import VkApiMethod

from config import Config
from vk_tg_converter.contacts.username_manager import ContactInfo, UsernameManager
from vk_tg_converter.converters.history_converter import IHistoryConverter, HistoryConverter
from vk_tg_converter.converters.media_converter import MediaConverter
from vk_tg_converter.converters.message_converter import MessageConverter
from vk_tg_converter.converters.video_downloader import VideoDownloader


class IHistoryConverterFactory(abc.ABC):
    @abc.abstractmethod
    def create(self, contacts: Optional[list[ContactInfo]],
               media_export_dir: Path, disable_progress_bar: bool) -> IHistoryConverter: ...


class HistoryConverterFactory(IHistoryConverterFactory):
    def __init__(self, vk_api: VkApiMethod, config: Config) -> None:
        self.vk_api = vk_api
        self.config = config

    def create(self, contacts: Optional[list[ContactInfo]],
               media_export_dir: Path, disable_progress_bar: bool) -> HistoryConverter:
        username_manager = UsernameManager(self.vk_api, contacts)
        video_downloader = VideoDownloader(
            self.config.tg.allowed_video_formats, self.config.tg.video_conversion_format,
            self.config.vk.max_video_size_mb, self.config.vk.video_quality, self.config.vk.max_video_download_retries)
        media_converter = MediaConverter(
            self.vk_api, video_downloader, media_export_dir, self.config, disable_progress_bar)
        message_converter = MessageConverter(self.config.vk.timezone, username_manager, media_converter)
        return HistoryConverter(message_converter, media_converter)
