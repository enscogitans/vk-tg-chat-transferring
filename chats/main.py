import argparse

from chats.arguments import get_arguments
from chats.controller import ChatsController
from chats.service import ChatsService
from common.tg_client import TgClient
from tg_importer.storage import TgHistoryStorage
from vk_tg_converter.contacts.storage import ContactsStorage


async def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace, tg_client: TgClient) -> None:
    tg_history_storage = TgHistoryStorage()
    args = get_arguments(parser, namespace, tg_history_storage)

    async with tg_client:
        service = ChatsService(
            tg_client,
            ContactsStorage(),
        )
        controller = ChatsController(service)
        await controller(args)
