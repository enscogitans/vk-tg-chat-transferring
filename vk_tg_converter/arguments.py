import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class ConverterArguments:
    use_dummy_input: bool
    input_file_opt: None | Path
    _skip_contacts: bool
    contacts_file_opt: None | Path
    export_file: Path
    media_export_dir: Path
    disable_progress_bar: bool

    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
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

    def __init__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> None:
        assert isinstance(namespace.dummy_input, bool)
        self.use_dummy_input = namespace.dummy_input
        assert namespace.input is None or isinstance(namespace.input, Path)
        self.input_file_opt = namespace.input
        assert isinstance(namespace.skip_contacts, bool)
        self._skip_contacts = namespace.skip_contacts
        assert namespace.contacts is None or isinstance(namespace.contacts, Path)
        self.contacts_file_opt = namespace.contacts
        assert isinstance(namespace.output, Path)
        self.export_file = namespace.output
        assert isinstance(namespace.media_export_dir, Path)
        self.media_export_dir = namespace.media_export_dir
        assert isinstance(namespace.no_progress_bar, bool)
        self.disable_progress_bar = namespace.no_progress_bar
        self._validate_args(parser)

    def _validate_args(self, parser: argparse.ArgumentParser) -> None:
        assert self.use_dummy_input == (self.input_file_opt is None)
        if self.input_file_opt is not None:
            if not self.input_file_opt.exists():
                parser.error(f"Vk history file does not exist {self.input_file_opt}")
            if not self.input_file_opt.is_file():
                parser.error(f"Vk history path does not point to a file {self.input_file_opt}")
        assert self._skip_contacts == (self.contacts_file_opt is None)
        if self.contacts_file_opt is not None:
            if not self.contacts_file_opt.exists():
                parser.error(f"File with contacts does not exist {self.input_file_opt}")
            if not self.contacts_file_opt.is_file():
                parser.error(f"Contacts path does not point to a file {self.contacts_file_opt}")
        if self.export_file.exists():
            parser.error(f"Output file already exists {self.export_file}")
        if self.media_export_dir.exists():
            if not self.media_export_dir.is_dir():
                parser.error(f"Output media path does not point to a directory {self.media_export_dir}")
            if any(True for _ in self.media_export_dir.iterdir()):
                parser.error(f"Output media directory is not empty {self.media_export_dir}")
        if self.use_dummy_input and self._skip_contacts:
            parser.error("You must not use --skip-contacts if you use --dummy-input")
