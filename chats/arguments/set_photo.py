import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SetPhotoArguments:
    chat_id: int
    photo_path: Path


class SetPhotoArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> "SetPhotoArgumentsParser":
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        parser.add_argument("--photo", required=True, type=Path, metavar="PHOTO_PATH")
        return SetPhotoArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> SetPhotoArguments:
        chat_id = namespace.chat
        assert isinstance(chat_id, int)
        photo_path = namespace.photo
        assert isinstance(photo_path, Path)

        args = SetPhotoArguments(
            chat_id=chat_id,
            photo_path=photo_path,
        )
        self._validate(args)
        return args

    def _validate(self, args: SetPhotoArguments) -> None:
        if not args.photo_path.exists():
            self.parser.error(f"File with photo does not exist: {args.photo_path}")
        if not args.photo_path.is_file():
            self.parser.error(f"Path to the photo is not a file: {args.photo_path}")
