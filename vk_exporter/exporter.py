from typing import Optional

from tqdm import tqdm
from vk_api.execute import VkFunction
from vk_api.vk_api import VkApiMethod

from vk_exporter.types import Message, ChatHistory, Photo


def export_history(api: VkApiMethod, peer_id: int,
                   max_count: Optional[int], disable_progress_bar: bool) -> ChatHistory:
    raw_history = export_raw_history(api, peer_id, max_count, disable_progress_bar)
    return parse_raw_history(raw_history)


def parse_raw_history(raw_history: dict) -> ChatHistory:
    photo: Optional[Photo] = None
    if raw_history["photo"] is not None:
        size: int = raw_history["photo_size"]
        assert size is not None
        photo = Photo(url=raw_history["photo"], width=size, height=size)
    return ChatHistory(
        messages=list(map(Message.parse, raw_history["messages"])),
        title=raw_history["title"],
        photo=photo,
    )


def export_raw_history(api: VkApiMethod, peer_id: int,
                       max_count: Optional[int], disable_progress_bar: bool) -> dict:
    last_message_id, title_opt, photo_url_opt, photo_size_opt = _get_conversation_info(api, peer_id)
    total_messages: int = _get_messages_count(api, peer_id)  # Could have changed since the previous line
    if max_count is not None:
        total_messages = min(max_count, total_messages)

    messages_reversed: list[dict] = []  # Last message is in the beginning of the list
    messages_loaded = 0
    with tqdm(total=total_messages, disable=disable_progress_bar, leave=True) as progress_bar:
        while messages_loaded < total_messages:
            new_batch = _get_raw_messages_reversed_batch(api, peer_id, last_message_id, messages_loaded)
            if not new_batch:
                break
            messages_reversed += new_batch
            messages_loaded += len(new_batch)
            progress_bar.update(len(new_batch))
    if max_count is not None:
        messages_reversed = messages_reversed[:max_count]
    return {
        "messages": messages_reversed[::-1],
        "title": title_opt,
        "photo": photo_url_opt,
        "photo_size": photo_size_opt,
    }


def _get_conversation_info(api: VkApiMethod, peer_id: int) -> tuple[int, Optional[str], Optional[str], Optional[int]]:
    response: dict = api.messages.getConversationsById(peer_ids=peer_id)
    assert len(response["items"]) == 1, response
    conversation: dict = response["items"][0]

    last_message_id: int = conversation["last_message_id"]
    title_opt: Optional[str] = None
    photo_url_opt: Optional[str] = None
    photo_size_opt: Optional[int] = None

    if "chat_settings" in conversation:
        assert conversation["peer"]["type"] == "chat", f"Only chats supposed to have title and photo: {conversation}"
        title_opt = conversation["chat_settings"]["title"]
        if "photo" in conversation["chat_settings"]:
            photo_size_opt = 200  # https://dev.vk.com/reference/objects/chat#photo_200
            photo_url_opt = conversation["chat_settings"]["photo"][f"photo_{photo_size_opt}"]
    else:
        assert conversation["peer"]["type"] != "chat", f"Chat supposed to have title and photo: {conversation}"

    return last_message_id, title_opt, photo_url_opt, photo_size_opt


def _get_messages_count(api: VkApiMethod, peer_id: int) -> int:
    response: dict = api.messages.getHistory(peer_id=peer_id, count=0)
    return response["count"]  # type: ignore


def _get_raw_messages_reversed_batch(api: VkApiMethod, peer_id: int, last_message_id: int, offset: int) -> list[dict]:
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
    messages_raw: list[dict] = func(api, peer_id, last_message_id, offset)
    return messages_raw
