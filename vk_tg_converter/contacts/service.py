import abc
from pathlib import Path

import vk_exporter.types as vk
from common.user_io import IUserOutput
from common.utils import get_full_name
from vk_exporter.storage import IVkHistoryStorage
from vk_tg_converter.contacts.storage import IContactsStorage
from vk_tg_converter.contacts.tg_client_adaptor import ITgClientAdaptor
from vk_tg_converter.contacts.username_manager import IUsernameManager, ContactInfo


class IContactsService(abc.ABC):
    @abc.abstractmethod
    async def list_contacts(self) -> None: ...

    @abc.abstractmethod
    async def make_contacts_mapping_file(self, vk_history_input: Path, contacts_mapping_output: Path) -> None: ...

    @abc.abstractmethod
    async def check_tg_names_in_mapping_file(self, contacts_mapping_file: Path) -> None: ...


class ContactsService(IContactsService):
    def __init__(self, username_manager: IUsernameManager, tg_client: ITgClientAdaptor,
                 vk_history_storage: IVkHistoryStorage, contacts_storage: IContactsStorage,
                 out_stream: IUserOutput) -> None:
        self.username_manager = username_manager
        self.tg_client = tg_client
        self.vk_history_storage = vk_history_storage
        self.contacts_storage = contacts_storage
        self.out_stream = out_stream

    async def list_contacts(self) -> None:
        async with self.tg_client:
            contacts = await self.tg_client.get_contacts()
        for contact in sorted(contacts, key=lambda c: (c.first_name or "", c.last_name or "")):
            info: str = (
                f"first_name = {contact.first_name}\n"
                f"last_name = {contact.last_name}\n"
                f"username = {contact.username}\n"
                f"phone_number = {contact.phone_number}\n"
                f"is_mutual = {contact.is_mutual_contact}\n"
            )
            self.out_stream.print(info)

    async def make_contacts_mapping_file(self, vk_history_input: Path, contacts_mapping_output: Path) -> None:
        result: list[ContactInfo] = []

        vk_messages: list[vk.Message] = self.vk_history_storage.load_history(vk_history_input).messages
        vk_user_ids: list[int] = list({msg.from_id for msg in vk_messages})
        vk_ego_id: int = self.username_manager.get_ego_id()

        async with self.tg_client:
            tg_contacts_names: set[str] = await self._get_contacts_names_saved_in_telegram()
            if vk_ego_id in vk_user_ids:
                vk_user_ids.remove(vk_ego_id)
                ego_tg_name = get_full_name(await self.tg_client.get_me())
                ego_vk_name = self.username_manager.get_full_name(vk_ego_id)
                result.append(ContactInfo(vk_id=vk_ego_id, vk_name=ego_vk_name, tg_name_opt=ego_tg_name))

        vk_names: list[str] = self.username_manager.get_full_names(vk_user_ids)
        for vk_id, vk_name in zip(vk_user_ids, vk_names):
            tg_name_opt: None | str = None
            if vk_name in tg_contacts_names:
                tg_name_opt = vk_name
            result.append(ContactInfo(vk_id=vk_id, vk_name=vk_name, tg_name_opt=tg_name_opt))

        def get_sort_key(contact: ContactInfo) -> tuple[str, str, int]:
            # Contacts with empty tg_name go first
            return contact.tg_name_opt or "", contact.vk_name, contact.vk_id

        result = sorted(result, key=get_sort_key)
        self.contacts_storage.save_contacts(result, contacts_mapping_output)
        self.out_stream.print(f"Check file '{str(contacts_mapping_output)}'")

    @staticmethod
    def _is_name_correct(tg_name: None | str, tg_contacts_names: set[str]) -> bool:
        if tg_name == "":  # One can explicitly set name to empty string to skip the check
            return True
        return tg_name in tg_contacts_names

    async def check_tg_names_in_mapping_file(self, contacts_mapping_file: Path) -> None:
        async with self.tg_client:
            tg_contacts_names: set[str] = await self._get_contacts_names_saved_in_telegram()

        mapping_data = self.contacts_storage.load_contacts(contacts_mapping_file, empty_as_none=False)
        # TODO: check all contacts have unique names
        wrong_contacts: list[ContactInfo] = [
            contact for contact in mapping_data if not self._is_name_correct(contact.tg_name_opt, tg_contacts_names)
        ]
        if not wrong_contacts:
            self.out_stream.print("All provided tg_names are found in telegram contacts")
        else:
            self.out_stream.print("There are some tg_names that are missing in telegram contacts")
            self.out_stream.print(
                "Either fix or skip them.",
                "To skip the check for a contact set an empty string as tg_name. Like: - tg_name: \"\"")
            self.out_stream.print("List of these contacts:")
            for i, c in enumerate(wrong_contacts, start=1):
                self.out_stream.print(f"  {i}. tg_name='{c.tg_name_opt}'",
                                      f"vk_name='{c.vk_name}'",
                                      f"vk_id={c.vk_id}", sep="\t")

    async def _get_contacts_names_saved_in_telegram(self) -> set[str]:
        return {get_full_name(contact) for contact in await self.tg_client.get_contacts()}
