import argparse
import asyncio
import os

import login
import tg_importer
import utils
import vk_exporter
import vk_tg_converter
import vk_tg_converter.contacts
from common import TgClient, VkClient
from config import Config


async def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="module", required=True)

    login_parser = subparsers.add_parser("login")
    login.fill_parser(login_parser)

    export_parser = subparsers.add_parser("export")
    vk_exporter.fill_parser(export_parser)

    contacts_parser = subparsers.add_parser("contacts")
    vk_tg_converter.contacts.fill_parser(contacts_parser)

    convert_parser = subparsers.add_parser("convert")
    vk_tg_converter.fill_parser(convert_parser)

    import_parser = subparsers.add_parser("import")
    tg_importer.fill_parser(import_parser)

    utils_parser = subparsers.add_parser("utils")
    utils.fill_parser(utils_parser)

    args = parser.parse_args()
    config = Config()
    match args.module:
        case "login":
            await login.main(args, config)
        case "export":
            vk_exporter.main(export_parser, args, config, VkClient(config.vk))
        case "contacts":
            await vk_tg_converter.contacts.main(contacts_parser, args, config, VkClient(config.vk), TgClient(config.tg))
        case "convert":
            await vk_tg_converter.main(convert_parser, args, config, VkClient(config.vk))
        case "import":
            await tg_importer.main(import_parser, args, config, TgClient(config.tg))
        case "utils":
            await utils.main(utils_parser, args, config, TgClient(config.tg))
        case module:
            raise ValueError(f"Unexpected module {module}")


if __name__ == "__main__":
    if os.name == "nt":  # Windows
        # https://stackoverflow.com/questions/68123296/asyncio-throws-runtime-error-with-exception-ignored
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore
    asyncio.run(main())
