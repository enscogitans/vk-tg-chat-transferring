import logging

from common.vk_client import VkClient
from config import Config
from tg_importer.storage import ITgHistoryStorage
from vk_exporter.storage import VkHistoryStorage
from vk_tg_converter.arguments import ConverterArguments
from vk_tg_converter.contacts.storage import ContactsStorage
from vk_tg_converter.controller import ConverterController
from vk_tg_converter.converters.history_converter_factory import HistoryConverterFactory
from vk_tg_converter.dummy_history_provider import DummyHistoryProvider
from vk_tg_converter.service import ConverterService


async def main(args: ConverterArguments, config: Config, vk_client: VkClient,
               tg_history_storage: ITgHistoryStorage, logger: logging.Logger) -> None:
    vk_api = vk_client.get_api()
    service = ConverterService(
        config.vk,
        ContactsStorage(),
        HistoryConverterFactory(vk_api, config, logger),
        DummyHistoryProvider(),
        VkHistoryStorage(),
        tg_history_storage,
    )
    controller = ConverterController(service)
    await controller(args)
