from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TypeAlias, Union, cast

from vk_api.vk_api import VkApiMethod


@dataclass(frozen=True)
class ChatHistory:
    messages: list["Message"]
    # Only valid for chats (not private messages):
    title: Optional[str]  # All chats have title
    photo: Optional["Photo"]  # Not all chats have photo


@dataclass(frozen=True)
class Message:
    """https://dev.vk.com/reference/objects/message"""
    from_id: int
    date: datetime
    text: str
    is_expired: bool = False  # If true message would not have any content
    attachments: tuple["Attachment", ...] = tuple()
    reply_message: Optional["Message"] = None
    fwd_messages: tuple["Message", ...] = tuple()
    action: Optional["Action"] = None  # E.g. add someone to the chat

    @staticmethod
    def parse(message_dict: dict) -> "Message":
        attachments: tuple["Attachment", ...] = ()
        if "geo" in message_dict:
            attachments += (Geo.parse(message_dict["geo"]),)
        attachments += tuple(parse_attachment(info) for info in message_dict.get("attachments", []))
        fwd_messages = tuple(Message.parse(info) for info in message_dict.get("fwd_messages", []))
        reply_message: Optional[Message] = None
        if "reply_message" in message_dict:
            reply_message = Message.parse(message_dict["reply_message"])
        action: Optional[Action] = None
        if "action" in message_dict:
            action = parse_action(message_dict["action"])
        return Message(
            date=datetime.fromtimestamp(message_dict["date"], tz=timezone.utc),
            from_id=message_dict["from_id"],
            text=message_dict["text"],
            is_expired=message_dict.get("is_expired", False),
            attachments=attachments,
            fwd_messages=fwd_messages,
            reply_message=reply_message,
            action=action,
        )


@dataclass(frozen=True)
class Geo:
    latitude: float
    longitude: float
    title: str

    @staticmethod
    def parse(geo_dict: dict) -> "Geo":
        return Geo(
            latitude=geo_dict["coordinates"]["latitude"],
            longitude=geo_dict["coordinates"]["longitude"],
            title=geo_dict["place"]["title"],
        )


Attachment: TypeAlias = Union[
    "Geo",
    "Photo",
    "Video",
    "Audio",
    "Voice",
    "Document",
    "Poll",
    "Wall",
    "Sticker",
    "Link",
    "UnsupportedAttachment",
]


def parse_attachment(attachment_dict: dict) -> Attachment:
    type_name = attachment_dict["type"]
    attachment_dict = attachment_dict[type_name]
    match type_name:
        case "photo":
            return Photo.parse(attachment_dict)
        case "video":
            return Video.parse(attachment_dict)
        case "audio":
            return Audio.parse(attachment_dict)
        case "audio_message":
            return Voice.parse(attachment_dict)
        case "doc":
            return Document.parse(attachment_dict)
        case "poll":
            return Poll.parse(attachment_dict)
        case "wall":
            return Wall.parse(attachment_dict)
        case "sticker":
            return Sticker.parse(attachment_dict)
        case "link":
            return Link.parse(attachment_dict)
    return UnsupportedAttachment(type_name=type_name)


@dataclass(frozen=True)
class Photo:
    """https://dev.vk.com/reference/objects/photo"""
    url: str
    width: int
    height: int

    @staticmethod
    def parse(photo_dict: dict) -> "Photo":
        best_size = Photo._pick_best_size(photo_dict["sizes"])
        return Photo(
            url=best_size["url"],
            width=best_size["width"],
            height=best_size["height"],
        )

    @staticmethod
    def _pick_best_size(sizes_list: list[dict]) -> dict:
        def get_size_priority(size: dict) -> int:
            # https://dev.vk.com/reference/objects/photo-sizes
            priorities = {size_type: i for i, size_type in enumerate("wzyrqpoxms")}
            return priorities.get(size["type"], len(priorities))

        assert sizes_list, "Empty sizes"
        return min(sizes_list, key=get_size_priority)


