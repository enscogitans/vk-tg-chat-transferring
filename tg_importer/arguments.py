import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class TgImporterArguments:
    chat_id: int
    tg_history_path: Path
    disable_progress_bar: bool

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("chat", type=int, metavar="CHAT_ID", help="Chat to import messages into")
        parser.add_argument("--input", type=Path, default=config.tg_default_export_file,
                            metavar="PATH", help="File containing telegram history")
        parser.add_argument("--no-progress-bar", action="store_true")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.chat, int)
        self.chat_id = namespace.chat
        assert isinstance(namespace.input, Path)
        self.tg_history_path = namespace.input
        assert isinstance(namespace.no_progress_bar, bool)
        self.disable_progress_bar = namespace.no_progress_bar
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if not self.tg_history_path.exists():
            parser.error(f"File with Telegram history does not exist {self.tg_history_path}")
        if not self.tg_history_path.is_file():
            parser.error(f"Telegram history path does not point to a file {self.tg_history_path}")
