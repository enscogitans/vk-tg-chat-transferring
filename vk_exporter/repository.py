import pickle
from pathlib import Path

from vk_exporter.types import ChatHistory, ChatRawHistory


class VkHistoryRepository:
    @staticmethod
    def save_raw_history(raw_history: ChatRawHistory, path: Path) -> None:
        with path.open("xb") as f:
            dct = {
                "raw_messages": raw_history.raw_messages,
                "title_opt": raw_history.title_opt,
                "photo_url_opt": raw_history.photo_url_opt,
                "photo_size_opt": raw_history.photo_size_opt,
            }
            pickle.dump(dct, f)

    @staticmethod
    def load_raw_history(path: Path) -> ChatRawHistory:
        with path.open("rb") as f:
            dct = pickle.load(f)
        assert isinstance(dct, dict), type(dct)
        return ChatRawHistory(
            raw_messages=dct["raw_messages"],
            title_opt=dct["title_opt"],
            photo_url_opt=dct["photo_url_opt"],
            photo_size_opt=dct["photo_size_opt"],
        )

    @staticmethod
    def save_history(history: ChatHistory, path: Path) -> None:
        with path.open("xb") as f:
            pickle.dump(history, f)

    @staticmethod
    def load_history(path: Path) -> ChatHistory:
        with path.open("rb") as f:
            history = pickle.load(f)
        assert isinstance(history, ChatHistory)
        return history