@dataclass(frozen=True)
class Video:
    """https://dev.vk.com/reference/objects/video"""
    title: str
    id: int
    owner_id: int
    width: int
    height: int
    duration: int
    content_restricted: bool  # If True, video won't be available
    image_url: str
    access_key: Optional[str]  # https://dev.vk.com/reference/objects

    @staticmethod
    def parse(video_dict: dict) -> "Video":
        return Video(
            title=video_dict["title"],
            id=video_dict["id"],
            owner_id=video_dict["owner_id"],
            width=video_dict.get("width", 0),
            height=video_dict.get("height", 0),
            duration=video_dict["duration"],
            content_restricted=video_dict.get("content_restricted", False),
            image_url=Video._pick_best_image(video_dict["image"])["url"],
            access_key=video_dict.get("access_key"),
        )

    def try_get_player_url(self, api: VkApiMethod) -> Optional[str]:
        # NB: This url doesn't live too much. Use it quickly
        if self.content_restricted:
            return None
        video_key = f"{self.owner_id}_{self.id}"
        if self.access_key is not None:  # For example, short videos (aka tik-toks) may not have this key
            video_key += f"_{self.access_key}"
        response = api.video.get(videos=video_key)
        assert len(response["items"]) == 1, response
        url = response["items"][0].get("player")  # Video can be deleted or something. In this case 'player' is absent
        return cast(Optional[str], url)

    @staticmethod
    def _pick_best_image(images_list: list[dict]) -> dict:
        def get_image_priority(image_dict: dict) -> tuple[int, int]:
            # Prefer images without padding. Then prefer the largest ones
            return image_dict.get("with_padding", 0), -image_dict["width"] * image_dict["height"]

        assert images_list, "Empty images (thumbs)"
        return min(images_list, key=get_image_priority)


@dataclass(frozen=True)
class Audio:
    """https://dev.vk.com/reference/objects/audio"""
    id: int
    owner_id: int
    artist: str
    title: str
    duration: int
    content_restricted: bool  # If True, url will be empty. Actually, it is int, but I don't know what it means
    url: str  # link to mp3 file. TODO: it is always empty. Find another way to download audio

    @staticmethod
    def parse(audio_dict: dict) -> "Audio":
        return Audio(
            id=audio_dict["id"],
            owner_id=audio_dict["owner_id"],
            artist=audio_dict["artist"],
            title=audio_dict["title"],
            duration=audio_dict["duration"],
            content_restricted=audio_dict.get("content_restricted", False),
            url=audio_dict["url"],
        )

    def try_get_vk_url(self) -> Optional[str]:
        if not self.content_restricted:  # I believe in this case link is valid
            return f"https://m.vk.com/audio{self.owner_id}_{self.id}"
        return None


@dataclass(frozen=True)
class Voice:
    """https://dev.vk.com/reference/objects/audio-message"""
    link_ogg: str  # link_mp3 is also available
    duration: int
    transcript: Optional[str]  # TODO: consider using it

    @staticmethod
    def parse(voice_dict: dict) -> "Voice":
        return Voice(
            link_ogg=voice_dict["link_ogg"],
            duration=voice_dict["duration"],
            transcript=voice_dict.get("transcript"),
        )


@dataclass(frozen=True)
class Document:
    """https://dev.vk.com/reference/objects/doc"""
    url: str
    title: str
    extension: str  # doesn't have leading period: "png" or "docx"
    type: int  # TODO: consider using it

    @staticmethod
    def parse(document_dict: dict) -> "Document":
        return Document(
            url=document_dict["url"],
            title=document_dict["title"],
            extension=document_dict["ext"],
            type=document_dict["type"],
        )


