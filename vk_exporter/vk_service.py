from dataclasses import dataclass
from typing import Optional

from tqdm import tqdm
from vk_api.execute import VkFunction
from vk_api.vk_api import VkApiMethod

from vk_exporter.types import ChatRawHistory


@dataclass
class _ConversationInfo:
    last_message_id: int
    title_opt: Optional[str]
    photo_url_opt: Optional[str]
    photo_size_opt: Optional[int]


class VkService:
    def __init__(self, api: VkApiMethod) -> None:
        self.api = api

    def get_raw_history(self, peer_id: int, max_messages: Optional[int], disable_progress_bar: bool) -> ChatRawHistory:
        conversation_info: _ConversationInfo = self._get_conversation_info(peer_id)
        total_messages: int = self._get_messages_count(peer_id)  # Could have changed since the previous line
        if max_messages is not None:
            total_messages = min(max_messages, total_messages)

        messages_reversed: list[dict] = []  # Last message is in the beginning of the list
        messages_loaded = 0
        with tqdm(total=total_messages, disable=disable_progress_bar, leave=True) as progress_bar:
            while messages_loaded < total_messages:
                new_batch = self._get_raw_messages_reversed_batch(
                    peer_id, conversation_info.last_message_id, messages_loaded)
                if not new_batch:
                    break
                messages_reversed += new_batch
                messages_loaded += len(new_batch)
                progress_bar.update(len(new_batch))
        if max_messages is not None:
            messages_reversed = messages_reversed[:max_messages]
        return ChatRawHistory(
            raw_messages=messages_reversed[::-1],
            title_opt=conversation_info.title_opt,
            photo_url_opt=conversation_info.photo_url_opt,
            photo_size_opt=conversation_info.photo_size_opt,
        )

    def _get_messages_count(self, peer_id: int) -> int:
        response: dict = self.api.messages.getHistory(peer_id=peer_id, count=0)
        count = response["count"]
        assert isinstance(count, int)
        return count

    def _get_conversation_info(self, peer_id: int) -> _ConversationInfo:
        last_message_id: int
        title_opt: Optional[str] = None
        photo_url_opt: Optional[str] = None
        photo_size_opt: Optional[int] = None

        response: dict = self.api.messages.getConversationsById(peer_ids=peer_id)
        assert len(response["items"]) == 1, response
        conversation: dict = response["items"][0]

        last_message_id = conversation["last_message_id"]
        assert isinstance(last_message_id, int), type(last_message_id)
        if "chat_settings" in conversation:
            # Options are "chat", "user" and "group"
            assert conversation["peer"]["type"] == "chat", \
                f"Only chats supposed to have title and photo: {conversation=}"
            title_opt = conversation["chat_settings"]["title"]
            assert isinstance(title_opt, str)
            if "photo" in conversation["chat_settings"]:
                photo_size_opt = 200  # https://dev.vk.com/reference/objects/chat#photo_200
                photo_url_opt = conversation["chat_settings"]["photo"][f"photo_{photo_size_opt}"]
                assert isinstance(photo_url_opt, str)
        else:
            assert conversation["peer"]["type"] != "chat", f"Chat supposed to have title and photo: {conversation}"

        return _ConversationInfo(
            last_message_id=last_message_id,
            title_opt=title_opt,
            photo_url_opt=photo_url_opt,
            photo_size_opt=photo_size_opt,
        )

    def _get_raw_messages_reversed_batch(self, peer_id: int, last_message_id: int, offset: int) -> list[dict]:
        # batch_size is <= 200 due to https://dev.vk.com/method/messages.getHistory
        # max_iter is <= 25 due to https://dev.vk.com/method/execute
        script_args = ("peer_id", "last_message_id", "initial_offset")
        script = """
            var batch_size = 200;
            var max_iter = 25;

            var messages = [];
            var offset = %(initial_offset)s;
            var i = 0;
            while (i < max_iter) {
                var history = API.messages.getHistory({
                    "peer_id": %(peer_id)s,
                    "start_message_id": %(last_message_id)s,
                    "offset": offset,
                    "count": batch_size,
                });
                messages = messages + history.items;
                offset = offset + batch_size;
                i = i + 1;
            }
            return messages;
        """
        func = VkFunction(code=script, args=script_args, clean_args=script_args)
        messages_raw: list[dict] = func(self.api, peer_id, last_message_id, offset)
        return messages_raw
