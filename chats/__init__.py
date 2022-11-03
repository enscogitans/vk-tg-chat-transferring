import argparse
from pathlib import Path

from common import TgClient
from config import Config
from chats.chats import list_chats, create_chat, set_is_mute_chat, invite_users
from vk_tg_converter import load_contacts_from_yaml, ContactInfo


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    subparsers = parser.add_subparsers(dest="app", required=True)

    subparsers.add_parser("list")

    mute_parser = subparsers.add_parser("mute")
    mute_parser.add_argument("chat", metavar="CHAT_ID")

    unmute_parser = subparsers.add_parser("unmute")
    unmute_parser.add_argument("chat", metavar="CHAT_ID")

    invite_parser = subparsers.add_parser("invite")
    invite_parser.add_argument("chat")
    invite_parser.add_argument("--contacts", type=Path, default=config.default_contacts_mapping_file,
                               metavar="CONTACTS_FILE", help="Path to contacts mapping data")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--title", required=True, help="Name of the created chat")
    create_parser.add_argument("--invite", nargs="?", type=Path, const=config.default_contacts_mapping_file,
                               metavar="CONTACTS_FILE", help="Invite users listed in file with contacts")
    create_parser.add_argument("--mute", action="store_true", help="Mute all users on chat creation")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace, tg_client: TgClient) -> None:
    match args.app:
        case "list":
            async with tg_client:
                await list_chats(tg_client)
        case "mute":
            async with tg_client:
                await set_is_mute_chat(tg_client, args.chat, is_mute=True)
        case "unmute":
            async with tg_client:
                await set_is_mute_chat(tg_client, args.chat, is_mute=False)
        case "invite":
            contacts_mapping_file: Path = args.contacts
            if not contacts_mapping_file.exists():
                parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
            contacts_to_invite = load_contacts_from_yaml(contacts_mapping_file, empty_as_none=True)
            async with tg_client:
                await invite_users(tg_client, args.chat, contacts_to_invite)
        case "create":
            contacts_to_invite: list[ContactInfo] = []
            if args.contacts is not None:
                contacts_mapping_file: Path = args.contacts
                if not contacts_mapping_file.exists():
                    parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
                contacts_to_invite = load_contacts_from_yaml(contacts_mapping_file, empty_as_none=True)
            async with tg_client:
                await create_chat(tg_client, args.title, contacts_to_invite, args.mute)
        case app:
            raise ValueError(f"Unexpected app {app}")
