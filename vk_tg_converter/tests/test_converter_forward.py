from tg_importer import types as tg
from vk_exporter import types as vk
from vk_tg_converter.tests.common import data_dir, make_ts


async def test_simple_forward(converter):
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="", fwd_messages=(vk_msg_1,))

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Forward] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!"
    )


async def test_forward_with_mention(converter):
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100,
                          text="Hi, [id151515151|Alice], [id151515152|Bob]!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="Hello",
                          fwd_messages=(vk_msg_1,))

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "Hello\n"
        "\n"
        "[Forward] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi, Alice, Bob!"
    )


async def test_forward_message_with_photo(converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!",
                          attachments=(vk_photo,))
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="",
                          fwd_messages=(vk_msg_1,))

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Forward] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "┊ [Photo]\n"
        "┊ ┊ https://example.com/img.jpg"
    )


async def test_forward_two_messages(converter):
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="Bonjour")
    vk_msg_3 = vk.Message(conversation_message_id=2, date=make_ts(0, 2), from_id=102, text="Hello",
                          fwd_messages=(vk_msg_1, vk_msg_2,))

    [tg_msg] = await converter.convert([vk_msg_3])
    assert tg_msg.user == "Tg 102"
    assert tg_msg.text == (
        "Hello\n"
        "\n"
        "[Forward] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "\n"
        "[Forward] 15.03.22, 00:01\n"
        "Vk 101\n"
        "┊ Bonjour"
    )


async def test_sticker_with_forward(media_converter, converter):
    vk_sticker = vk.Sticker(image_url="url.com/sticker.jpg")
    tg_sticker = tg.Sticker(data_dir / "sticker.webp")
    media_converter.add(vk_sticker, tg_sticker)

    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="",
                          attachments=(vk_sticker,), fwd_messages=(vk_msg_1,))
    [tg_msg_1, tg_msg_2] = await converter.convert([vk_msg_2])

    assert tg_msg_1.user == "Tg 101"
    assert tg_msg_1.text == (
        "[Forward] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!"
    )
    assert tg_msg_1.attachment is None

    assert tg_msg_2.user == "Tg 101"
    assert not tg_msg_2.text
    assert tg_msg_2.attachment is tg_sticker


async def test_forward_message_with_reply(converter):
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="Hello",
                          reply_message=vk_msg_1)
    vk_msg_3 = vk.Message(conversation_message_id=2, date=make_ts(0, 2), from_id=102, text="Bonjour",
                          fwd_messages=(vk_msg_2,))

    [tg_msg] = await converter.convert([vk_msg_3])
    assert tg_msg.user == "Tg 102"
    assert tg_msg.text == (
        "Bonjour\n"
        "\n"
        "[Forward] 15.03.22, 00:01\n"
        "Vk 101\n"
        "┊\n"
        "┊ [Reply] 15.03.22, 00:00\n"
        "┊ Vk 100\n"
        "┊ ┊ Hi!\n"
        "┊\n"
        "┊ Hello"
    )


async def test_nested_forward(converter):
    vk_msg_1 = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(conversation_message_id=1, date=make_ts(0, 1), from_id=101, text="Hello",
                          fwd_messages=(vk_msg_1,))
    vk_msg_3 = vk.Message(conversation_message_id=2, date=make_ts(0, 2), from_id=102, text="Bonjour",
                          fwd_messages=(vk_msg_2,))
    vk_msg_4 = vk.Message(conversation_message_id=3, date=make_ts(0, 3), from_id=103, text="Salut",
                          fwd_messages=(vk_msg_1,))
    vk_msg_5 = vk.Message(conversation_message_id=4, date=make_ts(0, 4), from_id=100, text="Is this English?",
                          fwd_messages=(vk_msg_3, vk_msg_4,))

    [tg_msg] = await converter.convert([vk_msg_5])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "Is this English?\n"
        "\n"
        "[Forward] 15.03.22, 00:02\n"
        "Vk 102\n"
        "┊ Bonjour\n"
        "┊\n"
        "┊ [Forward] 15.03.22, 00:01\n"
        "┊ Vk 101\n"
        "┊ ┊ Hello\n"
        "┊ ┊\n"
        "┊ ┊ [Forward] 15.03.22, 00:00\n"
        "┊ ┊ Vk 100\n"
        "┊ ┊ ┊ Hi!\n"
        "\n"
        "[Forward] 15.03.22, 00:03\n"
        "Vk 103\n"
        "┊ Salut\n"
        "┊\n"
        "┊ [Forward] 15.03.22, 00:00\n"
        "┊ Vk 100\n"
        "┊ ┊ Hi!"
    )
