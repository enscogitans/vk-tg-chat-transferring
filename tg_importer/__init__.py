import argparse
import pickle
from pathlib import Path

import tg_importer.types as tg
from common.tg_client import TgClient
from config import Config
from tg_importer.importer import import_messages


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    me_group = parser.add_mutually_exclusive_group(required=True)
    me_group.add_argument("--chat", type=int, metavar="ID", help="Chat to import messages into")
    me_group.add_argument("--name", help="Name of the chat to create and import messages into")
    parser.add_argument("--input", default=config.tg_default_export_file,
                        metavar="PATH", help="File containing telegram messages")
    parser.add_argument("--no-progress-bar", action="store_true")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace,
               tg_config: Config.Telegram, tg_client: TgClient) -> None:
    tg_messages_path = Path(args.input)
    if not tg_messages_path.exists():
        parser.error(f"Input file not found: '{tg_messages_path}'")

    with tg_messages_path.open("rb") as file:
        tg_messages: list[tg.Message] = pickle.load(file)
        assert isinstance(tg_messages, list) and all(isinstance(msg, tg.Message) for msg in tg_messages)

    async with tg_client:
        success: bool = await import_messages(
            tg_client, tg_config.timezone, tg_messages,
            tg_config.max_simultaneously_uploaded_files,
            args.no_progress_bar, args.chat, args.name)

    if success:
        print("Import finished successfully")
    else:
        print("Something went wrong")
