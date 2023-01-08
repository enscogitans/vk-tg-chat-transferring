import argparse
from typing import TypeAlias, Union

from chats import ChatsArguments, ChatsArgumentsParser
from config import Config
from login import LoginArguments, LoginArgumentsParser
from tg_importer import TgImporterArguments, TgImporterArgumentsParser
from tg_importer.storage import ITgHistoryStorage
from vk_exporter import VkExporterArguments, VkExporterArgumentsParser
from vk_tg_converter import ConverterArguments, ConverterArgumentsParser
from vk_tg_converter.contacts import ContactsArguments, ContactsArgumentsParser

MainArguments: TypeAlias = Union[
    LoginArguments,
    VkExporterArguments,
    ContactsArguments,
    ConverterArguments,
    ChatsArguments,
    TgImporterArguments,
]


class MainArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "MainArgumentsParser":
        subparsers = parser.add_subparsers(dest="module", required=True)

        subparser = subparsers.add_parser("login")
        login_parser = LoginArgumentsParser.fill_parser(subparser)

        subparser = subparsers.add_parser("export")
        export_parser = VkExporterArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("contacts")
        contacts_parser = ContactsArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("convert")
        convert_parser = ConverterArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("chats")
        chats_parser = ChatsArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("import")
        import_parser = TgImporterArgumentsParser.fill_parser(subparser, config)

        return MainArgumentsParser(
            login_parser=login_parser,
            export_parser=export_parser,
            contacts_parser=contacts_parser,
            convert_parser=convert_parser,
            chats_parser=chats_parser,
            import_parser=import_parser,
        )

    def __init__(self, login_parser: LoginArgumentsParser,
                 export_parser: VkExporterArgumentsParser,
                 contacts_parser: ContactsArgumentsParser,
                 convert_parser: ConverterArgumentsParser,
                 chats_parser: ChatsArgumentsParser,
                 import_parser: TgImporterArgumentsParser) -> None:
        self.login_parser = login_parser
        self.export_parser = export_parser
        self.contacts_parser = contacts_parser
        self.convert_parser = convert_parser
        self.chats_parser = chats_parser
        self.import_parser = import_parser

    def parse_arguments(self, namespace: argparse.Namespace, tg_history_storage: ITgHistoryStorage) -> MainArguments:
        match namespace.module:
            case "login":
                return self.login_parser.parse_arguments(namespace)
            case "export":
                return self.export_parser.parse_arguments(namespace)
            case "contacts":
                return self.contacts_parser.parse_arguments(namespace)
            case "convert":
                return self.convert_parser.parse_arguments(namespace)
            case "chats":
                return self.chats_parser.parse_arguments(namespace, tg_history_storage)
            case "import":
                return self.import_parser.parse_arguments(namespace)
        raise ValueError(f"Unexpected module: {namespace.module}")
