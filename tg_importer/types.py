import abc
import datetime
from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional

from pyrogram import Client
from pyrogram.errors import FilePartMissing
from pyrogram.raw.base import InputFile, InputMedia, InputPeer, MessageMedia
from pyrogram.raw.functions.messages import UploadImportedMedia
from pyrogram.raw.types import (
    DocumentAttributeAnimated, DocumentAttributeAudio, DocumentAttributeFilename,
    DocumentAttributeVideo, InputMediaUploadedDocument, InputMediaUploadedPhoto
)


@dataclass
class ChatHistory:
    messages: list["Message"]
    # Only valid for chats (not private messages):
    title: Optional[str]  # All chats have title
    photo: Optional["Photo"]  # If available


@dataclass
class Message:
    ts: datetime.datetime
    user: str
    text: str
    attachment: Optional["Media"] = None

    def __post_init__(self) -> None:
        if self.attachment is not None and self.text and not self.attachment.is_caption_allowed():
            msg = "Caption for attachment {} is not allowed: file='{}', caption='{}'".format(
                type(self.attachment).__name__, self.attachment.get_name(), self.text)
            raise ValueError(msg)


class Media(abc.ABC):
    def __init__(self, path: PurePath):
        self.path: PurePath = path

    def get_name(self) -> str:
        return str(self.path.name)

    @abc.abstractmethod
    def is_caption_allowed(self) -> bool: ...

    async def upload_media(self, app: Client, peer: InputPeer, import_id: int) -> MessageMedia:
        # Inspired by this function:
        # https://github.com/pyrogram/pyrogram/blob/37e0015463216a212b6417248a89c9133052ad07/pyrogram/methods/messages/send_video.py#L223
        prepared_media, file_id = await self._prepare_for_upload(app)
        while True:
            try:
                media: MessageMedia = await app.invoke(UploadImportedMedia(
                    peer=peer, import_id=import_id, file_name=self.get_name(), media=prepared_media))
            except FilePartMissing as e:
                await self._save_file(app, file_id=file_id, file_part=e.value)
            else:
                return media

    async def _save_file(self, app: Client, file_id: Optional[int] = None, file_part: int = 0) -> InputFile:
        input_file: InputFile = await app.save_file(self.path, file_id, file_part)  # type: ignore
        return input_file

    @abc.abstractmethod
    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]: ...


class Sticker(Media):
    def __init__(self, path: PurePath) -> None:
        if path.suffix == ".png":
            raise ValueError("Telegram doesn't support .png stickers. Try converting it to .webp")
        super().__init__(path)

    def is_caption_allowed(self) -> bool:
        return False  # However, I found out that caption for stickers works o_O

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        media = InputMediaUploadedDocument(
            mime_type=app.guess_mime_type(self.get_name()) or "image/webp",
            file=input_file,
            attributes=[
                DocumentAttributeFilename(file_name=self.get_name()),
            ]
        )
        return media, input_file.id


class Document(Media):
    def __init__(self, path: PurePath, title: str) -> None:
        super().__init__(path)
        self.title = title

    def is_caption_allowed(self) -> bool:
        return True

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        media = InputMediaUploadedDocument(
            file=input_file,
            force_file=True,
            mime_type=app.guess_mime_type(self.get_name()) or "application/zip",
            attributes=[
                DocumentAttributeFilename(file_name=self.title),
            ],
        )
        return media, input_file.id


class Photo(Media):
    def is_caption_allowed(self) -> bool:
        return True

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        return InputMediaUploadedPhoto(file=input_file), input_file.id


class Gif(Media):
    def __init__(self, path: PurePath, duration: int, width: int, height: int) -> None:
        if path.suffix == ".gif":
            raise ValueError("Telegram doesn't support real .gif files. Try converting it to .mp4")
        super().__init__(path)
        self.duration = duration
        self.width = width
        self.height = height

    def is_caption_allowed(self) -> bool:
        return False  # Actually, it works. But I don't think it's a good idea

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        media = InputMediaUploadedDocument(
            file=input_file,
            mime_type=app.guess_mime_type(self.get_name()) or "video/mp4",
            attributes=[
                DocumentAttributeVideo(duration=self.duration, w=self.width, h=self.height, supports_streaming=True),
                DocumentAttributeFilename(file_name=self.get_name()),
                DocumentAttributeAnimated(),
            ],
        )
        return media, input_file.id


class Video(Media):
    def __init__(self, path: PurePath, title: str, duration: int,
                 width: int, height: int, thumb_path: Optional[PurePath] = None) -> None:
        if path.suffix == ".webm":
            raise ValueError("Telegram doesn't consider .webm files as videos. Try converting it to .mp4")
        super().__init__(path)
        self.title = title
        self.duration = duration
        self.width = width
        self.height = height
        self.thumb_path = thumb_path

    def is_caption_allowed(self) -> bool:
        return True

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        thumb: Optional[InputFile] = None
        if self.thumb_path is not None:
            thumb = await app.save_file(self.thumb_path)  # type: ignore
        media = InputMediaUploadedDocument(
            file=input_file,
            thumb=thumb,  # type: ignore
            mime_type=app.guess_mime_type(self.get_name()) or "video/mp4",
            attributes=[
                DocumentAttributeVideo(duration=self.duration, w=self.width, h=self.height),
                DocumentAttributeFilename(file_name=self.title),
            ],
        )
        return media, input_file.id


class Audio(Media):
    def __init__(self, path: PurePath, performer: str, title: str, duration: int) -> None:
        super().__init__(path)
        self.performer = performer
        self.title = title
        self.duration = duration

    def is_caption_allowed(self) -> bool:
        return True

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        media = InputMediaUploadedDocument(
            file=input_file,
            mime_type=app.guess_mime_type(self.get_name()) or "audio/mpeg",
            attributes=[
                DocumentAttributeAudio(duration=self.duration, performer=self.performer, title=self.title),
                DocumentAttributeFilename(file_name=self.title),
            ]
        )
        return media, input_file.id


class Voice(Media):
    def __init__(self, path: PurePath, duration: int) -> None:
        if path.suffix == ".opus":
            raise ValueError("Telegram considers .opus files as audio, not voice message. Try converting it to .ogg")
        super().__init__(path)
        self.duration = duration

    def is_caption_allowed(self) -> bool:
        return False  # Actually, it works. But I don't think it's a good idea...

    async def _prepare_for_upload(self, app: Client) -> tuple[InputMedia, int]:
        input_file: InputFile = await self._save_file(app)
        media = InputMediaUploadedDocument(
            file=input_file,
            mime_type=app.guess_mime_type(self.get_name()) or "audio/mpeg",
            attributes=[
                DocumentAttributeAudio(duration=self.duration, voice=True),
            ]
        )
        return media, input_file.id
