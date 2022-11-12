import argparse
import pickle
from pathlib import Path

import tg_importer.types as tg
from common.tg_client import TgClient
from config import Config
from tg_importer.importer import import_history


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    parser.add_argument("chat", type=int, metavar="CHAT_ID", help="Chat to import messages into")
    parser.add_argument("--input", type=Path, default=config.tg_default_export_file,
                        metavar="PATH", help="File containing telegram history")
    parser.add_argument("--no-progress-bar", action="store_true")


async def main(parser: argparse.ArgumentParser, args: argparse.Namespace,
               tg_config: Config.Telegram, tg_client: TgClient) -> None:
    tg_history_path: Path = args.input
    if not tg_history_path.exists():
        parser.error(f"Input file not found: '{tg_history_path}'")

    with tg_history_path.open("rb") as file:
        tg_history: tg.ChatHistory = pickle.load(file)
    assert isinstance(tg_history, tg.ChatHistory)

    async with tg_client:
        success: bool = await import_history(
            tg_client, tg_config.timezone, tg_history,
            tg_config.max_simultaneously_uploaded_files,
            args.no_progress_bar, args.chat)

    if success:
        print("Import finished successfully")
    else:
        print("Something went wrong")
