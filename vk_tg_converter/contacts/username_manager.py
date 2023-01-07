import abc
import dataclasses
from typing import Any, Optional

from vk_api.vk_api import VkApiMethod


@dataclasses.dataclass(frozen=True)
class ContactInfo:
    vk_id: int
    vk_name: str
    tg_name_opt: Optional[str]


class IUsernameManager(abc.ABC):
    @abc.abstractmethod
    def get_full_names(self, vk_user_ids: list[int]) -> list[str]: ...

    @abc.abstractmethod
    def try_get_tg_name(self, vk_user_id: int) -> Optional[str]: ...

    def get_full_name(self, vk_user_id: int) -> str:
        [full_name] = self.get_full_names([vk_user_id])
        return full_name


class UsernameManager(IUsernameManager):
    def __init__(self, api: VkApiMethod, prepared_contacts: Optional[list[ContactInfo]] = None):
        self.api = api
        self.contacts_cache: dict[int, ContactInfo] = dict()
        if prepared_contacts is not None:
            assert all(c.tg_name_opt != "" for c in prepared_contacts), "If tg name is missing, set it to None, not ''"
            self.contacts_cache = {c.vk_id: c for c in prepared_contacts}

    def try_get_tg_name(self, vk_user_id: int) -> Optional[str]:
        if vk_user_id in self.contacts_cache:
            return self.contacts_cache[vk_user_id].tg_name_opt
        return None

    def get_full_names(self, vk_ids: list[int]) -> list[str]:
        if missing_ids := list(set(vk_id for vk_id in vk_ids if vk_id not in self.contacts_cache)):
            user_ids = [vk_id for vk_id in missing_ids if vk_id >= 0]
            group_ids = [vk_id for vk_id in missing_ids if vk_id < 0]

            if user_ids:
                request: str = ",".join(map(str, user_ids))
                missing_users: list[dict[Any, Any]] = self.api.users.get(user_ids=request)
                for user_id, user_data in zip(user_ids, missing_users):
                    contact = ContactInfo(vk_id=user_id, vk_name=self._make_full_name(user_data), tg_name_opt=None)
                    self.contacts_cache[user_id] = contact
            if group_ids:
                request = ",".join(str(-group_id) for group_id in group_ids)
                missing_groups = self.api.groups.getById(group_ids=request)
                for group_id, group_data in zip(group_ids, missing_groups):
                    contact = ContactInfo(vk_id=group_id, vk_name=group_data["name"], tg_name_opt=None)
                    self.contacts_cache[group_id] = contact

        return [self.contacts_cache[user_id].vk_name for user_id in vk_ids]

    @staticmethod
    def _make_full_name(user_data: dict[Any, Any]) -> str:
        return "{} {}".format(user_data["first_name"], user_data["last_name"])
