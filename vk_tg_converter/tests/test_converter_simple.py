from tg_importer import types as tg
from vk_exporter import types as vk
from vk_tg_converter.tests.common import data_dir, make_ts


async def test_simple_text(converter):
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi!")
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "Hi!"


async def test_mention(converter):
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="Hi, [id151515151|Alice]!")
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "Hi, Alice!"


async def test_simple_photo(media_converter, converter):
    vk_photo = vk.Photo(url="https://example.com/img.jpg", width=0, height=0)
    tg_photo = tg.Photo(data_dir / "img.jpg")
    media_converter.add(vk_photo, tg_photo)

    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="caption",
                        attachments=(vk_photo,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "caption"
    assert tg_msg.attachment is tg_photo


async def test_simple_link(media_converter, converter):
    vk_link = vk.Link(url="https://example.com", title="Example")
    media_converter.add(vk_link, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="text", attachments=(vk_link,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "text\n"
        "[Link]\n"
        "┊ Example\n"
        "┊ https://example.com"
    )
    assert tg_msg.attachment is None


async def test_do_not_repeat_links(media_converter, converter):
    vk_link = vk.Link(url="https://example.com", title="Example")
    media_converter.add(vk_link, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="https://example.com/",
                        attachments=(vk_link,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "https://example.com/"
    assert tg_msg.attachment is None


async def test_do_not_repeat_links_2(media_converter, converter):
    vk_link = vk.Link(url="https://example.com/", title="Example")
    media_converter.add(vk_link, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="example.com",
                        attachments=(vk_link,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == "example.com"
    assert tg_msg.attachment is None


async def test_filter_for_links_is_smart_enough(media_converter, converter):
    vk_link = vk.Link(url="https://example.com", title="Example")
    media_converter.add(vk_link, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100,
                        text="Broken Linkhttps://example.com", attachments=(vk_link,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "Broken Linkhttps://example.com\n"
        "[Link]\n"
        "┊ Example\n"
        "┊ https://example.com"
    )
    assert tg_msg.attachment is None


async def test_simple_repost(media_converter, converter):
    vk_wall = vk.Wall(id=2418560, owner_id=1)
    media_converter.add(vk_wall, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="I love SPB!",
                        attachments=(vk_wall,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "I love SPB!\n"
        "[Wall]\n"
        "┊ https://vk.com/wall1_2418560"
    )


async def test_simple_poll(media_converter, converter):
    answers = (
        vk.Poll.Answer(text="yes", votes=2, rate=2 / 3 * 100),
        vk.Poll.Answer(text="no", votes=1, rate=1 / 3 * 100),
    )
    vk_poll = vk.Poll("yes/no?", answers=answers, anonymous=True, multiple=False)
    media_converter.add(vk_poll, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="", attachments=(vk_poll,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "[Poll] anonymous, single choice\n"
        "┊\n"
        "┊ yes/no?\n"
        "┊\n"
        "┊ ◆ 67% - yes (2)\n"
        "┊ ◆ 33% - no (1)"
    )


async def test_text_with_poll(media_converter, converter):
    answers = (
        vk.Poll.Answer(text="yes", votes=2, rate=2 / 3 * 100),
        vk.Poll.Answer(text="no", votes=2, rate=2 / 3 * 100),
    )
    vk_poll = vk.Poll("yes/no?", answers=answers, anonymous=False, multiple=True)
    media_converter.add(vk_poll, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="text", attachments=(vk_poll,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "text\n"
        "\n"
        "[Poll] public, multiple choice\n"
        "┊\n"
        "┊ yes/no?\n"
        "┊\n"
        "┊ ◆ 67% - yes (2)\n"
        "┊ ◆ 67% - no (2)"
    )


async def test_restricted_audio(media_converter, converter):
    vk_audio = vk.Audio(url="", id=1, owner_id=2, artist="Ar", title="Ti", duration=100, content_restricted=True)
    media_converter.add(vk_audio, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="", attachments=(vk_audio,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "[Audio]\n"
        "┊ Ar - Ti\n"
        "┊ restricted (audio is unavailable)"
    )


async def test_text_with_3_photos(media_converter, converter):
    vk_photo_1 = vk.Photo(url="https://example.com/img_1.jpg", width=0, height=0)
    vk_photo_2 = vk.Photo(url="https://example.com/img_2.jpg", width=0, height=0)
    vk_photo_3 = vk.Photo(url="https://example.com/img_3.jpg", width=0, height=0)

    tg_photo_1 = tg.Photo(data_dir / "img_1.jpg")
    tg_photo_2 = tg.Photo(data_dir / "img_2.jpg")
    tg_photo_3 = tg.Photo(data_dir / "img_3.jpg")

    media_converter.add(vk_photo_1, tg_photo_1)
    media_converter.add(vk_photo_2, tg_photo_2)
    media_converter.add(vk_photo_3, tg_photo_3)

    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="text",
                        attachments=(vk_photo_1, vk_photo_2, vk_photo_3))

    [tg_msg_1, tg_msg_2, tg_msg_3] = await converter.convert([vk_msg])
    assert tg_msg_1.user == tg_msg_2.user == tg_msg_3.user == "Tg 100"
    assert tg_msg_1.text == "text"
    assert tg_msg_1.attachment is tg_photo_1
    assert not tg_msg_2.text
    assert tg_msg_2.attachment is tg_photo_2
    assert not tg_msg_3.text
    assert tg_msg_3.attachment is tg_photo_3


async def test_unsupported_attachment(media_converter, converter):
    attachment = vk.UnsupportedAttachment("some_type")
    media_converter.add(attachment, None)
    vk_msg = vk.Message(conversation_message_id=0, date=make_ts(0, 0), from_id=100, text="text",
                        attachments=(attachment,))
    [tg_msg] = await converter.convert([vk_msg])
    assert tg_msg.user == "Tg 100"
    assert tg_msg.text == (
        "text\n"
        "[Some Type]"
    )
    assert tg_msg.attachment is None
