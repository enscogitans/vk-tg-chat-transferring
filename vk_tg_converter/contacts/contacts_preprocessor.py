import pickle
from typing import Optional
from pathlib import Path

import yaml

import vk_exporter.types as vk
from common.tg_client import TgClient
from vk_tg_converter.contacts.username_manager import ContactInfo, UsernameManager


async def list_contacts(tg_client: TgClient) -> None:
    assert tg_client.is_initialized
    contacts = await tg_client.get_contacts()
    for contact in sorted(contacts, key=lambda c: (c.first_name or "", c.last_name or "")):
        info: str = (
            f"first_name = {contact.first_name}\n"
            f"last_name = {contact.last_name}\n"
            f"username = {contact.username}\n"
            f"phone_number = {contact.phone_number}\n"
            f"is_mutual = {contact.is_mutual_contact}\n"
        )
        print(info)


async def make_contacts_mapping_file(
        dst_mapping_file: Path, exported_messages_path: Path,
        tg_client: TgClient, username_manager: UsernameManager) -> None:
    tg_contacts_names: set[str] = await _get_tg_contacts_names(tg_client)

    with exported_messages_path.open("rb") as f:
        vk_messages: list[vk.Message] = pickle.load(f)
    vk_user_ids: list[int] = list({msg.from_id for msg in vk_messages})
    vk_names: list[str] = username_manager.get_full_names(vk_user_ids)

    mapping_data: list[ContactInfo] = []
    for vk_id, vk_name in zip(vk_user_ids, vk_names):
        tg_name_opt: Optional[str] = None
        if vk_name in tg_contacts_names:
            tg_name_opt = vk_name
        mapping_data.append(ContactInfo(vk_id=vk_id, vk_name=vk_name, tg_name_opt=tg_name_opt))

    def get_sort_key(contact: ContactInfo) -> tuple[str, str, int]:
        # First, contacts with empty tg_name. Then sort by vk_name and vk_id
        return contact.tg_name_opt or "", contact.vk_name, contact.vk_id

    mapping_data = sorted(mapping_data, key=get_sort_key)
    dump_contacts_to_yaml(mapping_data, dst_mapping_file)
    print(f"Check file '{str(dst_mapping_file)}'")


async def check_tg_names_in_mapping_file(mapping_file: Path, tg_client: TgClient) -> None:
    tg_contacts_names: set[str] = await _get_tg_contacts_names(tg_client)

    def is_name_correct(tg_name: Optional[str]) -> bool:
        if tg_name == "":
            return True  # Set empty string to skip check for the contact
        return tg_name in tg_contacts_names

    mapping_data: list[ContactInfo] = load_contacts_from_yaml(mapping_file, empty_as_none=False)
    # TODO: check all contacts have unique names
    wrong_contacts: list[ContactInfo] = [
        contact for contact in mapping_data if not is_name_correct(contact.tg_name_opt)
    ]
    if not wrong_contacts:
        print("All provided tg_names are found in telegram contacts")
    else:
        print("There are some tg_names that are missing in telegram contacts")
        print("Either fix them or skip by setting an empty string as tg_name like: - tg_name: \"\"")
        print("List of these contacts:")
        for i, c in enumerate(wrong_contacts, start=1):
            print(f"  {i}. tg_name='{c.tg_name_opt}'", f"vk_name='{c.vk_name}'", f"vk_id={c.vk_id}", sep="\t")


async def _get_tg_contacts_names(tg_client: TgClient) -> set[str]:
    assert tg_client.is_initialized
    tg_contacts_names: set[str] = set()
    for contact in await tg_client.get_contacts():
        first_name: str = contact.first_name or ""
        last_name: str = contact.last_name or ""
        tg_contacts_names.add(str.strip(first_name + " " + last_name))
    return tg_contacts_names


def dump_contacts_to_yaml(contacts: list[ContactInfo], file_path: Path) -> None:
    data = [
        {c.vk_id: [
            {"vk_name": c.vk_name},
            {"tg_name": c.tg_name_opt},
        ]}
        for c in contacts
    ]
    with file_path.open("w") as f:
        yaml.dump(data, f, allow_unicode=True)


def load_contacts_from_yaml(file_path: Path, *, empty_as_none: bool) -> list[ContactInfo]:
    with file_path.open("r") as f:
        data = yaml.load(f, yaml.Loader)
    result: list[ContactInfo] = []
    for item in data:
        [[vk_id, names]] = list(item.items())
        vk_name: str = names[0]["vk_name"]
        tg_name_opt: Optional[str] = names[1]["tg_name"]
        if empty_as_none and tg_name_opt == "":
            tg_name_opt = None
        result.append(ContactInfo(vk_id=vk_id, vk_name=vk_name, tg_name_opt=tg_name_opt))
    return result
