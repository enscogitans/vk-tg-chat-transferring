import argparse
from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class VkArguments:
    with_login: bool
    hide_password: bool


@dataclass
class TelegramArguments:
    hide_password: bool


LoginArguments: TypeAlias = VkArguments | TelegramArguments


class LoginArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> "LoginArgumentsParser":
        subparsers = parser.add_subparsers(dest="submodule", required=True)

        vk_parser = subparsers.add_parser("vk")
        vk_parser.add_argument("--with-login", action="store_true", help="authorize using login and password")
        vk_parser.add_argument("--show-password", action="store_true")

        tg_parser = subparsers.add_parser("tg")
        tg_parser.add_argument("--show-password", action="store_true")
        return LoginArgumentsParser()

    @staticmethod
    def parse_arguments(namespace: argparse.Namespace) -> LoginArguments:
        match namespace.submodule:
            case "vk":
                with_login = namespace.with_login
                assert isinstance(with_login, bool)
                show_password = namespace.show_password
                assert isinstance(show_password, bool)
                return VkArguments(with_login=with_login, hide_password=not show_password)
            case "tg":
                show_password = namespace.show_password
                assert isinstance(show_password, bool)
                return TelegramArguments(hide_password=not show_password)
        raise ValueError(f"Unexpected submodule: {namespace.submodule}")
