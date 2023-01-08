import argparse
from typing import TypeAlias

from chats.arguments.create import CreateArguments, CreateArgumentsParser
from chats.arguments.invite import InviteArguments, InviteArgumentsParser
from chats.arguments.list import ListArguments
from chats.arguments.mute import MuteArguments, MuteArgumentsParser
from chats.arguments.set_photo import SetPhotoArguments, SetPhotoArgumentsParser
from chats.arguments.unmute import UnmuteArguments, UnmuteArgumentsParser
from config import Config
from tg_importer.storage import ITgHistoryStorage

ChatsArguments: TypeAlias = \
    ListArguments | SetPhotoArguments | MuteArguments | UnmuteArguments | InviteArguments | CreateArguments


class ChatsArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "ChatsArgumentsParser":
        subparsers = parser.add_subparsers(dest="submodule", required=True)

        subparsers.add_parser("list")
        # This submodule has no specific arguments

        subparser = subparsers.add_parser("set-photo")
        set_photo_parser = SetPhotoArgumentsParser.fill_parser(subparser)

        subparser = subparsers.add_parser("mute")
        mute_parser = MuteArgumentsParser.fill_parser(subparser)

        subparser = subparsers.add_parser("unmute")
        unmute_parser = UnmuteArgumentsParser.fill_parser(subparser)

        subparser = subparsers.add_parser("invite")
        invite_parser = InviteArgumentsParser.fill_parser(subparser, config)

        subparser = subparsers.add_parser("create")
        create_parser = CreateArgumentsParser.fill_parser(subparser, config)

        return ChatsArgumentsParser(
            set_photo_parser=set_photo_parser,
            mute_parser=mute_parser,
            unmute_parser=unmute_parser,
            invite_parser=invite_parser,
            create_parser=create_parser,
        )

    def __init__(self,
                 set_photo_parser: SetPhotoArgumentsParser,
                 mute_parser: MuteArgumentsParser,
                 unmute_parser: UnmuteArgumentsParser,
                 invite_parser: InviteArgumentsParser,
                 create_parser: CreateArgumentsParser) -> None:
        self.set_photo_parser = set_photo_parser
        self.mute_parser = mute_parser
        self.unmute_parser = unmute_parser
        self.invite_parser = invite_parser
        self.create_parser = create_parser

    def parse_arguments(self, namespace: argparse.Namespace, tg_history_storage: ITgHistoryStorage) -> ChatsArguments:
        match namespace.submodule:
            case "list":
                return ListArguments()
            case "set-photo":
                return self.set_photo_parser.parse_arguments(namespace)
            case "mute":
                return self.mute_parser.parse_arguments(namespace)
            case "unmute":
                return self.unmute_parser.parse_arguments(namespace)
            case "invite":
                return self.invite_parser.parse_arguments(namespace)
            case "create":
                return self.create_parser.parse_arguments(namespace, tg_history_storage)
        raise ValueError(f"Unexpected submodule: {namespace.submodule}")
