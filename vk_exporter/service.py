import abc
from pathlib import Path

from vk_exporter.storage import IVkHistoryStorage
from vk_exporter.types import ChatHistory, Message, Photo, ChatRawHistory
from vk_exporter.vk_service import IVkService


class IExporterService(abc.ABC):
    @abc.abstractmethod
    def export_history(self, peer_id: int, max_messages: None | int,
                       disable_progress_bar: bool, export_path: Path) -> None: ...

    @abc.abstractmethod
    def export_raw_history(self, peer_id: int, max_messages: None | int,
                           disable_progress_bar: bool, export_path: Path) -> None: ...

    @abc.abstractmethod
    def export_history_from_raw_input(self, raw_input_path: Path, export_path: Path) -> None: ...


class ExporterService(IExporterService):
    def __init__(self, vk_service: IVkService, storage: IVkHistoryStorage) -> None:
        self.vk_service = vk_service
        self.storage = storage

    def export_history(self, peer_id: int, max_messages: None | int,
                       disable_progress_bar: bool, export_path: Path) -> None:
        raw_history = self.vk_service.get_raw_history(peer_id, max_messages, disable_progress_bar)
        history = self._parse_raw_history(raw_history)
        self.storage.save_history(history, export_path)

    def export_raw_history(self, peer_id: int, max_messages: None | int,
                           disable_progress_bar: bool, export_path: Path) -> None:
        raw_history = self.vk_service.get_raw_history(peer_id, max_messages, disable_progress_bar)
        self.storage.save_raw_history(raw_history, export_path)

    def export_history_from_raw_input(self, raw_input_path: Path, export_path: Path) -> None:
        raw_history = self.storage.load_raw_history(raw_input_path)
        history = self._parse_raw_history(raw_history)
        self.storage.save_history(history, export_path)

    @staticmethod
    def _parse_raw_history(raw_history: ChatRawHistory) -> ChatHistory:
        photo_opt: None | Photo = None
        if raw_history.photo_url_opt is not None:
            assert raw_history.photo_size_opt is not None
            photo_opt = Photo(url=raw_history.photo_url_opt,
                              width=raw_history.photo_size_opt, height=raw_history.photo_size_opt)
        return ChatHistory(
            messages=list(map(Message.parse, raw_history.raw_messages)),
            title_opt=raw_history.title_opt,
            photo_opt=photo_opt,
        )
