import argparse
import pickle
from pathlib import Path
from typing import Union

from common.vk_client import VkClient
from config import Config
from vk_exporter.exporter import export_history, export_raw_history, parse_raw_history
from vk_exporter.types import ChatHistory


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    parser.add_argument("--export-file", type=Path, metavar="PATH",
                        help="file where history will be dumped (in pickle format)")

    group1 = parser.add_argument_group("Export from vk")
    group1.add_argument("--chat", type=int, metavar="ID", help="id of the chat")
    group1.add_argument("-n", type=int, metavar="N", help="export only N last messages")
    group1.add_argument("--raw", action="store_true", help="export only raw messages data")
    group1.add_argument("--no-progress-bar", action="store_true")

    group2 = parser.add_argument_group("Export from raw history file")
    group2.add_argument("--raw-input", nargs="?", type=Path,
                        const=config.vk_default_raw_export_file, metavar="PATH",
                        help="file containing raw history data. If PATH is not provided, use default one")


def main(parser: argparse.ArgumentParser, args: argparse.Namespace, config: Config, vk_client: VkClient) -> None:
    if (args.chat is None) == (args.raw_input is None):
        parser.error("Provide either '--chat ID' or '--raw-input [PATH]'")
    if args.raw_input is not None and not args.raw_input.exists():
        parser.error(f"File with raw history does not exist: '{args.raw_input}'")

    export_file: Path
    if args.export_file is not None:
        export_file = args.export_file
    elif (args.chat is not None) and args.raw:
        export_file = config.vk_default_raw_export_file
    else:
        export_file = config.vk_default_export_file
    if export_file.exists():
        parser.error(f"Export file already exists: '{export_file}'")

    history: Union[ChatHistory, dict]
    if args.chat is not None:
        if args.raw:
            history = export_raw_history(vk_client.get_api(), args.chat, args.n, args.no_progress_bar)
        else:
            history = export_history(vk_client.get_api(), args.chat, args.n, args.no_progress_bar)
    else:
        assert args.raw_input is not None
        with args.raw_input.open("rb") as f:
            raw_history = pickle.load(f)
        history = parse_raw_history(raw_history)

    export_file.parent.mkdir(parents=True, exist_ok=True)
    with export_file.open("wb") as f:
        pickle.dump(history, f)
    print(f"Success. Check file '{export_file}'")
