import argparse
from pathlib import Path

from config import Config
from vk_exporter import VkExporterArgumentsParser, VkExporterArguments


class FakeParser(argparse.ArgumentParser):
    def error(self, message):
        return


def get_arguments(arguments_line: str) -> VkExporterArguments:
    config = Config()
    parser = FakeParser()
    export_parser = VkExporterArgumentsParser.fill_parser(parser, config)
    namespace = parser.parse_args(arguments_line.split())
    return export_parser.parse_arguments(namespace)


def test_raw_input():
    args = get_arguments("--raw-input")
    assert args.chat_id is None
    assert args.raw_import_file == Path("vk_raw_history.json")


def test_chat_id():
    args = get_arguments("--chat 123")
    assert args.chat_id == 123
    assert args.raw_import_file is None


def test_chat_id_with_link():
    args = get_arguments("--chat https://vk.com/im?sel=100")
    assert args.chat_id == 100

    args = get_arguments("--chat vk.com/im?sel=-100")
    assert args.chat_id == -100

    args = get_arguments("--chat http://vkontakte.ru/im?sel=c100")
    assert args.chat_id == 2_000_000_100
