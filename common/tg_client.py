import os

import pyrogram

from config import Config


class TgClient(pyrogram.Client):
    def __init__(self, config: Config.Telegram, *, hide_password: bool = True):
        super().__init__(
            name=config.client_name,
            api_id=config.api_id,
            api_hash=config.api_hash,
            workdir=os.getcwd(),
            hide_password=hide_password,
        )
