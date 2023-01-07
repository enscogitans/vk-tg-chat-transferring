import argparse

from common.tg_client import TgClient
from config import Config
from tg_importer.arguments import TgImporterArguments
from tg_importer.controller import TgImporterController
from tg_importer.encoder import WhatsAppAndroidEncoder
from tg_importer.service import TgImporterService
from tg_importer.storage import TgHistoryStorage


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    TgImporterArguments.fill_parser(parser, config)


async def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace,
               tg_config: Config.Telegram, tg_client: TgClient) -> None:
    args = TgImporterArguments(parser, namespace)

    tg_history_storage = TgHistoryStorage()
    encoder = WhatsAppAndroidEncoder(tg_config.timezone)

    async with tg_client:
        service = TgImporterService(
            tg_client,
            tg_history_storage,
            encoder,
            tg_config.max_simultaneously_uploaded_files,
        )
        controller = TgImporterController(service)
        await controller(args)
