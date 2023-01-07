import abc
import pickle
from pathlib import Path

from tg_importer.types import ChatHistory


class ITgHistoryStorage(abc.ABC):
    @abc.abstractmethod
    def save_history(self, history: ChatHistory, path: Path) -> None: ...

    @abc.abstractmethod
    def load_history(self, path: Path) -> ChatHistory: ...


class TgHistoryStorage(ITgHistoryStorage):
    def save_history(self, history: ChatHistory, path: Path) -> None:
        with path.open("xb") as f:
            pickle.dump(history, f)

    def load_history(self, path: Path) -> ChatHistory:
        with path.open("rb") as f:
            history = pickle.load(f)
        assert isinstance(history, ChatHistory)
        return history
