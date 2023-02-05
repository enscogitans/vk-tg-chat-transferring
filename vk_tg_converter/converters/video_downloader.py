import abc
import logging
from pathlib import PurePath
from typing import Any, Optional

from youtube_dl import YoutubeDL
from youtube_dl.postprocessor import FFmpegVideoConvertorPP
from youtube_dl.postprocessor.common import PostProcessor
from youtube_dl.utils import DownloadError


class IVideoDownloader(abc.ABC):
    @abc.abstractmethod
    def try_download_video(self, player_url: str, output_template: str) -> Optional[PurePath]: ...


class _VideoConverterPostprocessor(PostProcessor):
    def __init__(self, downloader: YoutubeDL, allowed_formats: list[str], conversion_format: str) -> None:
        assert conversion_format in allowed_formats
        super().__init__(downloader=downloader)
        self.allowed_formats = allowed_formats
        self.conversion_format = conversion_format
        self.last_information: Optional[dict[Any, Any]] = None

    def run(self, information: dict[Any, Any]) -> tuple[list[str], dict[Any, Any]]:
        files_to_delete: list[str] = []
        if information["ext"] not in self.allowed_formats:
            postprocessor = FFmpegVideoConvertorPP(downloader=self._downloader, preferedformat=self.conversion_format)
            files_to_delete, information = postprocessor.run(information)
        self.last_information = information
        return files_to_delete, information


class VideoDownloader(IVideoDownloader):
    def __init__(self, logger: logging.Logger, allowed_formats: list[str], conversion_format: str,
                 max_video_size_mb: int, video_quality: str, retries: int) -> None:
        self.logger = logger
        self.allowed_formats = allowed_formats
        self.conversion_format = conversion_format
        self.max_video_size_mb = max_video_size_mb
        self.video_quality = video_quality  # E.g. "bestvideo+bestaudio/best"
        self.retries = retries

    def try_download_video(self, player_url: str, output_template: str) -> Optional[PurePath]:
        # For 'output_template' see https://github.com/ytdl-org/youtube-dl#output-template
        downloader_params = {
            "outtmpl": output_template,
            "retries": self.retries,
            # TODO: max_filesize doesn't always work. Files still can be larger than this limit...
            # It is possible if server doesn't provide 'Content-length'
            # https://github.com/ytdl-org/youtube-dl/blob/5208ae92fc3e2916cdccae45c6b9a516be3d5796/youtube_dl/downloader/http.py#L207-L216
            "max_filesize": self.max_video_size_mb * 2 ** 20,  # in bytes. Download will be aborted if file exceeds it
            "format": self.video_quality,
            "logger": self.logger,
        }
        try:
            with YoutubeDL(downloader_params) as ydl:
                post_processor = _VideoConverterPostprocessor(ydl, self.allowed_formats, self.conversion_format)
                ydl.add_post_processor(post_processor)
                download_info: dict[Any, Any] = ydl.extract_info(player_url, download=True)  # result is not used
                # ydl doesn't update download_info after post-processing, so we need to update it by ourselves
                assert post_processor.last_information is not None
                download_info = post_processor.last_information
                file_path: str = ydl.prepare_filename(download_info)  # Generated with respect to 'outtmpl'
            return PurePath(file_path)
        except DownloadError:
            return None
