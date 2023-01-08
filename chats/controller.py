from chats.arguments import ChatsArguments
from chats.arguments.create import CreateArguments
from chats.arguments.invite import InviteArguments
from chats.arguments.list import ListArguments
from chats.arguments.mute import MuteArguments
from chats.arguments.set_photo import SetPhotoArguments
from chats.arguments.unmute import UnmuteArguments
from chats.service import IChatsService


class ChatsController:
    def __init__(self, service: IChatsService) -> None:
        self.service = service

    async def __call__(self, args: ChatsArguments) -> None:
        if isinstance(args, ListArguments):
            return await self.service.list_chats()
        if isinstance(args, SetPhotoArguments):
            return await self.service.set_photo(args.chat_id, args.photo_path)
        if isinstance(args, MuteArguments):
            return await self.service.set_is_mute_chat(args.chat_id, is_mute=True)
        if isinstance(args, UnmuteArguments):
            return await self.service.set_is_mute_chat(args.chat_id, is_mute=False)
        if isinstance(args, InviteArguments):
            return await self.service.invite_users(args.chat_id, args.contacts_path)
        if isinstance(args, CreateArguments):
            return await self.service.create_chat(
                args.title, args.photo_path, args.contacts_to_invite_path, args.is_mute)
        raise ValueError(f"Unknown argument: {args}")
