import argparse
from pathlib import Path

from common.tg_client import TgClient
from config import Config
from utils.list_chats import list_chats
from utils.make_contacts_test_chat import make_contacts_test_chat
from vk_tg_converter import load_contacts_from_yaml


def fill_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="app", required=True)

    subparsers.add_parser("list-chats", help="Print all telegram chats with their ids")

    test_contacts_parser = subparsers.add_parser("test-contacts", help=(
        "Verify telegram correctly maps names to real contacts. "
        "Pretend each contact has written a message and import these messages into the chat"))
    test_contacts_parser.add_argument("--contacts", metavar="PATH", help="Path to contacts mapping data")
    me_group = test_contacts_parser.add_mutually_exclusive_group(required=True)
    me_group.add_argument("--chat", type=int, metavar="ID", help="Chat to send messages to")
    me_group.add_argument("--name", help="Name of the chat to create and send messages to")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace, config: Config, tg_client: TgClient) -> None:
    match args.app:
        case "list-chats":
            await list_chats(tg_client)
        case "test-contacts":
            contacts_mapping_file = Path(args.contacts or config.default_contacts_mapping_file)
            if not contacts_mapping_file.exists():
                parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
            contacts = load_contacts_from_yaml(contacts_mapping_file, normalize=True)
            await make_contacts_test_chat(tg_client, contacts, args.chat, args.name)
        case app:
            raise ValueError(f"Unexpected app {app}")
