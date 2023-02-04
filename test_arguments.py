import argparse
from pathlib import Path

import chats.arguments.arguments as chats
import login.arguments as login
import vk_tg_converter.arguments as converter
import vk_tg_converter.contacts.arguments.arguments as contacts
from arguments import MainArgumentsParser, MainArguments
from config import Config
from tg_importer import TgImporterArguments
from tg_importer.storage import ITgHistoryStorage
from tg_importer.types import ChatHistory
from vk_exporter import VkExporterArguments


class FakeParser(argparse.ArgumentParser):
    def error(self, message):
        return


class FakeHistoryStorage(ITgHistoryStorage):
    def save_history(self, history, path):
        pass

    def load_history(self, path):
        return ChatHistory(messages=[], title_opt="Title", photo_opt=None)


def get_arguments(arguments_line: str) -> MainArguments:
    config = Config()
    parser = FakeParser()
    main_parser = MainArgumentsParser.fill_parser(parser, config)
    namespace = parser.parse_args(arguments_line.split())
    tg_history_storage = FakeHistoryStorage()
    return main_parser.parse_arguments(namespace, tg_history_storage)


def test_login():
    args = get_arguments("login vk")
    assert isinstance(args, login.VkArguments)
    assert not args.with_login
    assert args.hide_password

    args = get_arguments("login tg")
    assert isinstance(args, login.TelegramArguments)
    assert args.hide_password


def test_export():
    args = get_arguments("export --chat 123")
    assert isinstance(args, VkExporterArguments)
    assert args.export_file == Path("vk_history.pickle")


def test_contacts():
    args = get_arguments("contacts list")
    assert isinstance(args, contacts.ListArguments)

    args = get_arguments("contacts prepare")
    assert isinstance(args, contacts.PrepareArguments)
    assert args.vk_history_input == Path("vk_history.pickle")
    assert args.contacts_mapping_output == Path("contacts_mapping.yaml")

    args = get_arguments("contacts check")
    assert isinstance(args, contacts.CheckArguments)
    assert args.contacts_mapping_file == Path("contacts_mapping.yaml")


def test_convert():
    args = get_arguments("convert")
    assert isinstance(args, converter.ConverterArguments)
    assert args.input_file_opt == Path("vk_history.pickle")
    assert args.contacts_file_opt == Path("contacts_mapping.yaml")
    assert args.export_file == Path("tg_history.pickle")
    assert args.media_export_dir == Path("exported_media")


def test_chats():
    args = get_arguments("chats list")
    assert isinstance(args, chats.ListArguments)

    args = get_arguments("chats set-photo 123 --photo photo.jpg")
    assert isinstance(args, chats.SetPhotoArguments)
    assert args.chat_id == 123
    assert args.photo_path == Path("photo.jpg")

    args = get_arguments("chats mute 123")
    assert isinstance(args, chats.MuteArguments)
    assert args.chat_id == 123

    args = get_arguments("chats unmute 123")
    assert isinstance(args, chats.UnmuteArguments)
    assert args.chat_id == 123

    args = get_arguments("chats invite 123")
    assert isinstance(args, chats.InviteArguments)
    assert args.chat_id == 123
    assert args.contacts_path == Path("contacts_mapping.yaml")

    args = get_arguments("chats create --title Title")
    assert isinstance(args, chats.CreateArguments)
    assert args.title == "Title"


def test_import():
    args = get_arguments("import 123")
    assert isinstance(args, TgImporterArguments)
    assert args.chat_id == 123
    assert args.tg_history_path == Path("tg_history.pickle")
