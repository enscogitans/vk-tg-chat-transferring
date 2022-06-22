import argparse
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


def fill_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", metavar="PATH", help="Path to vk messages file")
    parser.add_argument("--output", metavar="PATH", help="File to export tg messages in")
    parser.add_argument("--media-export-dir", metavar="PATH", help="Directory to export media in. Must not exist")
    parser.add_argument("--no-progress-bar", action="store_true")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--contacts", metavar="PATH", help="Path to file with vk-tg contacts mapping")
    group.add_argument("--skip-contacts", action="store_true", help="Do not use contacts mapping")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace, config: Config, vk_client: VkClient) -> None:
    contacts_mapping_file: Optional[Path] = None
    if not args.skip_contacts:
        contacts_mapping_file = Path(args.contacts or config.default_contacts_mapping_file)
    vk_messages_file = Path(args.input or config.vk_default_export_file)
    tg_messages_export_file = Path(args.output or config.tg_default_export_file)
    tg_media_export_dir = Path(args.media_export_dir or config.tg_default_media_export_dir)

    if contacts_mapping_file and not contacts_mapping_file.exists():
        parser.error(f"Contacts mapping file does not exist: '{contacts_mapping_file}'")
    if not vk_messages_file.exists():
        parser.error(f"Vk messages file does not exist: '{vk_messages_file}'")
    if tg_messages_export_file.exists():
        parser.error(f"Telegram messages export file already exists: '{tg_messages_export_file}'")
    if tg_media_export_dir.exists() and any(True for _ in tg_media_export_dir.iterdir()):
        parser.error(f"Telegram media export directory is not empty: '{tg_media_export_dir}'")

    prepared_contacts: Optional[list[ContactInfo]] = None
    if contacts_mapping_file is not None:
        prepared_contacts = load_contacts_from_yaml(contacts_mapping_file, normalize=True)
    with vk_messages_file.open("rb") as f:
        vk_messages: list[vk.Message] = pickle.load(f)
        assert isinstance(vk_messages, list) and all(isinstance(msg, vk.Message) for msg in vk_messages)

    tg_messages: list[tg.Message] = await convert_messages(
        vk_client.get_api(), config.vk, vk_messages, prepared_contacts, tg_media_export_dir, args.no_progress_bar)

    with tg_messages_export_file.open("wb") as f:
        pickle.dump(tg_messages, f)
    print(f"Success. Check file '{tg_messages_export_file}' and directory '{tg_media_export_dir}'")
