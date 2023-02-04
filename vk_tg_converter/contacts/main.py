from common.tg_client import TgClient
from common.user_io import ConsoleUserOutput
from common.vk_client import VkClient
from vk_exporter.storage import VkHistoryStorage
from vk_tg_converter.contacts.arguments import ContactsArguments
from vk_tg_converter.contacts.controller import ContactsController
from vk_tg_converter.contacts.service import ContactsService
from vk_tg_converter.contacts.storage import ContactsStorage
from vk_tg_converter.contacts.tg_client_adaptor import TgClientAdaptor
from vk_tg_converter.contacts.username_manager import UsernameManager


async def main(args: ContactsArguments, vk_client: VkClient, tg_client: TgClient) -> None:
    vk_api = vk_client.get_api()
    service = ContactsService(
        UsernameManager(vk_api, prepared_contacts=None),
        TgClientAdaptor(tg_client),
        VkHistoryStorage(),
        ContactsStorage(),
        ConsoleUserOutput(),
    )
    controller = ContactsController(service)
    await controller(args)
