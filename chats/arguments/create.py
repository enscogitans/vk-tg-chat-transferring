import argparse
from dataclasses import dataclass
from pathlib import Path

from common.sentinel import Sentinel
from config import Config
from tg_importer.storage import ITgHistoryStorage


@dataclass
class CreateArguments:
    title: str
    photo_path: None | Path
    contacts_to_invite_path: None | Path
    is_mute: bool


class CreateArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "CreateArgumentsParser":
        parser.add_argument("--use-history", nargs="?", type=Path, const=config.tg_default_export_file,
                            metavar="TG_HISTORY_FILE", help="Get chat info from history file")
        parser.add_argument("--title", help="Name of the created chat")
        parser.add_argument("--photo", nargs="?", const=Sentinel(), type=Path,
                            metavar="PHOTO_PATH", help="Set chat photo")
        parser.add_argument("--invite", nargs="?", type=Path, const=config.default_contacts_mapping_file,
                            metavar="CONTACTS_FILE", help="Invite users listed in file with contacts")
        parser.add_argument("--mute", action="store_true", help="Mute all users on chat creation")
        return CreateArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace, tg_history_storage: ITgHistoryStorage) -> CreateArguments:
        tg_history_path = namespace.use_history
        assert tg_history_path is None or isinstance(tg_history_path, Path)
        arg_title = namespace.use_history
        assert arg_title is None or isinstance(arg_title, str)  # use title from tg history | use provided title
        arg_photo = namespace.photo
        # no photo | photo from history | provided photo
        assert arg_photo is None or isinstance(arg_photo, (Sentinel, Path))

        title, photo_path = self._parse_title_and_photo(
            tg_history_path, namespace.title, namespace.photo, tg_history_storage)

        contacts_to_invite_path = namespace.invite
        assert contacts_to_invite_path is None or isinstance(contacts_to_invite_path, Path)
        is_mute = namespace.mute
        assert isinstance(is_mute, bool)

        args = CreateArguments(
            title=title,
            photo_path=photo_path,
            contacts_to_invite_path=contacts_to_invite_path,
            is_mute=is_mute,
        )
        self._validate(args)
        return args

    def _validate(self, args: CreateArguments) -> None:
        if args.contacts_to_invite_path is None:
            return
        if not args.contacts_to_invite_path.exists():
            self.parser.error(f"File with contacts does not exist: {args.contacts_to_invite_path}")
        if not args.contacts_to_invite_path.is_file():
            self.parser.error(f"Contacts path does not point to a file: {args.contacts_to_invite_path}")

    def _parse_title_and_photo(self, arg_tg_history_path: None | Path,
                               arg_title: None | str,
                               arg_photo: None | Sentinel | Path,
                               tg_history_storage: ITgHistoryStorage) -> tuple[str, None | Path]:
        if arg_tg_history_path is None:
            if arg_title is None:
                self.parser.error("Neither --title provided nor --use-history used")
            if isinstance(arg_photo, Sentinel):
                self.parser.error("You have to provide photo path in '--photo PATH' unless you use --use-history")

        if (arg_title is not None) and not isinstance(arg_photo, Sentinel):
            return arg_title, arg_photo
        assert arg_tg_history_path is not None

        history_title, history_photo = self._read_title_and_photo_from_history(arg_tg_history_path, tg_history_storage)
        title = history_title if arg_title is None else arg_title
        photo = history_photo if isinstance(arg_photo, Sentinel) else arg_photo
        return title, photo

    def _read_title_and_photo_from_history(self, tg_history_path: Path,
                                           tg_history_storage: ITgHistoryStorage) -> tuple[str, None | Path]:
        if not tg_history_path.exists():
            self.parser.error(f"File with Telegram history does not exist: {tg_history_path}")
        if not tg_history_path.is_file():
            self.parser.error(f"Telegram history path does not point to a file: {tg_history_path}")

        tg_history = tg_history_storage.load_history(tg_history_path)
        if not tg_history.is_group:
            self.parser.error("--use-history can't be used with a private chat history")

        assert tg_history.title_opt is not None
        if tg_history.photo_opt is None:
            return tg_history.title_opt, None
        return tg_history.title_opt, Path(tg_history.photo_opt.path)
