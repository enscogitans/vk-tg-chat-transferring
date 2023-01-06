from chats.arguments import ChatsArguments, \
    ChatsListArguments, ChatsSetPhotoArguments, ChatsMuteArguments, \
    ChatsUnmuteArguments, ChatsInviteArguments, ChatsCreateArguments
from chats.service import ChatsService


class ChatsController:
    def __init__(self, service: ChatsService) -> None:
        self.service = service

    async def __call__(self, args: ChatsArguments) -> None:
        if isinstance(args, ChatsListArguments):
            await self.service.list_chats()
        elif isinstance(args, ChatsSetPhotoArguments):
            await self.service.set_photo(args.chat_id, args.photo_path)
        elif isinstance(args, ChatsMuteArguments):
            await self.service.set_is_mute_chat(args.chat_id, is_mute=True)
        elif isinstance(args, ChatsUnmuteArguments):
            await self.service.set_is_mute_chat(args.chat_id, is_mute=False)
        elif isinstance(args, ChatsInviteArguments):
            await self.service.invite_users(args.chat_id, args.contacts_path)
        else:
            assert isinstance(args, ChatsCreateArguments), f"Unknown argument {args}"
            await self.service.create_chat(args.title, args.contacts_to_invite_path, args.is_mute, args.photo_path)
