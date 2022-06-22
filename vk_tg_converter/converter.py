from pathlib import Path
from typing import Optional

from vk_api.vk_api import VkApiMethod

import tg_importer.types as tg
import vk_exporter.types as vk
from config import Config
from vk_tg_converter.contacts.username_manager import ContactInfo, UsernameManagerV1
from vk_tg_converter.media_converter import MediaConverterV1
from vk_tg_converter.message_converter import MessageConverterV1


async def convert_messages(
        vk_api: VkApiMethod,
        config: Config.Vk,
        vk_messages: list[vk.Message],
        prepared_contacts: Optional[list[ContactInfo]],
        tg_media_export_dir: Path,
        disable_progress_bar: bool) -> list[tg.Message]:
    username_manager = UsernameManagerV1(vk_api, prepared_contacts)
    media_converter = MediaConverterV1(
        vk_api, tg_media_export_dir, config.max_video_workers, config.max_non_video_workers,
        config.max_video_size_mb, config.video_quality, config.max_video_download_retries, disable_progress_bar)
    converter = MessageConverterV1(config.timezone, username_manager, media_converter)
    return await converter.convert(vk_messages)
