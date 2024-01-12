import abc
import asyncio
import io
from pathlib import Path

from pyrogram import utils
from pyrogram.raw.base import InputFile, InputPeer
from pyrogram.raw.functions.messages import \
    CheckHistoryImport, CheckHistoryImportPeer, InitHistoryImport, StartHistoryImport
from pyrogram.raw.types.messages import HistoryImport, HistoryImportParsed
from tqdm.asyncio import tqdm

import tg_importer.types as tg
from common.tg_client import TgClient
from tg_importer.encoder import IEncoder
from tg_importer.storage import ITgHistoryStorage


class ITgImporterService(abc.ABC):
    @abc.abstractmethod
    async def import_history(self, chat_id: int, tg_history_path: Path, disable_progress_bar: bool) -> None: ...


class TgImporterService(ITgImporterService):
    def __init__(self, tg_client: TgClient, tg_history_storage: ITgHistoryStorage,
                 encoder: IEncoder, max_simultaneously_uploaded_files: int) -> None:
        self.tg_client = tg_client
        self.tg_history_storage = tg_history_storage
        self.encoder = encoder
        self.max_simultaneously_uploaded_files = max_simultaneously_uploaded_files

    async def import_history(self, chat_id: int, tg_history_path: Path, disable_progress_bar: bool) -> None:
        peer_type: str = utils.get_peer_type(chat_id)
        if peer_type not in ("channel", "user"):  # supergroup or private chat
            raise ValueError(f"Invalid peer: only user and channel (supergroup) are supported. Provided {peer_type}")
        tg_history = self.tg_history_storage.load_history(tg_history_path)
        is_peer_group: bool = peer_type == "channel"
        if is_peer_group != tg_history.is_group:
            # In both cases Telegram will fail with error: 400 IMPORT_PEER_TYPE_INVALID
            raise ValueError(f"Invalid peer: peer and history must be of same type, got "
                             f"peer is_group={is_peer_group}, history is_group={tg_history.is_group}")
        success = await self._import_messages_inner(chat_id, tg_history, disable_progress_bar)
        if success:
            print("Import finished successfully")
        else:
            print("Something went wrong")

    async def _import_messages_inner(self, chat_id: int, tg_history: tg.ChatHistory,
                                     disable_progress_bar: bool) -> bool:
        """https://core.telegram.org/api/import"""

        import_data: str = self.encoder.encode(tg_history)
        max_lines_head = 50
        import_head: str = "\n".join(import_data.split("\n", maxsplit=max_lines_head)[:max_lines_head])
        import_head += "\n"
        media_files: list[tg.Media] = [msg.attachment for msg in tg_history.messages if msg.attachment is not None]

        import_parsed: HistoryImportParsed = await self.tg_client.invoke(CheckHistoryImport(import_head=import_head))
        # If Encoder works correctly parsed chat type and history chat type should be the same
        # I'm not sure whether it is awful if they differ. Let's check just in case
        assert import_parsed.pm or import_parsed.group, "Telegram sees unknown chat type"
        assert tg_history.is_group == import_parsed.group, f"{tg_history.is_group=}, {import_parsed.group=}"

        peer: InputPeer = await self.tg_client.resolve_peer(chat_id)  # type: ignore
        await self.tg_client.invoke(CheckHistoryImportPeer(peer=peer))  # CheckedHistoryImportPeer

        with io.BytesIO(import_data.encode()) as import_file:
            setattr(import_file, "name", "_chat.txt")  # 'name' is required by tg_client.save_file
            uploaded_import_file: InputFile = await self.tg_client.save_file(import_file)
        history_import: HistoryImport = await self.tg_client.invoke(
            InitHistoryImport(peer=peer, file=uploaded_import_file, media_count=len(media_files)))
        import_id: int = history_import.id

        semaphore = asyncio.Semaphore(self.max_simultaneously_uploaded_files)

        async def upload(media: tg.Media) -> None:
            async with semaphore:
                await media.upload_media(self.tg_client, peer, import_id)

        await tqdm.gather(*map(upload, media_files), leave=True, disable=disable_progress_bar, desc="Uploading media")

        success: bool = await self.tg_client.invoke(StartHistoryImport(peer=peer, import_id=import_id))
        return success
