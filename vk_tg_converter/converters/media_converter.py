import abc
import asyncio
import os.path
import urllib.parse
import urllib.request
from asyncio import AbstractEventLoop
from concurrent.futures import Executor, ThreadPoolExecutor
from logging import Logger
from pathlib import Path, PurePath
from typing import Optional

import PIL.Image
from aiohttp import ClientSession
from tqdm.asyncio import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from vk_api.vk_api import VkApiMethod

import tg_importer.types as tg
import vk_exporter.types as vk
from config import Config
from vk_tg_converter.converters.video_downloader import IVideoDownloader


class IMediaConverter(abc.ABC):
    @abc.abstractmethod
    async def try_convert(self, attachments: list[vk.Attachment]) -> list[None | tg.Media]: ...


class MediaConverter(IMediaConverter):
    def __init__(self, api: VkApiMethod, video_downloader: IVideoDownloader, logger: Logger,
                 export_dir: Path, config: Config, disable_progress_bar: bool) -> None:
        export_dir.mkdir(parents=True, exist_ok=True)
        if any(True for _ in export_dir.iterdir()):
            raise ValueError(f"Directory is not empty: {export_dir}")
        self.export_dir = export_dir
        self.api = api
        self.video_downloader = video_downloader
        self.logger = logger
        self.n_files_demanded = 0

        self.max_video_workers = config.vk.max_video_workers
        self.video_download_semaphore = asyncio.Semaphore(self.max_video_workers)
        self.non_video_download_semaphore = asyncio.Semaphore(config.vk.max_non_video_workers)
        self.disable_progress_bar = disable_progress_bar

    async def try_convert(self, attachments: list[vk.Attachment]) -> list[None | tg.Media]:
        result: list[Optional[tg.Media]] = [None] * len(attachments)

        videos_with_idx: list[tuple[vk.Video, int]] = []
        non_videos_with_idx: list[tuple[vk.Attachment, int]] = []
        for i, attch in enumerate(attachments):
            if isinstance(attch, vk.Video):
                videos_with_idx.append((attch, i))
            elif self._is_non_video_supported(attch):
                non_videos_with_idx.append((attch, i))

        loop = asyncio.get_running_loop()

        async def non_videos_task(session: ClientSession) -> None:
            async def one_task(attch: vk.Attachment, idx: int) -> None:
                result[idx] = await self._try_convert_non_video(attch, session)

            tasks = [one_task(attch, idx) for attch, idx in non_videos_with_idx]
            if tasks:
                await tqdm.gather(*tasks, desc="Non-video", disable=self.disable_progress_bar)

        async def videos_task(session: ClientSession) -> None:
            async def one_task(video: vk.Video, idx: int, executor: Executor) -> None:
                result[idx] = await self._try_convert_video(video, session, loop, executor)

            with ThreadPoolExecutor(max_workers=self.max_video_workers) as executor:
                tasks = [one_task(video, idx, executor) for video, idx in videos_with_idx]
                if tasks:
                    await tqdm.gather(*tasks, desc="Video", disable=self.disable_progress_bar)

        # This is to prevent logger and tqdm outputs interfere
        # Why logger.parent? I don't know, but None or just logger or logger.root don't fix the issue
        with logging_redirect_tqdm([self.logger.parent]):
            async with ClientSession() as session:
                await asyncio.gather(non_videos_task(session))
                # Running them in parallel doesn't really speed anything up
                # Sequential run at least has better visualization
                await asyncio.gather(videos_task(session))
        return result

    @staticmethod
    def _is_non_video_supported(attachment: vk.Attachment) -> bool:
        assert not isinstance(attachment, vk.Video)
        return isinstance(attachment, (vk.Photo, vk.Sticker, vk.Document, vk.Audio, vk.Voice))

    async def _try_convert_non_video(self, attachment: vk.Attachment, session: ClientSession) -> Optional[tg.Media]:
        if isinstance(attachment, vk.Photo):
            return await self._try_convert_photo(attachment, session)
        if isinstance(attachment, vk.Sticker):
            return await self._try_convert_sticker(attachment, session)
        if isinstance(attachment, vk.Document):
            return await self._try_convert_document(attachment, session)
        if isinstance(attachment, vk.Audio):
            return await self._try_convert_audio(attachment, session)
        if isinstance(attachment, vk.Voice):
            return await self._try_convert_voice(attachment, session)
        assert not self._is_non_video_supported(attachment)
        return None

    async def _try_convert_video(self, video: vk.Video, session: ClientSession,
                                 loop: AbstractEventLoop, executor: Executor) -> Optional[tg.Video]:
        async with self.video_download_semaphore:
            player_url_opt = video.try_get_player_url(self.api)
            if player_url_opt is None:
                self.logger.error(f"Couldn't get video url for '{video.title}'. Skipping")
                return None
            file_path_opt = await loop.run_in_executor(executor, self._try_download_video, player_url_opt)
            if file_path_opt is None:
                self.logger.error(f"Couldn't download video '{video.title}'. Skipping")
                return None
            thumb_path = None
            if video.image_url is not None:
                thumb_path = await self._try_download_file(video.image_url, session)
                if thumb_path is None:
                    self.logger.warning(f"Couldn't download thumbnail for '{video.title}'. Skipping the thumbnail")
            else:
                self.logger.warning(f"Couldn't download thumbnail for '{video.title}', video.image_url is None")
        return tg.Video(
            path=file_path_opt,
            title=video.title,
            duration=video.duration,
            width=video.width,
            height=video.height,
            thumb_path=thumb_path,
        )

    async def _try_convert_photo(self, photo: vk.Photo, session: ClientSession) -> Optional[tg.Photo]:
        if file_opt := await self._try_download_file(photo.url, session):
            return tg.Photo(file_opt)
        self.logger.error(f"Couldn't download photo. Skipping. Link {photo.url}")
        return None

    async def _try_convert_sticker(self, sticker: vk.Sticker, session: ClientSession) -> Optional[tg.Sticker]:
        # Vk uses .png for stickers, but tg doesn't support it. However, it supports .webp
        if file_opt := await self._try_download_file(sticker.image_url, session):
            if not file_opt.suffix == ".webp":
                new_path = file_opt.with_suffix(".webp")
                with PIL.Image.open(file_opt) as image:
                    image.save(new_path, format="webp")
                file_opt.unlink()
                file_opt = new_path
            return tg.Sticker(path=file_opt)
        self.logger.error(f"Couldn't download sticker. Skipping. Link {sticker.image_url}")
        return None

    async def _try_convert_document(self, document: vk.Document, session: ClientSession) -> Optional[tg.Document]:
        if file_opt := await self._try_download_file(document.url, session, extension_hint="." + document.extension):
            return tg.Document(file_opt, title=document.title)
        self.logger.error(f"Couldn't download document '{document.title}'. Skipping")
        return None

    async def _try_convert_audio(self, audio: vk.Audio, session: ClientSession) -> Optional[tg.Audio]:
        if not audio.url:
            self.logger.error(f"Couldn't download audio '{audio.title} - {audio.artist}'. No url available. Skipping")
            return None
        if file_opt := await self._try_download_file(audio.url, session):
            return tg.Audio(file_opt, performer=audio.artist, title=audio.title, duration=audio.duration)
        self.logger.error(f"Couldn't download audio '{audio.title} - {audio.artist}'. Skipping")
        return None

    async def _try_convert_voice(self, voice: vk.Voice, session: ClientSession) -> Optional[tg.Voice]:
        if file_opt := await self._try_download_file(voice.link_ogg, session):
            return tg.Voice(file_opt, duration=voice.duration)
        self.logger.error(f"Couldn't download voice. Skipping. Link {voice.link_ogg}")
        return None

    async def _try_download_file(self, url: str, session: ClientSession, extension_hint: str = "") -> Optional[Path]:
        parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(url)
        extension: str = PurePath(parsed_url.path).suffix or extension_hint  # May be empty
        file_path: Path = self._make_new_path(postfix=extension)
        async with self.non_video_download_semaphore:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                with file_path.open("xb") as dst:
                    dst.write(await resp.content.read())
        return file_path

    def _try_download_video(self, player_url: str) -> Optional[PurePath]:
        path: PurePath = self._make_new_path(postfix="")
        dir_escaped = str(path.parent).replace("%", "%%")
        old_name_escaped = str(path.name).replace("%", "%%")

        # example: "export_dir/FILE-0003 (video title).mp4"
        output_template = os.path.join(dir_escaped, old_name_escaped + " (%(title)s).%(ext)s")
        return self.video_downloader.try_download_video(player_url, output_template)

    def _make_new_path(self, *, postfix: str) -> Path:
        self.n_files_demanded += 1
        return self.export_dir / "FILE-{:0>4}{}".format(self.n_files_demanded, postfix)
