import json
from typing import Any, Callable, Optional

import jconfig.memory
import vk_api

from config import Config


class VkClient(vk_api.VkApi):
    def __init__(
            self,
            config: Config.Vk,
            token: Optional[str] = None,
            login: Optional[str] = None,
            password: Optional[str] = None,
            auth_handler: Optional[Callable[[], tuple[str, bool]]] = None,
            captcha_handler: Optional[Callable[[vk_api.Captcha], Any]] = None,
    ):
        args = [login, password, auth_handler, captcha_handler]
        if any(arg is None for arg in args) and any(arg is not None for arg in args):
            raise ValueError("Provide all: login, password, auth_handler and captcha_handler")

        self.name = config.client_name
        if token is not None:
            super().__init__(token=token, app_id=config.api_id, api_version=config.api_version)
        elif login is not None:
            super().__init__(
                login=login, password=password,
                app_id=config.api_id,
                api_version=config.api_version,
                scope=config.scope,
                auth_handler=auth_handler,
                captcha_handler=captcha_handler,
                config=jconfig.memory.MemoryConfig,
            )
        else:
            token = self._try_load_token(self.name)
            if token is None:
                raise ValueError(f"Failed to load token from {self.name}.session file. Did you login before?")
            super().__init__(token=token, app_id=config.api_id, api_version=config.api_version)

    def check_token(self) -> bool:
        return self._check_token() or False  # _check_token can return None

    def dump_token(self) -> None:
        token: str = self.token["access_token"]
        session_info = {"token": token}
        with open(f"{self.name}.session", "w") as f:
            json.dump(session_info, f)

    @staticmethod
    def _try_load_token(name: str) -> Optional[str]:
        try:
            with open(f"{name}.session") as f:
                session_info = json.load(f)
                assert isinstance(session_info, dict)
                assert isinstance(session_info.get("token"), str)
                return session_info["token"]  # type: ignore
        except FileNotFoundError:
            return None
