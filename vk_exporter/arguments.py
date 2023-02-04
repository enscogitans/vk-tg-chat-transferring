import argparse
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Config


@dataclass
class VkExporterArguments:
    is_raw_export: bool
    export_file: Path
    is_disable_progress_bar: bool
    raw_import_file: Optional[Path]
    chat_id: Optional[int]
    messages_count: Optional[int]


class VkExporterArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "VkExporterArgumentsParser":
        parser.add_argument("--export-file", type=Path, metavar="PATH",
                            help="File where history will be dumped (in pickle format)")

        group1 = parser.add_argument_group("Import data from raw history file")
        group1.add_argument("--raw-input", nargs="?", type=Path,
                            const=config.vk_default_raw_export_file, metavar="PATH", dest="raw_input_path",
                            help="File containing raw history data. If PATH is not provided, use default one")

        group2 = parser.add_argument_group("Import data from vk")
        group2.add_argument("--chat", type=str, metavar="ID/LINK", help="Id of the chat or a link to it")
        group2.add_argument("-n", type=int, metavar="N", help="Export only N last messages")
        group2.add_argument("--raw-export", action="store_true", help="Export only raw messages data")
        group2.add_argument("--no-progress-bar", action="store_true")

        return VkExporterArgumentsParser(parser, config)

    def __init__(self, parser: argparse.ArgumentParser, config: Config) -> None:
        self.parser = parser
        self.config = config

    def parse_arguments(self, namespace: argparse.Namespace) -> VkExporterArguments:
        is_raw_export = namespace.raw_export
        assert isinstance(is_raw_export, bool)
        arg_export_file = namespace.export_file
        assert arg_export_file is None or isinstance(arg_export_file, Path)
        is_disable_progress_bar = namespace.no_progress_bar
        assert isinstance(is_disable_progress_bar, bool)
        raw_import_file = namespace.raw_input_path
        assert raw_import_file is None or isinstance(raw_import_file, Path)
        chat_id = None if namespace.chat is None else self._get_chat_id(namespace.chat)
        assert chat_id is None or isinstance(chat_id, int)
        messages_count = namespace.n
        assert messages_count is None or isinstance(messages_count, int)

        export_file: Path
        if arg_export_file is not None:
            export_file = arg_export_file
        elif is_raw_export:
            export_file = self.config.vk_default_raw_export_file
        else:
            export_file = self.config.vk_default_export_file

        args = VkExporterArguments(
            is_raw_export=is_raw_export,
            export_file=export_file,
            is_disable_progress_bar=is_disable_progress_bar,
            raw_import_file=raw_import_file,
            chat_id=chat_id,
            messages_count=messages_count,
        )
        self._validate(args)
        return args

    def _get_chat_id(self, input_str: str) -> int:
        try:
            return int(input_str)
        except ValueError:
            return self._parse_id_from_link(input_str)

    def _parse_id_from_link(self, link: str) -> int:
        query: str = urllib.parse.urlparse(link).query
        params_dict = urllib.parse.parse_qs(query)
        key = "sel"
        if key not in params_dict:
            self.parser.error("Can't find chat id in provided url")
        if len(params_dict[key]) > 1:
            self.parser.error("Too many ids in provided url")

        value = params_dict[key][0]
        try:
            if value.startswith("c"):  # id of a group looks like 'c120'
                return 2_000_000_000 + int(value[1:])
            return int(value)
        except ValueError:
            self.parser.error(f"Can't extract chat id from url '{link}'")

    def _validate(self, args: VkExporterArguments) -> None:
        if args.export_file.exists():
            self.parser.error(f"Export file already exists: {args.export_file}")
        if (args.chat_id is None) == (args.raw_import_file is None):
            self.parser.error("Provide either '--chat ID' or '--raw-input [PATH]'")
        if args.raw_import_file is not None:
            if not args.raw_import_file.exists():
                self.parser.error(f"Import file does not exist: {args.raw_import_file}")
            if not args.raw_import_file.is_file():
                self.parser.error(f"Import file path does not point to a file: {args.raw_import_file}")
        if args.is_raw_export and args.raw_import_file is not None:
            self.parser.error("You are trying to save raw data while reading raw data: "
                              "do not use both --raw-export and --raw-input")
