import datetime

from tg_importer import types as tg
from vk_exporter import types as vk
from vk_tg_converter.converters.message_converter import MessageConverterV1
from vk_tg_converter.tests.common import data_dir, make_ts


async def test_simple_reply(converter):
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "\n"
        "Hello"
    )


async def test_timezone(username_manager, media_converter):
    tz = datetime.timezone(datetime.timedelta(hours=3))
    converter = MessageConverterV1(tz, username_manager, media_converter)

    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 03:00\n"
        "Vk 100\n"
        "┊ Hi\n"
        "\n"
        "Hello"
    )


async def test_reply_to_mention(converter):
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi, [id151515151|Alice]!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi, Alice!\n"
        "\n"
        "Hello"
    )


async def test_reply_to_very_long_message(converter):
    text = "A" * 1000
    short_text = "A" * 119 + "…"
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text=text)
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        f"┊ {short_text}\n"
        "\n"
        "Hello"
    )


async def test_reply_to_message_with_many_lines(converter):
    text = "\n".join("A" * 50)
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text=text)
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hi", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ A\n"
        "┊ A\n"
        "┊ A…\n"
        "\n"
        "Hi"
    )


async def test_reply_to_repost(converter):
    vk_wall = vk.Wall(id=2418560, owner_id=1)
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="I love SPB!", attachments=(vk_wall,))
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="wow...", reply_message=vk_msg_1)
    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ I love SPB!\n"
        "┊ [Wall]\n"
        "\n"
        "wow..."
    )
    assert tg_msg.attachment is None


async def test_reply_to_message_with_link(converter):
    vk_link = vk.Link(url="https://example.com", title="Example")
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Some link", attachments=(vk_link,))
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="wow...", reply_message=vk_msg_1)
    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Some link\n"
        "┊ [Link]\n"
        "\n"
        "wow..."
    )
    assert tg_msg.attachment is None


async def test_reply_to_photo_with_text(converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!", attachments=(vk_photo,))
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "┊ [Photo]\n"
        "\n"
        "Hello"
    )


async def test_nested_reply_2(converter):
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)
    vk_msg_3 = vk.Message(date=make_ts(0, 2), from_id=102, text="Bonjour", reply_message=vk_msg_2)

    [tg_msg] = await converter.convert([vk_msg_3])
    assert tg_msg.user == "Tg 102"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:01\n"
        "Vk 101\n"
        "┊ Hello\n"
        "\n"
        "Bonjour"
    )


async def test_nested_reply_3(converter):
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", reply_message=vk_msg_1)
    vk_msg_3 = vk.Message(date=make_ts(0, 2), from_id=102, text="Bonjour", reply_message=vk_msg_2)
    vk_msg_4 = vk.Message(date=make_ts(0, 3), from_id=100, text="Is this English?", reply_message=vk_msg_3)

    [tg_msg] = await converter.convert([vk_msg_4])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:02\n"
        "Vk 102\n"
        "┊ Bonjour\n"
        "\n"
        "Is this English?"
    )


async def test_reply_to_forwarded_message(converter):
    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", fwd_messages=(vk_msg_1,))
    vk_msg_3 = vk.Message(date=make_ts(0, 2), from_id=102, text="Bonjour", reply_message=vk_msg_2)

    [tg_msg] = await converter.convert([vk_msg_3])
    assert tg_msg.user == "Tg 102"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:01\n"
        "Vk 101\n"
        "┊ Hello\n"
        "┊ [Forward]\n"
        "\n"
        "Bonjour"
    )


async def test_reply_with_photo_and_text(media_converter, converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    tg_photo = tg.Photo(data_dir / "img.jpg")
    media_converter.add(vk_photo, tg_photo)

    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello", attachments=(vk_photo,),
                          reply_message=vk_msg_1)
    [tg_msg_1, tg_msg_2] = await converter.convert([vk_msg_2])

    assert tg_msg_1.user == "Tg 101"
    assert tg_msg_1.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "┊"
    )
    assert tg_msg_1.attachment is None
    assert tg_msg_2.text == "Hello"
    assert tg_msg_2.attachment is tg_photo


async def test_reply_with_sticker(media_converter, converter):
    vk_sticker = vk.Sticker(image_url="https://example.com/sticker.png")
    tg_sticker = tg.Sticker(data_dir / "sticker.webp")
    media_converter.add(vk_sticker, tg_sticker)

    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="",
                          attachments=(vk_sticker,), reply_message=vk_msg_1)
    [tg_msg_1, tg_msg_2] = await converter.convert([vk_msg_2])

    assert tg_msg_1.user == "Tg 101"
    assert tg_msg_1.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "┊"
    )
    assert tg_msg_1.attachment is None

    assert tg_msg_2.user == "Tg 101"
    assert not tg_msg_2.text
    assert tg_msg_2.attachment is tg_sticker


async def test_reply_with_link(media_converter, converter):
    vk_link = vk.Link(url="https://example.com", title="Example")
    media_converter.add(vk_link, None)

    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="",
                          attachments=(vk_link,), reply_message=vk_msg_1)

    [tg_msg] = await converter.convert([vk_msg_2])
    assert tg_msg.user == "Tg 101"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:00\n"
        "Vk 100\n"
        "┊ Hi!\n"
        "\n"
        "[Link]\n"
        "┊ Example\n"
        "┊ https://example.com"
    )
    assert tg_msg.attachment is None


async def test_reply_to_message_with_many_attachments(media_converter, converter):
    vk_photo = vk.Photo(url="img.jpg", width=0, height=0)
    tg_photo = tg.Photo(data_dir / "img.jpg")
    media_converter.add(vk_photo, tg_photo)

    vk_poll = vk.Poll(question="", answers=(), anonymous=False, multiple=False)
    media_converter.add(vk_poll, None)

    vk_msg_1 = vk.Message(date=make_ts(0, 0), from_id=100, text="Hi!")
    vk_msg_2 = vk.Message(date=make_ts(0, 1), from_id=101, text="Hello",
                          fwd_messages=(vk_msg_1,), attachments=(vk_poll, vk_photo, vk_photo, vk_photo))
    vk_msg_3 = vk.Message(date=make_ts(0, 2), from_id=102, text="Bonjour", reply_message=vk_msg_2)

    [tg_msg] = await converter.convert([vk_msg_3])
    assert tg_msg.user == "Tg 102"
    assert tg_msg.text == (
        "[Reply] 15.03.22, 00:01\n"
        "Vk 101\n"
        "┊ Hello\n"
        "┊ [Forward], [Poll], …\n"
        "\n"
        "Bonjour"
    )
    assert tg_msg.attachment is None
