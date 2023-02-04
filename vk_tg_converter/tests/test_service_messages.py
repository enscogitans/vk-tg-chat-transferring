from tg_importer import types as tg
from vk_exporter import types as vk
from vk_tg_converter.tests.common import data_dir, make_ts


async def test_create_chat(converter):
    vk_msg = vk.Message(conversation_message_id=0,
                        date=make_ts(0, 0), from_id=100, text="", action=vk.CreateChatAction())
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "*Vk 100 created chat*"


async def test_update_title(converter):
    vk_msg = vk.Message(conversation_message_id=0,
                        date=make_ts(0, 0), from_id=100, text="", action=vk.UpdateTitleAction("new title"))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "*Vk 100 set new title: 'new title'*"


async def test_update_photo(media_converter, converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    tg_photo = tg.Photo(data_dir / "img.jpg")
    media_converter.add(vk_photo, tg_photo)

    vk_msg = vk.Message(conversation_message_id=0,
                        date=make_ts(0, 0), from_id=100, text="", attachments=(vk_photo,),
                        action=vk.UpdatePhotoAction())
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "*Vk 100 set new chat photo*"
    assert tg_msg.attachment is tg_photo


async def test_pin_message(media_converter, converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    tg_photo = tg.Photo(data_dir / "img.jpg")
    media_converter.add(vk_photo, tg_photo)

    vk_msg_1 = vk.Message(conversation_message_id=0,
                          date=make_ts(0, 0), from_id=100, text="Hi!", attachments=(vk_photo,))
    vk_msg_2 = vk.Message(conversation_message_id=1,
                          date=make_ts(0, 1), from_id=101, text="", action=vk.PinMessageAction(0, "random text"))

    [_, tg_msg] = await converter.convert([vk_msg_1, vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "┊ [Photo]\n"
        "\n"
        "*Vk 101 pinned message*"
    )


async def test_pinned_message_not_in_index_but_with_text(media_converter, converter):
    vk_msg = vk.Message(conversation_message_id=1,
                        date=make_ts(0, 1), from_id=101, text="", action=vk.PinMessageAction(0, "message text"))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == "*Vk 101 pinned message: 'message text'*"


async def test_pinned_message_not_in_index_and_without_text(media_converter, converter):
    vk_msg = vk.Message(conversation_message_id=1,
                        date=make_ts(0, 1), from_id=101, text="", action=vk.PinMessageAction(0, ""))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == "*Vk 101 pinned message*"


async def test_unpin_message(media_converter, converter):
    vk_msg_1 = vk.Message(conversation_message_id=0,
                          date=make_ts(0, 0), from_id=100, text="Hello")
    vk_msg_2 = vk.Message(conversation_message_id=1,
                          date=make_ts(0, 1), from_id=101, text="", action=vk.UnpinMessageAction(0))

    [_, tg_msg] = await converter.convert([vk_msg_1, vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hello\n"
        "\n"
        "*Vk 101 unpinned message*"
    )


async def test_unpinned_message_not_in_index(converter):
    vk_msg = vk.Message(conversation_message_id=1,
                        date=make_ts(0, 1), from_id=101, text="", action=vk.UnpinMessageAction(0))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == "*Vk 101 unpinned message*"
