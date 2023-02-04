import abc
import pickle
import json
from pathlib import Path

from vk_exporter.types import ChatHistory, ChatRawHistory


class IVkHistoryStorage(abc.ABC):
    @abc.abstractmethod
    def save_raw_history(self, raw_history: ChatRawHistory, path: Path) -> None: ...

    @abc.abstractmethod
    def load_raw_history(self, path: Path) -> ChatRawHistory: ...

    @abc.abstractmethod
    def save_history(self, history: ChatHistory, path: Path) -> None: ...

    @abc.abstractmethod
    def load_history(self, path: Path) -> ChatHistory: ...


class VkHistoryStorage(IVkHistoryStorage):
    def save_raw_history(self, raw_history: ChatRawHistory, path: Path) -> None:
        with path.open("x") as f:
            dct = {
                "raw_messages": raw_history.raw_messages,
                "title_opt": raw_history.title_opt,
                "photo_url_opt": raw_history.photo_url_opt,
                "photo_size_opt": raw_history.photo_size_opt,
            }
            json.dump(dct, f, ensure_ascii=False, indent=2)

    def load_raw_history(self, path: Path) -> ChatRawHistory:
        with path.open() as f:
            dct = json.load(f)
        assert isinstance(dct, dict), type(dct)
        return ChatRawHistory(
            raw_messages=dct["raw_messages"],
            title_opt=dct["title_opt"],
            photo_url_opt=dct["photo_url_opt"],
            photo_size_opt=dct["photo_size_opt"],
        )

    def save_history(self, history: ChatHistory, path: Path) -> None:
        with path.open("xb") as f:
            pickle.dump(history, f)

    def load_history(self, path: Path) -> ChatHistory:
        with path.open("rb") as f:
            history = pickle.load(f)
        assert isinstance(history, ChatHistory)
        return history
