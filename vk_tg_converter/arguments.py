import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class ConverterArguments:
    input_file_opt: None | Path
    contacts_file_opt: None | Path
    export_file: Path
    media_export_dir: Path
    disable_progress_bar: bool


class ConverterArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "ConverterArgumentsParser":
        group_1 = parser.add_mutually_exclusive_group()
        group_1.add_argument("--input", type=Path, default=config.vk_default_export_file,
                             metavar="FILE", help="Path to vk history file")
        group_1.add_argument("--dummy-input", action="store_true",
                             help="Use dummy tg history instead of real conversion. "
                                  "You must provide vk-tg contacts mapping")

        group_2 = parser.add_mutually_exclusive_group()
        group_2.add_argument("--contacts", type=Path, default=config.default_contacts_mapping_file,
                             metavar="FILE", help="Path to a file with vk-tg contacts mapping")
        group_2.add_argument("--skip-contacts", action="store_true", help="Do not use contacts mapping")

        parser.add_argument("--output", type=Path, default=config.tg_default_export_file,
                            metavar="FILE", help="File to export converted history into")
        parser.add_argument("--media-export-dir", type=Path, default=config.tg_default_media_export_dir,
                            metavar="DIR", help="Directory to export media files into")
        parser.add_argument("--no-progress-bar", action="store_true")

        return ConverterArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> ConverterArguments:
        use_dummy_input = namespace.dummy_input
        assert isinstance(use_dummy_input, bool)
        input_file_opt = namespace.input
        assert input_file_opt is None or isinstance(input_file_opt, Path)
        assert use_dummy_input == (input_file_opt is None)

        skip_contacts = namespace.skip_contacts
        assert isinstance(skip_contacts, bool)
        contacts_file_opt = namespace.contacts
        assert contacts_file_opt is None or isinstance(contacts_file_opt, Path)
        assert skip_contacts == (contacts_file_opt is None)

        export_file = namespace.output
        assert isinstance(export_file, Path)
        media_export_dir = namespace.media_export_dir
        assert isinstance(media_export_dir, Path)
        disable_progress_bar = namespace.no_progress_bar
        assert isinstance(disable_progress_bar, bool)

        args = ConverterArguments(
            input_file_opt=input_file_opt,
            contacts_file_opt=contacts_file_opt,
            export_file=export_file,
            media_export_dir=media_export_dir,
            disable_progress_bar=disable_progress_bar,
        )
        self._validate(args)
        return args

    def _validate(self, args: ConverterArguments) -> None:
        if args.input_file_opt is not None:
            if not args.input_file_opt.exists():
                self.parser.error(f"Vk history file does not exist: {args.input_file_opt}")
            if not args.input_file_opt.is_file():
                self.parser.error(f"Vk history path does not point to a file: {args.input_file_opt}")
        if args.contacts_file_opt is not None:
            if not args.contacts_file_opt.exists():
                self.parser.error(f"File with contacts does not exist: {args.input_file_opt}")
            if not args.contacts_file_opt.is_file():
                self.parser.error(f"Contacts path does not point to a file: {args.contacts_file_opt}")
        if args.export_file.exists():
            self.parser.error(f"Output file already exists: {args.export_file}")
        if args.media_export_dir.exists():
            if not args.media_export_dir.is_dir():
                self.parser.error(f"Output media path does not point to a directory: {args.media_export_dir}")
            if any(True for _ in args.media_export_dir.iterdir()):
                self.parser.error(f"Output media directory is not empty: {args.media_export_dir}")
        if (args.contacts_file_opt is None) and (args.input_file_opt is None):
            self.parser.error("You must not use --skip-contacts if you use --dummy-input")
