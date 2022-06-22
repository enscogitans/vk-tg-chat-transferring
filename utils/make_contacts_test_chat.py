from datetime import datetime
from typing import Optional

import tg_importer.types as tg
from common import TgClient
from tg_importer.importer import import_messages
from vk_tg_converter import ContactInfo


async def make_contacts_test_chat(
        client: TgClient, contacts: list[ContactInfo], chat_id: Optional[int], chat_title: Optional[str]) -> None:
    ts = datetime.now()
    tz = ts.astimezone().tzinfo
    assert tz is not None
    messages: list[tg.Message] = []
    for c in contacts:
        text = f"vk: {c.vk_name}\ntg: {c.tg_name_opt}"
        user = c.tg_name_opt or c.vk_name
        messages.append(tg.Message(ts=ts, user=user, text=text))
    async with client:
        await import_messages(
            client, tz, messages, max_tasks=1,
            disable_progress_bar=True, chat_id=chat_id, chat_title=chat_title)
