from common import TgClient


async def list_chats(client: TgClient) -> None:
    async with client:
        async for dialog in client.get_dialogs():  # type: ignore
            name: str = dialog.chat.title or ""
            if not name:
                first_name: str = dialog.chat.first_name or ""
                last_name: str = dialog.chat.last_name or ""
                name = str.strip(first_name + " " + last_name)
            print(f"id={dialog.chat.id: <14}\tname='{name}'")
