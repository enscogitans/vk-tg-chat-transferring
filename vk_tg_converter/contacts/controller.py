from vk_tg_converter.contacts.arguments import ContactsArguments, \
    ContactsListArguments, ContactsPrepareArguments, ContactsCheckArguments
from vk_tg_converter.contacts.service import IContactsService


class ContactsController:
    def __init__(self, service: IContactsService) -> None:
        self.service = service

    async def __call__(self, args: ContactsArguments) -> None:
        if isinstance(args, ContactsListArguments):
            await self.service.list_contacts()
        elif isinstance(args, ContactsPrepareArguments):
            await self.service.make_contacts_mapping_file(args.vk_history_input, args.contacts_mapping_output)
        else:
            assert isinstance(args, ContactsCheckArguments), f"Unexpected arguments {args}"
            await self.service.check_tg_names_in_mapping_file(args.contacts_mapping_file)
