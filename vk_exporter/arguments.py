import argparse
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

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("--export-file", type=Path, metavar="PATH",
                            help="File where history will be dumped (in pickle format)")

        group1 = parser.add_argument_group("Import data from raw history file")
        group1.add_argument("--raw-input", nargs="?", type=Path,
                            const=config.vk_default_raw_export_file, metavar="PATH", dest="raw_input_path",
                            help="File containing raw history data. If PATH is not provided, use default one")

        group2 = parser.add_argument_group("Import data from vk")
        group2.add_argument("--chat", type=int, metavar="ID", help="Id of the chat")
        group2.add_argument("-n", type=int, metavar="N", help="Export only N last messages")
        group2.add_argument("--raw-export", action="store_true", help="Export only raw messages data")
        group2.add_argument("--no-progress-bar", action="store_true")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, config: Config) -> None:
        assert isinstance(namespace.raw_export, bool)
        self.is_raw_export = namespace.raw_export
        assert namespace.export_file is None or isinstance(namespace.export_file, Path)
        if namespace.export_file is not None:
            self.export_file = namespace.export_file
        elif self.is_raw_export:
            self.export_file = config.vk_default_raw_export_file
        else:
            self.export_file = config.vk_default_export_file
        assert isinstance(namespace.no_progress_bar, bool)
        self.is_disable_progress_bar = namespace.no_progress_bar
        assert namespace.raw_input_path is None or isinstance(namespace.raw_input_path, Path)
        self.raw_import_file = namespace.raw_input_path
        assert namespace.chat is None or isinstance(namespace.chat, int)
        self.chat_id = namespace.chat
        assert namespace.n is None or isinstance(namespace.n, int)
        self.messages_count = namespace.n
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if self.export_file.exists():
            parser.error(f"Export file already exists {self.export_file}")
        if (self.chat_id is None) == (self.raw_import_file is None):
            parser.error("Provide either '--chat ID' or '--raw-input [PATH]'")
        if self.raw_import_file is not None and not self.raw_import_file.exists():
            parser.error(f"Import file does not exist {self.raw_import_file}")
        if self.is_raw_export and self.raw_import_file is not None:
            parser.error("You are trying to save raw data while reading raw data: "
                         "do not use both --raw-export and --raw-input")
