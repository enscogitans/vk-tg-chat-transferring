from vk_tg_converter.contacts.arguments.arguments import \
    ContactsArguments, ListArguments, PrepareArguments, CheckArguments
from vk_tg_converter.contacts.service import IContactsService


class ContactsController:
    def __init__(self, service: IContactsService) -> None:
        self.service = service

    async def __call__(self, args: ContactsArguments) -> None:
        if isinstance(args, ListArguments):
            return await self.service.list_contacts()
        if isinstance(args, PrepareArguments):
            return await self.service.make_contacts_mapping_file(args.vk_history_input, args.contacts_mapping_output)
        if isinstance(args, CheckArguments):
            return await self.service.check_tg_names_in_mapping_file(args.contacts_mapping_file)
        raise ValueError(f"Unexpected arguments: {args}")
