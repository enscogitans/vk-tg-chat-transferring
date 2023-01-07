import argparse

from common import VkClient
from config import Config
from tg_importer.storage import TgHistoryStorage
from vk_exporter.storage import VkHistoryStorage
from vk_tg_converter.arguments import ConverterArguments
from vk_tg_converter.contacts.storage import ContactsStorage
from vk_tg_converter.controller import ConverterController
from vk_tg_converter.converters.history_converter_factory import HistoryConverterFactory
from vk_tg_converter.dummy_history_provider import DummyHistoryProvider
from vk_tg_converter.service import ConverterService


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    ConverterArguments.fill_parser(parser, config)


async def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace,
               config: Config, vk_client: VkClient) -> None:
    args = ConverterArguments(parser, namespace)

    vk_api = vk_client.get_api()
    service = ConverterService(
        config.vk,
        ContactsStorage(),
        HistoryConverterFactory(vk_api, config),
        DummyHistoryProvider(),
        VkHistoryStorage(),
        TgHistoryStorage(),
    )

    controller = ConverterController(service)
    await controller(args)
