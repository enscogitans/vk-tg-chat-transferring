from pathlib import Path
from typing import Optional

from pyrogram.enums import ChatType
from pyrogram.types import Chat, User

from common import TgClient
from vk_tg_converter import ContactInfo


async def list_chats(client: TgClient) -> None:
    async for dialog in client.get_dialogs():  # type: ignore
        name: str = dialog.chat.title or ""
        if not name:
            first_name: str = dialog.chat.first_name or ""
            last_name: str = dialog.chat.last_name or ""
            name = str.strip(first_name + " " + last_name)
        print(f"id={dialog.chat.id: <14}\tname='{name}'")


async def set_photo(client: TgClient, chat_id: int, photo_path: Path) -> None:
    chat = await client.get_chat(chat_id)
    assert isinstance(chat, Chat), f"You are not a member of the chat {chat_id}"
    await chat.set_photo(photo=str(photo_path))
    print(f"Successfully set photo to '{photo_path}'")


async def set_is_mute_chat(client: TgClient, chat_id: int, *, is_mute: bool) -> None:
    chat = await client.get_chat(chat_id)
    assert isinstance(chat, Chat), f"You are not a member of the chat {chat_id}"
    assert chat.type in (ChatType.GROUP, ChatType.SUPERGROUP), f"Chat {chat_id} is not a group or supergroup"
    assert chat.permissions is not None, "Groups and supergroups have this field set"

    if chat.permissions.can_send_messages != is_mute:
        if is_mute:
            print("The chat is already muted")
        else:
            print("The chat is already unmuted")
        return

    new_permissions = chat.permissions
    new_permissions.can_send_messages = \
        new_permissions.can_send_media_messages = \
        new_permissions.can_send_other_messages = \
        new_permissions.can_send_polls = \
        new_permissions.can_add_web_page_previews = not is_mute

    await client.set_chat_permissions(chat.id, new_permissions)
    if is_mute:
        print("Prohibited sending messages to the chat")
    else:
        print("Allowed sending messages to the chat")


async def invite_users(client: TgClient, chat_id: int, contacts: list[ContactInfo]) -> None:
    added_contacts, missing_contacts = await _add_users_to_chat(client, chat_id, contacts)

    if not missing_contacts:
        print("Successfully added all users")
        return

    print("Failed to add some users to the chat:")
    for i, c in enumerate(missing_contacts, start=1):
        print(f"  {i}. tg_name='{c.tg_name_opt}'", f"vk_name='{c.vk_name}'", f"vk_id={c.vk_id}", sep="\t")

    print("\nAdded users:")
    for i, c in enumerate(added_contacts, start=1):
        print(f"  {i}. tg_name='{c.tg_name_opt}'", f"vk_name='{c.vk_name}'", f"vk_id={c.vk_id}", sep="\t")


async def create_chat(client: TgClient, title: str, contacts: list[ContactInfo],
                      mute_all: bool, photo_path: Optional[Path]) -> None:
    chat = await client.create_supergroup(title)
    print("Created chat with id =", chat.id)
    if mute_all:
        await set_is_mute_chat(client, chat.id, is_mute=True)
    if contacts:
        await invite_users(client, chat.id, contacts)
    if photo_path is not None:
        await set_photo(client, chat.id, photo_path)


async def _add_users_to_chat(
        client: TgClient, chat_id: int, contacts: list[ContactInfo]) -> tuple[list[ContactInfo], list[ContactInfo]]:
    contact_to_id: dict[ContactInfo, Optional[int]] = await _get_contact_to_user_id_mapping(client, contacts)
    user_ids_to_add: list[int] = [user_id for user_id in contact_to_id.values() if user_id is not None]
    await client.add_chat_members(chat_id, user_ids_to_add)  # type: ignore

    chat_members_generator = client.get_chat_members(chat_id)
    assert chat_members_generator is not None
    chat_members_names: set[str] = {_make_name(member.user) async for member in chat_members_generator}
    added_contacts = [contact for contact in contacts if contact.tg_name_opt in chat_members_names]
    missing_contacts = [contact for contact in contacts if contact.tg_name_opt not in chat_members_names]
    return added_contacts, missing_contacts


async def _get_contact_to_user_id_mapping(
        client: TgClient, prepared_contacts: list[ContactInfo]) -> dict[ContactInfo, Optional[int]]:
    tg_name_to_id: dict[str, Optional[int]] = dict.fromkeys(c.tg_name_opt for c in prepared_contacts if c.tg_name_opt)

    for contact in await client.get_contacts():
        name = _make_name(contact)
        if name in tg_name_to_id:
            assert tg_name_to_id[name] is None, f"'{name}' appears in contacts several times"
            tg_name_to_id[name] = contact.id

    result: dict[ContactInfo, Optional[int]] = dict.fromkeys(prepared_contacts)
    for prepared_contact in result:
        if prepared_contact.tg_name_opt is not None:
            result[prepared_contact] = tg_name_to_id[prepared_contact.tg_name_opt]
    return result


def _make_name(tg_user: User) -> str:
    # TODO: move to common
    first_name: str = tg_user.first_name or ""
    last_name: str = tg_user.last_name or ""
    return str.strip(first_name + " " + last_name)
