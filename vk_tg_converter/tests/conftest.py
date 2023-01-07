from pathlib import PurePath
from typing import Dict, Optional
from datetime import timezone

import pytest

from tg_importer import types as tg
from vk_exporter import types as vk
from vk_tg_converter.converters.message_converter import MessageConverter, IMediaConverter, IUsernameManager


class FakeUsernameManager(IUsernameManager):
    def get_full_names(self, vk_user_ids):
        return list(map(self.get_full_name, vk_user_ids))

    def get_full_name(self, vk_user_id):
        return f"Vk {vk_user_id}"

    def try_get_tg_name(self, vk_user_id):
        return f"Tg {vk_user_id}"


class FakeMediaConverter(IMediaConverter):
    def __init__(self):
        super().__init__()
        self.conversion_results: Dict[vk.Attachment, Optional[tg.Media]] = {}

    def add(self, vk_attachment, tg_attachment):
        self.conversion_results[vk_attachment] = tg_attachment

    async def try_convert(self, vk_attachments):
        return [self.conversion_results[vk_attachment] for vk_attachment in vk_attachments]


@pytest.fixture
def username_manager():
    return FakeUsernameManager()


@pytest.fixture
def media_converter():
    return FakeMediaConverter()


@pytest.fixture
def converter(username_manager, media_converter):
    return MessageConverter(timezone.utc, username_manager, media_converter)


"""
Now if we request two this fixtures in test and then modify media_converter,
converter will also see the change. See below
"""


async def test_fixtures(media_converter, converter):
    vk_attachment = vk.Sticker("url.com/img")
    tg_media = tg.Sticker(PurePath("./sticker.webp"))

    with pytest.raises(KeyError):
        await converter.media_converter.try_convert([vk_attachment])
    media_converter.add(vk_attachment, tg_media)
    converted = await converter.media_converter.try_convert([vk_attachment])
    assert converted[0] is tg_media
