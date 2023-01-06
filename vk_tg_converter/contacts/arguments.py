import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, Union

from config import Config

ContactsArguments: TypeAlias = Union[
    "ContactsListArguments",
    "ContactsPrepareArguments",
    "ContactsCheckArguments",
]


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    subparsers = parser.add_subparsers(dest="submodule", required=True)

    subparsers.add_parser("list")
    # This submodule has no specific arguments

    prepare_parser = subparsers.add_parser("prepare")
    ContactsPrepareArguments.fill_parser(prepare_parser, config)

    check_parser = subparsers.add_parser("check")
    ContactsCheckArguments.fill_parser(check_parser, config)


def get_arguments(parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> ContactsArguments:
    match namespace.submodule:
        case "list":
            return ContactsListArguments()
        case "prepare":
            return ContactsPrepareArguments(parser, namespace)
        case "check":
            return ContactsCheckArguments(parser, namespace)
    raise ValueError(f"Unexpected submodule {namespace.submodule}")


class ContactsListArguments:
    """Nothing here"""


@dataclass
class ContactsPrepareArguments:
    vk_history_input: Path
    contacts_mapping_output: Path

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("--input", type=Path, default=config.vk_default_export_file,
                            metavar="PATH", help="Path to vk messages file")
        parser.add_argument("--output", type=Path, default=config.default_contacts_mapping_file,
                            metavar="PATH", help="File to export contacts mapping data in")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.input, Path)
        self.vk_history_input = namespace.input
        assert isinstance(namespace.output, Path)
        self.contacts_mapping_output = namespace.output
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if not self.vk_history_input.exists():
            parser.error(f"File with vk history does not exist {self.vk_history_input}")
        if not self.vk_history_input.is_file():
            parser.error(f"History path does not point to a file {self.vk_history_input}")
        if self.contacts_mapping_output.exists():
            parser.error(f"File with contacts already exists {self.contacts_mapping_output}")


@dataclass
class ContactsCheckArguments:
    contacts_mapping_file: Path

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("--input", type=Path, default=config.default_contacts_mapping_file,
                            metavar="PATH", help="Path to contacts mapping data")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.input, Path)
        self.contacts_mapping_file = namespace.input
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if not self.contacts_mapping_file.exists():
            parser.error(f"File with contacts does not exist {self.contacts_mapping_file}")
        if not self.contacts_mapping_file.is_file():
            parser.error(f"Contacts path does not point to a file {self.contacts_mapping_file}")
