from datetime import datetime, tzinfo
import envparse
from pathlib import PurePath
from typing import Optional

from vk_api import VkUserPermissions


def _get_local_timezone() -> tzinfo:
    tz = datetime.now().astimezone().tzinfo
    assert tz is not None
    return tz


class Config:
    def __init__(self, config_file_path: Optional[PurePath] = PurePath("env")) -> None:
        env: envparse.Env = envparse.Env()  # If config_file_path is None, read from environment
        if config_file_path is not None:
            env.read_envfile(config_file_path)  # Read everything from file (no overrides)

        self.tg = Config.Telegram(env)
        self.vk = Config.Vk(env)
        self.vk_default_raw_export_file = PurePath("vk_raw_messages.pickle")
        self.vk_default_export_file = PurePath("vk_messages.pickle")
        self.tg_default_export_file = PurePath("tg_messages.pickle")
        self.tg_default_media_export_dir = PurePath("exported_media")
        self.default_contacts_mapping_file = PurePath("contacts_mapping.yaml")

    class Telegram:
        def __init__(self, env: envparse.Env) -> None:
            self.env = env
            self.client_name = "tg"
            self.max_simultaneously_uploaded_files = 10
            self.timezone = _get_local_timezone()

        @property
        def api_id(self) -> str:
            return self.env.str("TG_API_ID")  # type: ignore

        @property
        def api_hash(self) -> str:
            return self.env.str("TG_API_HASH")  # type: ignore

    class Vk:
        def __init__(self, env: envparse.Env) -> None:
            self.env = env
            self.client_name = "vk"
            self.scope: int = VkUserPermissions.MESSAGES | VkUserPermissions.VIDEO
            self.api_version = "5.131"
            self.timezone = _get_local_timezone()
            # workers which download media files
            self.max_non_video_workers = 10
            self.max_video_workers = 5

            self.max_video_download_retries = 5
            self.max_video_size_mb = 50
            # See https://github.com/ytdl-org/youtube-dl#format-selection for more information
            self.video_quality = "(bestvideo+bestaudio/best)[filesize<=?{}M]".format(self.max_video_size_mb)

        @property
        def api_id(self) -> int:
            return self.env.int("VK_API_ID")  # type: ignore
