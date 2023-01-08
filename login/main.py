from config import Config
from login.arguments import LoginArguments, VkArguments, TelegramArguments
from login.login import login_tg, login_vk


async def main(args: LoginArguments, config: Config) -> None:
    if isinstance(args, VkArguments):
        return login_vk(config.vk, with_login=args.with_login, hide_password=args.hide_password)
    if isinstance(args, TelegramArguments):
        return await login_tg(config.tg, hide_password=args.hide_password)
    raise ValueError(f"Unknown argument: {args}")
