import argparse
import asyncio
import logging
import os
from types import UnionType
from typing import cast

import chats
import login
import tg_importer
import vk_exporter
import vk_tg_converter
import vk_tg_converter.contacts
from arguments import MainArgumentsParser, MainArguments, \
    LoginArguments, VkExporterArguments, ContactsArguments, ConverterArguments, ChatsArguments, TgImporterArguments
from common.tg_client import TgClient
from common.vk_client import VkClient
from config import Config
from tg_importer.storage import ITgHistoryStorage, TgHistoryStorage


def make_logger(name: str) -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(name)s - %(message)s"))
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    return logger


def get_arguments(config: Config, tg_history_storage: ITgHistoryStorage) -> MainArguments:
    parser = argparse.ArgumentParser()
    main_parser = MainArgumentsParser.fill_parser(parser, config)
    namespace = parser.parse_args()
    return main_parser.parse_arguments(namespace, tg_history_storage)


async def run_module(args: MainArguments, config: Config, vk_client: VkClient,
                     tg_client: TgClient, tg_history_storage: ITgHistoryStorage) -> None:
    if isinstance(args, cast(UnionType, LoginArguments)):
        return await login.main(args, config)  # type: ignore[arg-type]
    if isinstance(args, VkExporterArguments):
        return vk_exporter.main(args, vk_client)
    if isinstance(args, cast(UnionType, ContactsArguments)):
        return await vk_tg_converter.contacts.main(args, vk_client, tg_client)  # type: ignore[arg-type]
    if isinstance(args, ConverterArguments):
        return await vk_tg_converter.main(args, config, vk_client, tg_history_storage, make_logger("converter"))
    if isinstance(args, cast(UnionType, ChatsArguments)):
        return await chats.main(args, tg_client)  # type: ignore[arg-type]
    if isinstance(args, TgImporterArguments):
        return await tg_importer.main(args, config.tg, tg_client, tg_history_storage)
    raise ValueError(f"Unexpected arguments: {args}")


async def main() -> None:
    config = Config()
    tg_history_storage = TgHistoryStorage()

    args = get_arguments(config, tg_history_storage)

    vk_client = VkClient(config.vk)
    tg_client = TgClient(config.tg)

    await run_module(args, config, vk_client, tg_client, tg_history_storage)


if __name__ == "__main__":
    if os.name == "nt":  # Windows
        # https://stackoverflow.com/questions/68123296/asyncio-throws-runtime-error-with-exception-ignored
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore
    asyncio.run(main())
