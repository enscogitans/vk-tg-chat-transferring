import abc
import re
from dataclasses import dataclass
from datetime import datetime, tzinfo
from itertools import chain
from typing import Literal, Optional, Union

import tg_importer.types as tg
import vk_exporter.types as vk
from common.sentinel import Sentinel
from vk_tg_converter.contacts.username_manager import IUsernameManager
from vk_tg_converter.converters.media_converter import IMediaConverter


class IMessageConverter(abc.ABC):
    @abc.abstractmethod
    async def convert(self, messages: list[vk.Message]) -> list[tg.Message]: ...


@dataclass
class _PreparedMessage:
    vk_name: str
    tg_name_opt: Optional[str]  # If available
    date: datetime
    reply: Optional["_PreparedMessage"]
    text: str
    forwards: list["_PreparedMessage"]
    attachments: list["_PreparedAttachment"]

    def __post_init__(self) -> None:
        assert self.reply is None or not self.forwards, \
            "I believe vk won't provide reply and forwarded messages simultaneously"
        assert self.text or self.attachments or self.forwards, "Message has no content"


@dataclass
class _PreparedAttachment:
    attachment: vk.Attachment
    alternative_text_need_newline_before_header: bool
    alternative_text_header: str
    alternative_text_header_extra_info: str
    alternative_text_body: list[str]
    # Sentinel if no one tried to set value, None if conversion has failed
    converted_media_opt: Union[Sentinel, None, tg.Media] = Sentinel()


