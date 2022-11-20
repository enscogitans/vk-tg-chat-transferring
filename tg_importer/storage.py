import pickle
from pathlib import Path

from tg_importer.types import ChatHistory


class TgHistoryStorage:
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
