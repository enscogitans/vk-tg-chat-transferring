import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class CheckArguments:
    contacts_mapping_file: Path


class CheckArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "CheckArgumentsParser":
        parser.add_argument("--input", type=Path, default=config.default_contacts_mapping_file,
                            metavar="PATH", help="Path to contacts mapping data")
        return CheckArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> CheckArguments:
        contacts_mapping_file = namespace.input
        assert isinstance(contacts_mapping_file, Path)
        args = CheckArguments(contacts_mapping_file=contacts_mapping_file)
        self._validate(args)
        return args

    def _validate(self, args: CheckArguments) -> None:
        if not args.contacts_mapping_file.exists():
            self.parser.error(f"File with contacts does not exist: {args.contacts_mapping_file}")
        if not args.contacts_mapping_file.is_file():
            self.parser.error(f"Contacts path does not point to a file: {args.contacts_mapping_file}")
