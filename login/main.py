import argparse

from config import Config
from login.login import login_tg, login_vk


def fill_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="app", required=True)

    vk_parser = subparsers.add_parser("vk")
    vk_parser.add_argument("--with-login", action="store_true", help="authorize using login and password")
    vk_parser.add_argument("--show-password", action="store_true")

    tg_parser = subparsers.add_parser("tg")
    tg_parser.add_argument("--show-password", action="store_true")


async def main(args: argparse.Namespace, config: Config) -> None:
    match args.app:
        case "vk":
            login_vk(config.vk, with_login=args.with_login, hide_password=not args.show_password)
        case "tg":
            await login_tg(config.tg, hide_password=not args.show_password)
        case app:
            raise ValueError(f"Unexpected app {app}")
