import argparse
from pathlib import Path

from common.tg_client import TgClient
from common.vk_client import VkClient
from config import Config
from vk_tg_converter.contacts.contacts_preprocessor import \
    check_tg_names_in_mapping_file, list_contacts, make_contacts_mapping_file
from vk_tg_converter.contacts.username_manager import UsernameManagerV1


def fill_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="submodule", required=True)

    subparsers.add_parser("list")

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--input", metavar="PATH", help="Path to vk messages file")
    prepare_parser.add_argument("--output", metavar="PATH", help="File to export contacts mapping data in")

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--input", metavar="PATH", help="Path to contacts mapping data")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace,
               config: Config, vk_client: VkClient, tg_client: TgClient) -> None:
    async with tg_client:
        match args.submodule:
            case "list":
                await list_contacts(tg_client)
            case "prepare":
                input_file = Path(args.input or config.vk_default_export_file)
                output_file = Path(args.output or config.default_contacts_mapping_file)
                if not input_file.exists():
                    parser.error(f"Input file does not exist: '{input_file}'")
                if output_file.exists():
                    parser.error(f"Output file already exists: '{output_file}'")
                um = UsernameManagerV1(vk_client.get_api())
                await make_contacts_mapping_file(output_file, input_file, tg_client, um)
            case "check":
                mapping_file = Path(args.input or config.default_contacts_mapping_file)
                if not mapping_file.exists():
                    parser.error(f"File with mapping data not found: '{mapping_file}'")
                await check_tg_names_in_mapping_file(mapping_file, tg_client)
            case submodule:
                raise ValueError(f"Unexpected submodule {submodule}")
