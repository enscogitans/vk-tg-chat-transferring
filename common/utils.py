from pyrogram.types import Chat, User


def get_full_name(tg_entity: Chat | User) -> str:
    first_name: str = tg_entity.first_name or ""
    last_name: str = tg_entity.last_name or ""
    return str.strip(first_name + " " + last_name)
