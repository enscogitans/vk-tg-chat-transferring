import argparse
from dataclasses import dataclass
from pathlib import Path

from config import Config


@dataclass
class PrepareArguments:
    vk_history_input: Path
    contacts_mapping_output: Path


class PrepareArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser, config: Config) -> "PrepareArgumentsParser":
        parser.add_argument("--input", type=Path, default=config.vk_default_export_file,
                            metavar="PATH", help="Path to vk messages file")
        parser.add_argument("--output", type=Path, default=config.default_contacts_mapping_file,
                            metavar="PATH", help="File to export contacts mapping data in")
        return PrepareArgumentsParser(parser)

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

    def parse_arguments(self, namespace: argparse.Namespace) -> PrepareArguments:
        vk_history_input = namespace.input
        assert isinstance(vk_history_input, Path)
        contacts_mapping_output = namespace.output
        assert isinstance(contacts_mapping_output, Path)

        args = PrepareArguments(
            vk_history_input=vk_history_input,
            contacts_mapping_output=contacts_mapping_output,
        )
        self._validate(args)
        return args

    def _validate(self, args: PrepareArguments) -> None:
        if not args.vk_history_input.exists():
            self.parser.error(f"File with vk history does not exist: {args.vk_history_input}")
        if not args.vk_history_input.is_file():
            self.parser.error(f"History path does not point to a file: {args.vk_history_input}")
        if args.contacts_mapping_output.exists():
            self.parser.error(f"File with contacts already exists: {args.contacts_mapping_output}")
