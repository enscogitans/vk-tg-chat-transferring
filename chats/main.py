from chats.arguments import ChatsArguments
from chats.controller import ChatsController
from chats.service import ChatsService
from common.tg_client import TgClient
from vk_tg_converter.contacts.storage import ContactsStorage


async def main(args: ChatsArguments, tg_client: TgClient) -> None:
    async with tg_client:
        service = ChatsService(
            tg_client,
            ContactsStorage(),
        )
        controller = ChatsController(service)
        await controller(args)
