import argparse
from typing import TypeAlias

from chats.arguments.list import ListArguments
from config import Config
from vk_tg_converter.contacts.arguments.check import CheckArguments, CheckArgumentsParser
from vk_tg_converter.contacts.arguments.prepare import PrepareArguments, PrepareArgumentsParser

ContactsArguments: TypeAlias = ListArguments | PrepareArguments | CheckArguments


class ContactsArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "ContactsArgumentsParser":
        subparsers = parser.add_subparsers(dest="submodule", required=True)

        subparsers.add_parser("list")
        # This submodule has no specific arguments

        subparser = subparsers.add_parser("prepare")
        prepare_parser = PrepareArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("check")
        check_parser = CheckArgumentsParser.fill_parser(subparser, config)

        return ContactsArgumentsParser(
            prepare_parser=prepare_parser,
            check_parser=check_parser,
        )

    def __init__(self, prepare_parser: PrepareArgumentsParser, check_parser: CheckArgumentsParser) -> None:
        self.prepare_parser = prepare_parser
        self.check_parser = check_parser

    def parse_arguments(self, namespace: argparse.Namespace) -> ContactsArguments:
        match namespace.submodule:
            case "list":
                return ListArguments()
            case "prepare":
                return self.prepare_parser.parse_arguments(namespace)
            case "check":
                return self.check_parser.parse_arguments(namespace)
        raise ValueError(f"Unexpected submodule: {namespace.submodule}")
