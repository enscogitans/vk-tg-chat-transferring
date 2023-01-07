import abc
import datetime

from tg_importer.types import Message, ChatHistory


class IEncoder(abc.ABC):
    @abc.abstractmethod
    def encode(self, history: ChatHistory) -> str: ...


class WhatsAppAndroidEncoder(IEncoder):
    def __init__(self, timezone: datetime.tzinfo):
        super().__init__()
        self.timezone = timezone

    def encode(self, history: ChatHistory) -> str:
        if not history.messages:
            raise ValueError("No messages provided")
        if not all(history.messages[i - 1].ts <= history.messages[i].ts for i in range(1, len(history.messages))):
            raise ValueError("Messages must be sorted by timestamp")
        if not history.is_group and 2 < (users_count := len(set(msg.user for msg in history.messages))):
            raise ValueError(f"Private chat contains too many users: {users_count}")
        chunks: list[str] = self._get_initial_messages_chunks(history)
        chunks += [self._encode_message(message) for message in history.messages]
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

    def _get_initial_messages_chunks(self, history: ChatHistory) -> list[str]:
        ts: datetime.datetime = history.messages[0].ts
        ts_str = self._encode_timestamp(ts)
        result: list[str]
        if history.is_group:
            result = [
                f"{ts_str} - You created group \"{history.title_opt}\"",  # Actually, this title is not used by Telegram
                f"{ts_str} - Messages you send to this group are now secured with end-to-end encryption. Tap for more info.",  # noqa: E501
            ]
        else:
            result = [
                f"{ts_str} - Messages you send to this chat and calls are now secured with end-to-end encryption. Tap for more info.",  # noqa: E501
            ]
        user = history.messages[0].user
        result.append(self._encode_message(  # TODO: investigate when dummy message is necessary
            Message(ts=ts, user=user, text="Dummy line. Otherwise Telegram ignores first message")))
        return result