class MessageConverter(IMessageConverter):
    def __init__(self, vk_timezone: tzinfo, username_manager: IUsernameManager, media_converter: IMediaConverter):
        self.vk_timezone = vk_timezone
        self.username_manager = username_manager
        self.media_converter = media_converter

    async def convert(self, messages: list[vk.Message]) -> list[tg.Message]:
        prepared_messages = [self._prepare_message(msg) for msg in messages]
        await self._convert_media_in_messages(prepared_messages)

        result: list[tg.Message] = []
        for msg in prepared_messages:
            result += self._convert_one_message(msg)
        return result

    def _prepare_message(self, msg: vk.Message) -> _PreparedMessage:
        if msg.action is not None:
            return self._prepare_service_message(msg)
        text = self._prepare_text(msg)
        attachments = self._prepare_attachments(msg)
        forwards = list(map(self._prepare_message, msg.fwd_messages))
        if not (text or attachments or forwards):
            text = "*empty message*"
        return _PreparedMessage(
            vk_name=self.username_manager.get_full_name(msg.from_id),
            tg_name_opt=self.username_manager.try_get_tg_name(msg.from_id),
            date=msg.date,
            reply=None if msg.reply_message is None else self._prepare_message(msg.reply_message),
            text=text,
            attachments=attachments,
            forwards=forwards,
        )

    async def _convert_media_in_messages(self, messages: list[_PreparedMessage]) -> None:
        """This function does not convert media in nested messages"""
        prepared_attachments: list[_PreparedAttachment] = list(chain.from_iterable(msg.attachments for msg in messages))
        conversion_results: list[Optional[tg.Media]] = \
            await self.media_converter.try_convert([pa.attachment for pa in prepared_attachments])
        for attch, media_opt in zip(prepared_attachments, conversion_results):
            attch.converted_media_opt = media_opt

    @staticmethod
    def _prepare_attachments(msg: vk.Message) -> list[_PreparedAttachment]:
        result: list[_PreparedAttachment] = []
        for attch in msg.attachments:
            if not MessageConverter._should_skip_attachment(attch, msg.text):
                need_newline, header, header_extra_info, body = \
                    MessageConverter._prepare_alternative_text_for_attachment(attch)
                result.append(_PreparedAttachment(attch, need_newline, header, header_extra_info, body))
        return result

    def _convert_one_message(self, msg: _PreparedMessage) -> list[tg.Message]:
        result: list[tg.Message] = []
        tg_name: str = msg.tg_name_opt or msg.vk_name

        pending_media: list[tg.Media] = []
        media_text_lines: list[str] = []
        for attachment in msg.attachments:
            assert attachment.converted_media_opt is not Sentinel(), "Did you convert media in messages?"
            if attachment.converted_media_opt is None:
                need_newline: bool = attachment.alternative_text_need_newline_before_header
                if need_newline and (msg.text or media_text_lines):
                    media_text_lines.append("")
                media_text_lines += self._attachment_as_text_lines(attachment)
            else:
                assert isinstance(attachment.converted_media_opt, tg.Media), "mypy, are you happy now?"
                pending_media.append(attachment.converted_media_opt)

        lines: list[str] = []
        if msg.reply is not None:
            lines = self._reply_as_text_lines(msg.reply)
            # Reply and attachments (maybe with caption) should be in separate messages
            if pending_media and (pending_media[0].is_caption_allowed() or not msg.text):
                lines += self._shift_lines([""])
                result.append(tg.Message(ts=msg.date, user=tg_name, text="\n".join(lines)))
                lines = []

        if lines and (msg.text or media_text_lines):  # Newline after a reply block
            lines.append("")
        lines += msg.text.splitlines()
        lines += media_text_lines
        for forward in msg.forwards:
            if lines:
                lines.append("")
            lines += self._inner_message_as_text_lines(forward, "Forward")

        if text := "\n".join(lines):
            if pending_media and pending_media[0].is_caption_allowed():
                result.append(tg.Message(ts=msg.date, user=tg_name, text=text, attachment=pending_media[0]))
                pending_media = pending_media[1:]
            else:
                result.append(tg.Message(ts=msg.date, user=tg_name, text=text))
        result += [
            tg.Message(ts=msg.date, user=tg_name, text="", attachment=tg_media) for tg_media in pending_media
        ]
        return result

    def _reply_as_text_lines(self, msg: _PreparedMessage) -> list[str]:
        header: list[str] = self._make_message_header(msg, "Reply")
        # Inner replies are skipped
        body: list[str] = self._cut_text(msg.text, max_len=120, max_lines=3)
        if attachments_line := self._make_line_with_forwards_and_attachments(msg, max_items=2):
            body.append(attachments_line)
        return header + self._shift_lines(body)

    def _inner_message_as_text_lines(self, msg: _PreparedMessage, msg_type: Literal["Reply", "Forward"]) -> list[str]:
        header: list[str] = self._make_message_header(msg, msg_type)
        body: list[str] = []
        if msg.reply is not None:
            body.append("")
            body += self._inner_message_as_text_lines(msg.reply, "Reply")
            body.append("")
        body += msg.text.splitlines()
        for attachment in msg.attachments:
            body += self._attachment_as_text_lines(attachment)
        for forward in msg.forwards:
            body.append("")
            body += self._inner_message_as_text_lines(forward, "Forward")
        return header + self._shift_lines(body)

    def _prepare_service_message(self, msg: vk.Message) -> _PreparedMessage:
        assert msg.action is not None
        vk_name: str = self.username_manager.get_full_name(msg.from_id)
        tg_name_opt: Optional[str] = self.username_manager.try_get_tg_name(msg.from_id)

        text: str
        if isinstance(msg.action, vk.CreateChatAction):
            text = f"*{vk_name} created chat*"
        elif isinstance(msg.action, vk.UpdateTitleAction):
            text = f"*{vk_name} set new title: '{msg.action.new_title}'*"
        elif isinstance(msg.action, vk.UpdatePhotoAction):
            text = f"*{vk_name} set new chat photo*"
        elif isinstance(msg.action, vk.RemovePhotoAction):
            text = f"*{vk_name} removed chat photo*"
        elif isinstance(msg.action, vk.JoinByLinkAction):
            text = f"*{vk_name} joined chat by link*"
        elif isinstance(msg.action, vk.InviteUserAction):
            new_user_name = self.username_manager.get_full_name(msg.action.invited_user_id)
            text = f"*{vk_name} invited {new_user_name}*"
        elif isinstance(msg.action, vk.KickUserAction):
            if msg.action.kicked_user_id == msg.from_id:
                text = f"*{vk_name} left chat*"
            else:
                kicked_user_name = self.username_manager.get_full_name(msg.action.kicked_user_id)
                text = f"*{vk_name} kicked {kicked_user_name}*"
        elif isinstance(msg.action, vk.PinMessageAction):
            text = f"*{vk_name} pinned message*"  # TODO: consider using conversation_message_id here
        elif isinstance(msg.action, vk.UnpinMessageAction):
            text = f"*{vk_name} unpinned message*"  # TODO: consider using conversation_message_id here
        elif isinstance(msg.action, vk.ScreenshotAction):
            text = f"*{vk_name} made a screenshot*"
        else:
            assert isinstance(msg.action, vk.UnsupportedAction), msg.action
            text = f"*{vk_name} triggered action '{msg.action.action_type}'*"

        return _PreparedMessage(
            vk_name=vk_name,
            tg_name_opt=tg_name_opt,
            date=msg.date,
            reply=None,
            text=text,
            forwards=[],
            attachments=self._prepare_attachments(msg),
        )

    @staticmethod
    def _attachment_as_text_lines(attachment: _PreparedAttachment) -> list[str]:
        result: list[str] = [attachment.alternative_text_header + attachment.alternative_text_header_extra_info]
        result += MessageConverter._shift_lines(attachment.alternative_text_body)
        return result

    @staticmethod
    def _prepare_text(msg: vk.Message) -> str:
        if msg.is_expired:
            return "*the message has disappeared 💣*"

        # Replace "[id123456789|Alice]" with just "Alice"
        pattern = r"\[id\d+\|(.+?)\]"
        return re.sub(pattern, r"\1", msg.text)

    @staticmethod
    def _prepare_alternative_text_for_attachment(attachment: vk.Attachment) -> tuple[bool, str, str, list[str]]:
        need_newline_before_header: bool = False
        header: str
        header_extra_info: str = ""
        body: list[str]
        if isinstance(attachment, vk.Geo):
            header = "[Geo]"
            body = [
                attachment.title,
                f"https://www.google.com/maps/search/?api=1&query={attachment.latitude},{attachment.longitude}",
            ]
        elif isinstance(attachment, vk.Photo):
            header = "[Photo]"
            body = [attachment.url]
        elif isinstance(attachment, vk.Video):
            header = "[Video]"
            body = [attachment.title]
        elif isinstance(attachment, vk.Audio):
            header = "[Audio]"
            body = [f"{attachment.artist} - {attachment.title}"]
            if attachment.content_restricted:
                body.append("restricted (audio is unavailable)")
            elif link := attachment.try_get_vk_url():
                body.append(link)
        elif isinstance(attachment, vk.Voice):
            header = "[Voice]"
            body = [attachment.link_ogg]
        elif isinstance(attachment, vk.Document):
            header = "[Document]"
            body = [
                attachment.title,
                attachment.url,
            ]
        elif isinstance(attachment, vk.Poll):
            need_newline_before_header = True
            header = "[Poll]"
            header_extra_info = " {}, {} choice".format(
                "anonymous" if attachment.anonymous else "public",
                "multiple" if attachment.multiple else "single",
            )
            body = ["", attachment.question, ""]
            body.extend(
                "◆ {:.0f}% - {} ({})".format(answer.rate, answer.text, answer.votes)
                for answer in attachment.answers
            )
        elif isinstance(attachment, vk.Wall):
            header = "[Wall]"
            body = [attachment.get_post_url()]
        elif isinstance(attachment, vk.Sticker):
            header = "[Sticker]"
            body = []
        elif isinstance(attachment, vk.Link):
            header = "[Link]"
            body = [
                attachment.title,
                attachment.url,
            ]
        else:
            assert isinstance(attachment, vk.UnsupportedAttachment), attachment
            header = "[{}]".format(attachment.type_name.replace("_", " ").title())
            body = []
        return need_newline_before_header, header, header_extra_info, body

    @staticmethod
    def _should_skip_attachment(attachment: vk.Attachment, msg_text: str) -> bool:
        if not isinstance(attachment, vk.Link):
            return False

        url_with_scheme = attachment.url.lower().rstrip("/")
        url_without_scheme = re.sub("https?://", "", url_with_scheme)
        for word in msg_text.split():
            if word.lower().rstrip("/") in (url_with_scheme, url_without_scheme):
                return True
        return False

    def _make_message_header(self, msg: _PreparedMessage, msg_type: Literal["Reply", "Forward"]) -> list[str]:
        date_str = msg.date.astimezone(self.vk_timezone).strftime("%d.%m.%y, %H:%M")  # 17.07.14, 16:20
        return [
            f"[{msg_type}] {date_str}",
            msg.vk_name,
        ]

    @staticmethod
    def _shift_lines(lines: list[str]) -> list[str]:
        return [str.rstrip("┊ " + line) for line in lines]

    @staticmethod
    def _cut_text(text: str, max_len: int, max_lines: int) -> list[str]:
        text_was_cut = False
        if len(text) > max_len:
            text = text[:max_len - 1].rstrip()
            text_was_cut = True
        lines = text.splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            assert lines[0]
            while not lines[-1]:  # delete empty lines in the end
                lines.pop()
            text_was_cut = True
        if text_was_cut:
            lines[-1] += "…"
        return lines

    @staticmethod
    def _make_line_with_forwards_and_attachments(msg: _PreparedMessage, max_items: int) -> str:
        items: list[str] = ["[Forward]"] * len(msg.forwards)
        items.extend(attch.alternative_text_header for attch in msg.attachments)
        if len(items) > max_items:
            items = items[:max_items]
            items.append("…")
        return ", ".join(items)
