import abc
import datetime
import typing

from tg_importer.types import Message


class Encoder(abc.ABC):
    @abc.abstractmethod
    def encode(self, messages: typing.List[Message]) -> str: ...


class WhatsAppAndroidEncoder(Encoder):
    def __init__(self, timezone: datetime.tzinfo, is_group: bool):
        super().__init__()
        self.timezone = timezone
        self.is_group = is_group

    def encode(self, messages: typing.List[Message]) -> str:
        if not messages:
            raise ValueError("No messages provided")
        if not self.is_group:
            raise NotImplementedError("Encoder for private messages is not implemented yet")  # TODO: implement it
        if not all(messages[i-1].ts <= messages[i].ts for i in range(1, len(messages))):
            raise ValueError("Messages must be sorted by timestamp")

        title = "Chat Title"  # Telegram doesn't use it anywhere
        first_ts_str = self._encode_timestamp(messages[0].ts)
        chunks: typing.List[str] = [
            f"{first_ts_str} - You created group \"{title}\"",
            f"{first_ts_str} - Messages you send to this group are now secured with end-to-end encryption. Tap for more info.",  # noqa: E501
            # TODO: use dummy message only if chat is empty
            self._encode_message(Message(
                ts=messages[0].ts, user="Dummy User", text="Dummy line. Otherwise Telegram ignores first message")),
        ]
        chunks += [self._encode_message(message) for message in messages]
        chunks.append("")  # Newline in the end. Without it last message may disappear
        return "\n".join(chunks)

    def _encode_timestamp(self, ts: datetime.datetime) -> str:
        return ts.astimezone(self.timezone).strftime("%d.%m.%Y, %H:%M")  # 24.02.2022, 05:00

    def _encode_message(self, message: Message) -> str:
        header = "{} - {}".format(self._encode_timestamp(message.ts), message.user)
        body = ""
        if message.attachment:
            body = "{} (file attached)".format(message.attachment.get_name())
        if message.text:
            if body:
                body += "\n"
            # TODO: We need to escape the text in case it mimics to header format
            body += message.text
        return f"{header}: {body}"
