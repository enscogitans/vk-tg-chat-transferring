import argparse
import datetime
import pickle
from pathlib import Path
from typing import Optional

import tg_importer.types as tg
import vk_exporter.types as vk
from common.vk_client import VkClient
from config import Config
from vk_tg_converter.contacts.contacts_preprocessor import load_contacts_from_yaml
from vk_tg_converter.contacts.username_manager import ContactInfo
from vk_tg_converter.converter import convert_messages


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    group_1 = parser.add_mutually_exclusive_group()
    group_1.add_argument("--input", default=config.vk_default_export_file,
                         metavar="PATH", help="Path to vk messages file")
    group_1.add_argument("--dummy-input", action="store_true",
                         help="Use dummy tg messages instead of real conversion. "
                              "You must provide vk-tg contacts mapping")

    parser.add_argument("--output", default=config.tg_default_export_file,
                        metavar="PATH", help="File to export tg messages in")
    parser.add_argument("--media-export-dir", default=config.tg_default_media_export_dir,
                        metavar="PATH", help="Directory to export media in. Must not exist")
    parser.add_argument("--no-progress-bar", action="store_true")

    group_2 = parser.add_mutually_exclusive_group()
    group_2.add_argument("--contacts", default=config.default_contacts_mapping_file,
                         metavar="PATH", help="Path to file with vk-tg contacts mapping")
    group_2.add_argument("--skip-contacts", action="store_true", help="Do not use contacts mapping")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace,
               vk_config: Config.Vk, vk_client: VkClient) -> None:
    if args.dummy_input and args.skip_contacts:
        parser.error(f"You must provide contacts mapping if you use --dummy-input")

    contacts_mapping_file: Optional[Path] = None
    if not args.skip_contacts:
        contacts_mapping_file = Path(args.contacts)
    vk_messages_file_opt = None if args.dummy_input else Path(args.input)
    tg_messages_export_file = Path(args.output)
    tg_media_export_dir = Path(args.media_export_dir)

    if contacts_mapping_file and not contacts_mapping_file.exists():
        parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
    if vk_messages_file_opt is not None and not vk_messages_file_opt.exists():
        parser.error(f"Vk messages file does not exist: '{vk_messages_file_opt}'")
    if tg_messages_export_file.exists():
        parser.error(f"Telegram messages export file already exists: '{tg_messages_export_file}'")
    if tg_media_export_dir.exists() and any(True for _ in tg_media_export_dir.iterdir()):
        parser.error(f"Telegram media export directory is not empty: '{tg_media_export_dir}'")

    prepared_contacts: Optional[list[ContactInfo]] = None
    if contacts_mapping_file is not None:
        prepared_contacts = load_contacts_from_yaml(contacts_mapping_file, empty_as_none=True)

    tg_messages: list[tg.Message]
    if args.dummy_input:
        assert prepared_contacts is not None, "No contacts despite using --dummy-input"
        tg_messages = _make_dummy_tg_messages(prepared_contacts)
    else:
        assert vk_messages_file_opt is not None
        with vk_messages_file_opt.open("rb") as f:
            vk_messages: list[vk.Message] = pickle.load(f)
            assert isinstance(vk_messages, list) and all(isinstance(msg, vk.Message) for msg in vk_messages)
        tg_messages = await convert_messages(
            vk_client.get_api(), vk_config, vk_messages, prepared_contacts, tg_media_export_dir, args.no_progress_bar)

    with tg_messages_export_file.open("wb") as f:
        pickle.dump(tg_messages, f)
    print(f"Success. Check file '{tg_messages_export_file}' and directory '{tg_media_export_dir}'")


def _make_dummy_tg_messages(contacts: list[ContactInfo]) -> list[tg.Message]:
    ts = datetime.datetime.now()
    tg_messages: list[tg.Message] = []
    for contact in contacts:
        user = contact.tg_name_opt or contact.vk_name
        text = f"vk: {contact.vk_name}\ntg: {contact.tg_name_opt}"
        tg_messages.append(tg.Message(ts=ts, user=user, text=text))
    return tg_messages
