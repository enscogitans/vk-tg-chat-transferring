import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class InviteArguments:
    chat_id: int
    contacts_path: Path


class InviteArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "InviteArgumentsParser":
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        parser.add_argument("--contacts", type=Path, default=config.default_contacts_mapping_file,
                            metavar="CONTACTS_FILE", help="Path to contacts mapping data")
        return InviteArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> InviteArguments:
        chat_id = namespace.chat
        assert isinstance(chat_id, int)
        contacts_path = namespace.contacts
        assert isinstance(contacts_path, Path)

        args = InviteArguments(
            chat_id=chat_id,
            contacts_path=contacts_path,
        )
        self._validate(args)
        return args

    def _validate(self, args: InviteArguments) -> None:
        if not args.contacts_path.exists():
            self.parser.error(f"File with contacts does not exist: {args.contacts_path}")
        if not args.contacts_path.is_file():
            self.parser.error(f"Contacts path does not point to a file: {args.contacts_path}")
