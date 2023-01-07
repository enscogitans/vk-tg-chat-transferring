import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, Union

from common.sentinel import Sentinel
from config import Config
from tg_importer.storage import TgHistoryStorage

ChatsArguments: TypeAlias = Union[
    "ChatsListArguments",
    "ChatsSetPhotoArguments",
    "ChatsMuteArguments",
    "ChatsUnmuteArguments",
    "ChatsInviteArguments",
    "ChatsCreateArguments",
]


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    subparsers = parser.add_subparsers(dest="submodule", required=True)

    subparsers.add_parser("list")
    # This submodule has no specific arguments

    set_photo_parser = subparsers.add_parser("set-photo")
    ChatsSetPhotoArguments.fill_parser(set_photo_parser)

    mute_parser = subparsers.add_parser("mute")
    ChatsMuteArguments.fill_parser(mute_parser)

    unmute_parser = subparsers.add_parser("unmute")
    ChatsUnmuteArguments.fill_parser(unmute_parser)

    invite_parser = subparsers.add_parser("invite")
    ChatsInviteArguments.fill_parser(invite_parser, config)

    create_parser = subparsers.add_parser("create")
    ChatsCreateArguments.fill_parser(create_parser, config)


def get_arguments(parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                  tg_history_storage: TgHistoryStorage) -> ChatsArguments:
    match namespace.submodule:
        case "list":
            return ChatsListArguments()
        case "set-photo":
            return ChatsSetPhotoArguments(parser, namespace)
        case "mute":
            return ChatsMuteArguments(namespace)
        case "unmute":
            return ChatsUnmuteArguments(namespace)
        case "invite":
            return ChatsInviteArguments(parser, namespace)
        case "create":
            return ChatsCreateArguments(parser, namespace, tg_history_storage)
    raise ValueError(f"Unexpected submodule {namespace.submodule}")


class ChatsListArguments:
    """Nothing here"""


@dataclass
class ChatsSetPhotoArguments:
    chat_id: int
    photo_path: Path

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        parser.add_argument("--photo", required=True, type=Path, metavar="PHOTO_PATH")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.chat, int)
        self.chat_id = namespace.chat
        assert isinstance(namespace.photo, Path)
        self.photo_path = namespace.photo
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if not self.photo_path.exists():
            parser.error(f"File with photo does not exist {self.photo_path}")
        if not self.photo_path.is_file():
            parser.error(f"Path to the photo is not a file {self.photo_path}")


@dataclass
class ChatsMuteArguments:
    chat_id: int

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("chat", type=int, metavar="CHAT_ID")

    def __init__(self, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.chat, int)
        self.chat_id = namespace.chat


@dataclass
class ChatsUnmuteArguments:
    chat_id: int

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("chat", type=int, metavar="CHAT_ID")

    def __init__(self, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.chat, int)
        self.chat_id = namespace.chat


@dataclass
class ChatsInviteArguments:
    chat_id: int
    contacts_path: Path

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        parser.add_argument("--contacts", type=Path, default=config.default_contacts_mapping_file,
                            metavar="CONTACTS_FILE", help="Path to contacts mapping data")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.chat, int)
        self.chat_id = namespace.chat
        assert isinstance(namespace.contacts, Path)
        self.contacts_path = namespace.contacts
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        if not self.contacts_path.exists():
            parser.error(f"File with contacts does not exist {self.contacts_path}")
        if not self.contacts_path.is_file():
            parser.error(f"Contacts path does not point to a file {self.contacts_path}")


@dataclass
class ChatsCreateArguments:
    title: str
    photo_path: None | Path
    contacts_to_invite_path: None | Path
    is_mute: bool

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
        parser.add_argument("--use-history", nargs="?", type=Path, const=config.tg_default_export_file,
                            metavar="TG_HISTORY_FILE", help="Get chat info from history file")
        parser.add_argument("--title", help="Name of the created chat")
        parser.add_argument("--photo", nargs="?", const=Sentinel(), type=Path,
                            metavar="PHOTO_PATH", help="Set chat photo")
        parser.add_argument("--invite", nargs="?", type=Path, const=config.default_contacts_mapping_file,
                            metavar="CONTACTS_FILE", help="Invite users listed in file with contacts")
        parser.add_argument("--mute", action="store_true", help="Mute all users on chat creation")

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 tg_history_storage: TgHistoryStorage) -> None:
        assert isinstance(namespace.mute, bool)
        self.is_mute = namespace.mute

        assert namespace.invite is None or isinstance(namespace.invite, Path)
        self.contacts_to_invite_path = namespace.invite
        if self.contacts_to_invite_path is not None:
            if not self.contacts_to_invite_path.exists():
                parser.error(f"File with contacts does not exist {self.contacts_to_invite_path}")
            if not self.contacts_to_invite_path.is_file():
                parser.error(f"Contacts path does not point to a file {self.contacts_to_invite_path}")

        assert namespace.title is None or isinstance(namespace.title, str)
        title_raw: None | str = namespace.title  # use title from tg history | use provided title
        assert namespace.photo is None or isinstance(namespace.photo, (Sentinel, Path))
        photo_raw: None | Sentinel | Path = namespace.photo  # no photo | use photo from tg history | use provided photo

        assert namespace.use_history is None or isinstance(namespace.use_history, Path)
        if namespace.use_history is None:
            if title_raw is None:
                parser.error("Neither --title provided nor --use-history used")
            if isinstance(photo_raw, Sentinel):
                parser.error("You have to provide photo path in '--photo PATH' unless you use --use-history")
        if (title_raw is not None) and not isinstance(photo_raw, Sentinel):
            self.title = title_raw
            self.photo_path = photo_raw
            return
        assert namespace.use_history is not None

        tg_history_path: Path = namespace.use_history
        if not tg_history_path.exists():
            parser.error(f"File with Telegram history does not exist {self.contacts_to_invite_path}")
        if not tg_history_path.is_file():
            parser.error(f"Telegram history path does not point to a file {self.contacts_to_invite_path}")
        tg_history = tg_history_storage.load_history(tg_history_path)
        if not tg_history.is_group:
            parser.error("--use-history can't be used with a private chat history")

        if title_raw is None:
            assert tg_history.title_opt is not None
            self.title = tg_history.title_opt
        else:
            self.title = title_raw

        if isinstance(photo_raw, Sentinel):
            self.photo_path = None if tg_history.photo_opt is None else Path(tg_history.photo_opt.path)
        else:
            self.photo_path = photo_raw
