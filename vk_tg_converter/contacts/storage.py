from pathlib import Path

import yaml

from vk_tg_converter.contacts.username_manager import ContactInfo


class ContactsStorage:
    @staticmethod
    def save_contacts(contacts: list[ContactInfo], file_path: Path) -> None:
        data = [
            {c.vk_id: [
                {"vk_name": c.vk_name},
                {"tg_name": c.tg_name_opt},
            ]}
            for c in contacts
        ]
        with file_path.open("w") as f:
            yaml.dump(data, f, allow_unicode=True)

    @staticmethod
    def load_contacts(file_path: Path, *, empty_as_none: bool = True) -> list[ContactInfo]:
        with file_path.open("r") as f:
            data = yaml.load(f, yaml.Loader)
        result: list[ContactInfo] = []
        for item in data:
            [[vk_id, names]] = list(item.items())
            assert isinstance(vk_id, int)
            assert isinstance(names, list)
            assert len(names) == 2
            vk_name = names[0]["vk_name"]
            assert isinstance(vk_name, str)
            tg_name_opt = names[1]["tg_name"]
            assert tg_name_opt is None or isinstance(tg_name_opt, str)
            if empty_as_none and tg_name_opt == "":
                tg_name_opt = None
            result.append(ContactInfo(vk_id=vk_id, vk_name=vk_name, tg_name_opt=tg_name_opt))
        return result
