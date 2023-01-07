import argparse

from common.tg_client import TgClient
from common.vk_client import VkClient
from vk_exporter.storage import VkHistoryStorage
from vk_tg_converter.contacts.arguments import get_arguments
from vk_tg_converter.contacts.controller import ContactsController
from vk_tg_converter.contacts.service import ContactsService
from vk_tg_converter.contacts.storage import ContactsStorage
from vk_tg_converter.contacts.username_manager import UsernameManagerV1


async def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace,
               vk_client: VkClient, tg_client: TgClient) -> None:
    vk_api = vk_client.get_api()
    service = ContactsService(
        UsernameManagerV1(vk_api, prepared_contacts=None),
        tg_client,
        VkHistoryStorage(),
        ContactsStorage(),
    )

    controller = ContactsController(service)

    args = get_arguments(parser, namespace)
    await controller(args)