@dataclass(frozen=True)
class Poll:
    """https://dev.vk.com/reference/objects/poll"""
    question: str
    answers: tuple["Answer", ...]
    anonymous: bool
    multiple: bool

    @dataclass(frozen=True)
    class Answer:
        text: str
        votes: int  # how many people have chosen this answer
        rate: float  # 0-100

    @staticmethod
    def parse(poll_dict: dict) -> "Poll":
        answers = tuple(
            Poll.Answer(text=answer_dict["text"], votes=answer_dict["votes"], rate=answer_dict["rate"])
            for answer_dict in poll_dict["answers"]
        )
        return Poll(
            question=poll_dict["question"],
            answers=answers,
            anonymous=poll_dict["anonymous"],
            multiple=poll_dict["multiple"],
        )


@dataclass(frozen=True)
class Wall:
    """https://dev.vk.com/reference/objects/post"""
    id: int
    owner_id: int

    @staticmethod
    def parse(wall_dict: dict) -> "Wall":
        return Wall(
            id=wall_dict["id"],
            owner_id=wall_dict.get("owner_id") or wall_dict["to_id"],
        )

    def get_post_url(self) -> str:
        return f"https://vk.com/wall{self.owner_id}_{self.id}"  # TODO: Verify that we should use owner_id here


@dataclass(frozen=True)
class Sticker:
    """https://dev.vk.com/reference/objects/sticker"""
    image_url: str  # usually, .png file
    animation_url: Optional[str] = None  # TODO: support animated stickers

    @staticmethod
    def parse(sticker_dict: dict) -> "Sticker":
        assert sticker_dict["images"], "Empty images"
        best_image = max(sticker_dict["images"], key=lambda img: img["width"] * img["height"])  # type: ignore
        return Sticker(
            image_url=best_image["url"],
            animation_url=sticker_dict.get("animation_url"),
        )


@dataclass(frozen=True)
class Link:
    """https://dev.vk.com/reference/objects/link"""
    url: str
    title: str

    @staticmethod
    def parse(link_dict: dict) -> "Link":
        return Link(
            url=link_dict["url"],
            title=link_dict["title"]
        )


@dataclass(frozen=True)
class UnsupportedAttachment:
    type_name: str


# https://dev.vk.com/reference/objects/message#action
Action: TypeAlias = Union[
    "CreateChatAction",
    "UpdateTitleAction",
    "UpdatePhotoAction",
    "RemovePhotoAction",
    "JoinByLinkAction",
    "InviteUserAction",
    "KickUserAction",
    "PinMessageAction",
    "UnpinMessageAction",
    "ScreenshotAction",
    "UnsupportedAction",
]


def parse_action(action_dict: dict) -> Action:
    match action_dict["type"]:
        case "chat_create":
            return CreateChatAction()
        case "chat_title_update":
            return UpdateTitleAction(new_title=action_dict["text"])
        case "chat_photo_update":
            return UpdatePhotoAction()
        case "chat_photo_remove":
            return RemovePhotoAction()
        case "chat_invite_user_by_link":
            return JoinByLinkAction()
        case "chat_invite_user":
            return InviteUserAction(invited_user_id=action_dict["member_id"])
        case "chat_kick_user":
            return KickUserAction(kicked_user_id=action_dict["member_id"])
        case "chat_pin_message":
            return PinMessageAction(conversation_message_id=action_dict["conversation_message_id"])
        case "chat_unpin_message":
            return UnpinMessageAction(conversation_message_id=action_dict["conversation_message_id"])
        case "chat_screenshot":
            return ScreenshotAction()
        case action_type:
            return UnsupportedAction(action_type, action_dict)


class CreateChatAction:
    pass


@dataclass
class UpdateTitleAction:
    new_title: str


class UpdatePhotoAction:
    pass


class RemovePhotoAction:
    pass


class JoinByLinkAction:
    pass


@dataclass
class InviteUserAction:
    invited_user_id: int


@dataclass
class KickUserAction:
    kicked_user_id: int


@dataclass
class PinMessageAction:
    conversation_message_id: int


@dataclass
class UnpinMessageAction:
    conversation_message_id: int


class ScreenshotAction:
    pass


@dataclass
class UnsupportedAction:
    action_type: str
    action_dict: dict
