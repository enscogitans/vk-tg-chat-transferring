import argparse
import pickle
from pathlib import Path
from typing import Optional

from chats.chats import list_chats, create_chat, set_is_mute_chat, invite_users, set_photo
from common import TgClient, Sentinel
from config import Config
from tg_importer.types import ChatHistory
from vk_tg_converter.contacts.storage import ContactsStorage
from vk_tg_converter.contacts.username_manager import ContactInfo


def load_contacts_from_yaml(file_path: Path, *, empty_as_none: bool = True) -> list[ContactInfo]:
    return ContactsStorage.load_contacts(file_path, empty_as_none=empty_as_none)


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    subparsers = parser.add_subparsers(dest="app", required=True)

    subparsers.add_parser("list")

    set_photo_parser = subparsers.add_parser("set-photo")
    set_photo_parser.add_argument("chat", metavar="CHAT_ID")
    set_photo_parser.add_argument("--photo", required=True, type=Path, metavar="PHOTO_PATH")

    mute_parser = subparsers.add_parser("mute")
    mute_parser.add_argument("chat", metavar="CHAT_ID")

    unmute_parser = subparsers.add_parser("unmute")
    unmute_parser.add_argument("chat", metavar="CHAT_ID")

    invite_parser = subparsers.add_parser("invite")
    invite_parser.add_argument("chat")
    invite_parser.add_argument("--contacts", type=Path, default=config.default_contacts_mapping_file,
                               metavar="CONTACTS_FILE", help="Path to contacts mapping data")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--use-history", nargs="?", type=Path, const=config.tg_default_export_file,
                               metavar="TG_HISTORY_FILE", help="Get chat info from history file")
    create_parser.add_argument("--title", help="Name of the created chat")
    create_parser.add_argument("--photo", nargs="?", const=Sentinel(), type=Path,
                               metavar="PHOTO_PATH", help="Set chat photo")
    create_parser.add_argument("--invite", nargs="?", type=Path, const=config.default_contacts_mapping_file,
                               metavar="CONTACTS_FILE", help="Invite users listed in file with contacts")
    create_parser.add_argument("--mute", action="store_true", help="Mute all users on chat creation")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace, tg_client: TgClient) -> None:
    match args.app:
        case "list":
            async with tg_client:
                await list_chats(tg_client)
        case "set-photo":
            if not args.photo.exists():
                parser.error(f"Path '{args.photo}' does not exist")
            async with tg_client:
                await set_photo(tg_client, args.chat, args.photo)
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
            contacts_to_invite: list[ContactInfo] = load_contacts_from_yaml(contacts_mapping_file, empty_as_none=True)
            async with tg_client:
                await invite_users(tg_client, args.chat, contacts_to_invite)
        case "create":
            # TODO: get contacts from history file
            contacts_to_invite = []
            if args.invite is not None:
                contacts_mapping_file = args.invite
                if not contacts_mapping_file.exists():
                    parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
                contacts_to_invite = load_contacts_from_yaml(contacts_mapping_file, empty_as_none=True)

            title: Optional[str] = args.title
            use_photo: bool = args.photo is not None
            photo_path: Optional[Path] = None
            if use_photo and args.photo is not Sentinel():
                photo_path = args.photo
                assert isinstance(photo_path, Path)
                if not photo_path.exists():
                    parser.error(f"Photo {photo_path} does not exist")
            if title is None or (use_photo and photo_path is None):
                if args.use_history is None:
                    if title is None:
                        parser.error("Neither title provided nor --use-history used")
                    else:
                        parser.error("Neither photo path provided nor --use-history used")
                history_path: Path = args.use_history
                if not history_path.exists():
                    parser.error(f"History path {history_path} does not exist")
                with history_path.open("rb") as file:
                    history = pickle.load(file)
                assert isinstance(history, ChatHistory), history
                if title is None:
                    title = history.title_opt
                if use_photo and photo_path is None:
                    photo_path = None if history.photo_opt is None else Path(history.photo_opt.path)

            assert title is not None
            async with tg_client:
                await create_chat(tg_client, title, contacts_to_invite, args.mute, photo_path)
        case app:
            raise ValueError(f"Unexpected app {app}")
