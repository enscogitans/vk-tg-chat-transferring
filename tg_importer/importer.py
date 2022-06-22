import asyncio
import datetime
import io
from typing import Optional

from pyrogram import utils
from pyrogram.raw.base import InputFile, InputPeer
from pyrogram.raw.functions.messages import \
    CheckHistoryImport, CheckHistoryImportPeer, InitHistoryImport, StartHistoryImport
from pyrogram.raw.types.messages import HistoryImport
from tqdm.asyncio import tqdm

import tg_importer.types as tg
from common.tg_client import TgClient
from tg_importer.encoder import Encoder, WhatsAppAndroidEncoder


async def import_messages(
        tg_client: TgClient,
        tg_timezone: datetime.tzinfo,
        tg_messages: list[tg.Message],
        max_tasks: int,  # Maximum number of files being uploaded simultaneously
        disable_progress_bar: bool,
        chat_id: Optional[int],
        chat_title: Optional[str]) -> bool:
    if (chat_id is None) == (chat_title is None):
        raise ValueError("Provide either 'peer_id' or 'chat_title'")

    if chat_id is None:
        assert chat_title is not None
        chat = await tg_client.create_supergroup(chat_title)
        chat_id = chat.id
        # TODO: add logger, print chat_id

    peer_type: str = utils.get_peer_type(chat_id)
    if peer_type == "channel":  # supergroup
        is_group = True
    elif peer_type == "user":
        is_group = False
    else:
        raise ValueError(f"Invalid peer, only user and channel (supergroup) are supported. Provided {peer_type}")

    encoder = WhatsAppAndroidEncoder(tg_timezone, is_group)
    success: bool = \
        await _import_messages_inner(tg_client, tg_messages, encoder, chat_id, max_tasks, disable_progress_bar)
    return success


async def _import_messages_inner(
        tg_client: TgClient, messages: list[tg.Message], encoder: Encoder,
        chat_id: int, max_tasks: int, disable_progress_bar: bool) -> bool:
    """https://core.telegram.org/api/import"""

    import_data: str = encoder.encode(messages)
    max_lines_head = 50
    import_head: str = "\n".join(import_data.split("\n", maxsplit=max_lines_head)[:max_lines_head])
    media_files: list[tg.Media] = [msg.attachment for msg in messages if msg.attachment is not None]

    await tg_client.invoke(CheckHistoryImport(import_head=import_head))  # HistoryImportParsed

    peer: InputPeer = await tg_client.resolve_peer(chat_id)  # type: ignore
    await tg_client.invoke(CheckHistoryImportPeer(peer=peer))  # CheckedHistoryImportPeer

    with io.BytesIO(import_data.encode()) as import_file:
        setattr(import_file, "name", "_chat.txt")  # 'name' is required by tg_client.save_file
        uploaded_import_file: InputFile = await tg_client.save_file(import_file)
    history_import: HistoryImport = await tg_client.invoke(
        InitHistoryImport(peer=peer, file=uploaded_import_file, media_count=len(media_files)))
    import_id: int = history_import.id

    semaphore = asyncio.Semaphore(max_tasks)

    async def upload(media: tg.Media) -> None:
        async with semaphore:
            await media.upload_media(tg_client, peer, import_id)

    await tqdm.gather(*map(upload, media_files), leave=True, disable=disable_progress_bar, desc="Uploading media")

    success: bool = await tg_client.invoke(StartHistoryImport(peer=peer, import_id=import_id))
    return success
