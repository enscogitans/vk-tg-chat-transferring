import datetime
from pathlib import Path
from typing import Optional

import pytest
from pyrogram import types

from common.user_io import MemoryUserOutput
from vk_exporter.storage import IVkHistoryStorage
from vk_exporter.types import ChatHistory, Message
from vk_tg_converter.contacts.service import ContactsService
from vk_tg_converter.contacts.storage import IContactsStorage
from vk_tg_converter.contacts.tg_client_adaptor import ITgClientAdaptor
from vk_tg_converter.contacts.username_manager import IUsernameManager, ContactInfo


@pytest.fixture
def username_manager():
    class FakeUsernameManager(IUsernameManager):
        def __init__(self):
            self.name_by_id: dict[int, str] = {}
            self.ego_id: None | int = None

        def get_full_names(self, vk_ids):
            return [self.name_by_id[vk_id] for vk_id in vk_ids]

        def get_ego_id(self) -> int:
            assert self.ego_id is not None
            return self.ego_id

        def try_get_tg_name(self, vk_user_id: int) -> Optional[str]: raise NotImplementedError

    return FakeUsernameManager()


@pytest.fixture
def tg_client():
    class FakeTgClient(ITgClientAdaptor):
        def __init__(self):
            self.contacts: list[types.User] = []
            self.me: None | types.User = None

        async def get_contacts(self):
            return self.contacts

        async def get_me(self) -> types.User:
            assert self.me is not None
            return self.me

    return FakeTgClient()


@pytest.fixture
def vk_history_storage():
    class FakeVkHistoryStorage(IVkHistoryStorage):
        def __init__(self):
            self.messages = []

        def save_raw_history(self, raw_history, path): raise NotImplementedError

        def load_raw_history(self, path): raise NotImplementedError

        def save_history(self, history, path): raise NotImplementedError

        def set_messages_from_users(self, user_ids: list[int]):
            ts = datetime.datetime(2007, 10, 10)
            for user_id in user_ids:
                self.messages.append(Message(from_id=user_id, date=ts, text=str(user_id)))

        def load_history(self, path):
            return ChatHistory(messages=self.messages, title_opt="Title", photo_opt=None)

    return FakeVkHistoryStorage()


@pytest.fixture
def contacts_storage():
    class FakeContactsStorage(IContactsStorage):
        def __init__(self):
            self.contacts: list[ContactInfo] = []

        def load_contacts(self, file_path, *, empty_as_none=True): raise NotImplementedError

        def save_contacts(self, contacts, file_path) -> None:
            self.contacts += contacts

    return FakeContactsStorage()


@pytest.fixture
def service(username_manager, tg_client, vk_history_storage, contacts_storage):
    return ContactsService(
        username_manager,
        tg_client,
        vk_history_storage,
        contacts_storage,
        MemoryUserOutput(),
    )


async def test_mapping_one_missing(service, username_manager, tg_client, vk_history_storage, contacts_storage):
    tg_client.contacts = [
        types.User(id=1, first_name="A", last_name="B"),
        types.User(id=2, first_name="B"),
        types.User(id=3, first_name="C", last_name="D"),
    ]
    username_manager.ego_id = 1000
    username_manager.name_by_id = {
        # vk_id -> vk full name
        101: "A B",
        102: "x",
        103: "C D",
    }
    vk_history_storage.set_messages_from_users([101, 102, 103])

    await service.make_contacts_mapping_file(Path(), Path())

    assert contacts_storage.contacts == [
        ContactInfo(vk_id=102, vk_name="x", tg_name_opt=None),
        ContactInfo(101, "A B", "A B"),
        ContactInfo(103, "C D", "C D"),
    ]


async def test_mapping_user_without_message(service, username_manager, tg_client, vk_history_storage, contacts_storage):
    tg_client.contacts = [
        types.User(id=1, first_name="A", last_name="B"),
        types.User(id=2, first_name="B"),
        types.User(id=3, first_name="C", last_name="D"),
    ]
    username_manager.ego_id = 1000
    username_manager.name_by_id = {
        # vk_id -> vk full name
        101: "A B",
        102: "x",
        103: "C D",
    }
    vk_history_storage.set_messages_from_users([101, 102])

    await service.make_contacts_mapping_file(Path(), Path())

    assert contacts_storage.contacts == [
        ContactInfo(vk_id=102, vk_name="x", tg_name_opt=None),
        ContactInfo(101, "A B", "A B"),
    ]


async def test_mapping_add_ego(service, username_manager, tg_client, vk_history_storage, contacts_storage):
    tg_client.contacts = [
        types.User(id=1, first_name="A", last_name="B"),
        types.User(id=2, first_name="B"),
        types.User(id=3, first_name="C", last_name="D"),
    ]
    tg_client.me = types.User(id=300, first_name="Tg", last_name="Name")
    username_manager.ego_id = 1000
    username_manager.name_by_id = {
        # vk_id -> vk full name
        101: "A B",
        102: "x",
        103: "C D",
        1000: "Vk Name",
    }
    vk_history_storage.set_messages_from_users([101, 102, 103, 1000])

    await service.make_contacts_mapping_file(Path(), Path())

    assert contacts_storage.contacts == [
        ContactInfo(vk_id=102, vk_name="x", tg_name_opt=None),
        ContactInfo(101, "A B", "A B"),
        ContactInfo(103, "C D", "C D"),
        ContactInfo(1000, "Vk Name", "Tg Name"),
    ]
