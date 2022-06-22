import getpass
import urllib.parse
from typing import Any

import vk_api

from common.tg_client import TgClient
from common.vk_client import VkClient
from config import Config


async def login_tg(config: Config.Telegram, *, hide_password: bool) -> None:
    try:
        async with TgClient(config, hide_password=hide_password):
            pass
    except Exception as err:
        print("Error!", err)
    else:
        print("Success!")


def login_vk(config: Config.Vk, *, with_login: bool, hide_password: bool) -> None:
    def two_factor_handler() -> tuple[str, bool]:
        key = input("Enter two-factor authentication code: ")
        remember_device = True
        return key, remember_device

    def captcha_handler(captcha: vk_api.Captcha) -> Any:
        key = input(f"Enter captcha code {captcha.get_url()}: ")
        return captcha.try_again(key)

    if with_login:
        login = input("Enter phone number or email: ")
        password = getpass.getpass("Enter password: ") if hide_password else input("Enter password: ")
        vk_session = VkClient(
            config,
            login=login, password=password,
            auth_handler=two_factor_handler,
            captcha_handler=captcha_handler,
        )
    else:
        auth_url = (
            "https://oauth.vk.com/authorize"
            f"?client_id={config.api_id}"
            f"&v={config.api_version}"
            f"&scope={config.scope}"
            "&display=page"
            "&redirect_uri=https://oauth.vk.com/blank.html"
            "&response_type=token"
        )
        print("Open this link and paste url of the page you were redirected to:")
        print(auth_url)
        result_url = input("Paste url: ")

        fragment: str = urllib.parse.urlparse(result_url).fragment
        params_dict = urllib.parse.parse_qs(fragment)
        if "access_token" not in params_dict:
            raise ValueError("Can't find access_token in provided url")
        if len(params_dict["access_token"]) > 1:
            raise ValueError("Too many values for access_token in provided url")
        token = params_dict["access_token"][0]

        vk_session = VkClient(config, token=token)

    if with_login:
        try:
            vk_session.auth()
        except vk_api.AuthError as err:
            print("Error!", err)
            return
    elif not vk_session.check_token():
        print("Error! Token doesn't work")
        return

    vk_session.dump_token()
    print("Success!")
