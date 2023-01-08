import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class TgImporterArguments:
    chat_id: int
    tg_history_path: Path
    disable_progress_bar: bool


class TgImporterArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "TgImporterArgumentsParser":
        parser.add_argument("chat", type=int, metavar="CHAT_ID", help="Chat to import messages into")
        parser.add_argument("--input", type=Path, default=config.tg_default_export_file,
                            metavar="PATH", help="File containing telegram history")
        parser.add_argument("--no-progress-bar", action="store_true")
        return TgImporterArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> TgImporterArguments:
        chat_id = namespace.chat
        assert isinstance(chat_id, int)
        tg_history_path = namespace.input
        assert isinstance(tg_history_path, Path)
        disable_progress_bar = namespace.no_progress_bar
        assert isinstance(disable_progress_bar, bool)

        args = TgImporterArguments(
            chat_id=chat_id,
            tg_history_path=tg_history_path,
            disable_progress_bar=disable_progress_bar,
        )
        self._validate(args)
        return args

    def _validate(self, args: TgImporterArguments) -> None:
        if not args.tg_history_path.exists():
            self.parser.error(f"File with Telegram history does not exist: {args.tg_history_path}")
        if not args.tg_history_path.is_file():
            self.parser.error(f"Telegram history path does not point to a file: {args.tg_history_path}")
