from typing import Optional

from tqdm import tqdm
from vk_api.execute import VkFunction
from vk_api.vk_api import VkApiMethod

from vk_exporter.types import Message


def export_messages(api: VkApiMethod, peer_id: int,
                    max_count: Optional[int], disable_progress_bar: bool) -> list[Message]:
    raw_messages = export_raw_messages(api, peer_id, max_count, disable_progress_bar)
    return parse_raw_messages(raw_messages)


def parse_raw_messages(raw_messages: list[dict]) -> list[Message]:
    return list(map(Message.parse, raw_messages))


def export_raw_messages(api: VkApiMethod, peer_id: int,
                        max_count: Optional[int], disable_progress_bar: bool) -> list[dict]:
    last_message_id: int = _get_last_message_id(api, peer_id)
    total_messages: int = _get_messages_count(api, peer_id)  # Could have changed since the previous line
    if max_count is not None:
        total_messages = min(max_count, total_messages)

    result_reversed: list[dict] = []  # Last message is in the beginning of the list
    messages_loaded = 0
    with tqdm(total=total_messages, disable=disable_progress_bar, leave=True) as progress_bar:
        while messages_loaded < total_messages:
            new_batch = _get_raw_messages_reversed_batch(api, peer_id, last_message_id, messages_loaded)
            if not new_batch:
                break
            result_reversed += new_batch
            messages_loaded += len(new_batch)
            progress_bar.update(len(new_batch))
    if max_count is not None:
        result_reversed = result_reversed[:max_count]
    return result_reversed[::-1]


def _get_last_message_id(api: VkApiMethod, peer_id: int) -> int:
    conversation_info: dict = api.messages.getConversationsById(peer_ids=peer_id)
    assert len(conversation_info["items"]) == 1, conversation_info
    return conversation_info["items"][0]["last_message_id"]  # type: ignore


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
