import argparse
import pickle
from pathlib import Path
from typing import Optional, Union

from common.vk_client import VkClient
from config import Config
from vk_exporter.exporter import export_messages, export_raw_messages, parse_raw_messages
from vk_exporter.types import Message


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    parser.add_argument("--export-file", type=Path, metavar="PATH",
                        help="file where messages will be dumped (in pickle format)")

    group1 = parser.add_argument_group("Export from vk")
    group1.add_argument("--chat", type=int, metavar="ID", help="id of the chat")
    group1.add_argument("-n", type=int, metavar="N", help="export only N last messages")
    group1.add_argument("--raw", action="store_true", help="export only raw messages data")
    group1.add_argument("--no-progress-bar", action="store_true")

    group2 = parser.add_argument_group("Export from raw messages file")
    group2.add_argument("--raw-input", nargs="?", type=Path,
                        const=config.vk_default_raw_export_file, metavar="PATH",
                        help="file containing raw messages data. If PATH is not provided, use default one")


def main(parser: argparse.ArgumentParser, args: argparse.Namespace, config: Config, vk_client: VkClient) -> None:
    if (args.chat is None) == (args.raw_input is None):
        parser.error("Provide either '--chat ID' or '--raw-input [PATH]'")
    if args.raw_input is not None and not args.raw_input.exists():
        parser.error(f"File with raw messages does not exist: '{args.raw_input}'")

    export_file: Path
    if args.export_file is not None:
        export_file = args.export_file
    elif (args.chat is not None) and args.raw:
        export_file = config.vk_default_raw_export_file
    else:
        export_file = config.vk_default_export_file
    if export_file.exists():
        parser.error(f"Export file already exists: '{export_file}'")

    messages: Union[list[Message], list[dict]]
    if args.chat is not None:
        if args.raw:
            messages = export_raw_messages(vk_client.get_api(), args.chat, args.n, args.no_progress_bar)
        else:
            messages = export_messages(vk_client.get_api(), args.chat, args.n, args.no_progress_bar)
    else:
        assert args.raw_input is not None
        with args.raw_input.open("rb") as f:
            raw_messages = pickle.load(f)
            assert isinstance(raw_messages, list) and all(isinstance(item, dict) for item in raw_messages)
        messages = parse_raw_messages(raw_messages)

    export_file.parent.mkdir(parents=True, exist_ok=True)
    with export_file.open("wb") as f:
        pickle.dump(messages, f)
    print(f"Success. Check file '{export_file}'")
