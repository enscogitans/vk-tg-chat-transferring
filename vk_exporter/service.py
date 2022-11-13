from pathlib import Path
from typing import Optional

from vk_exporter.repository import HistoryRepository
from vk_exporter.types import ChatHistory, Message, Photo, ChatRawHistory
from vk_exporter.vk_service import VkService


class ExporterService:
    def __init__(self, vk_service: VkService, repository: HistoryRepository) -> None:
        self.vk_service = vk_service
        self.repository = repository

    def export_history(self, peer_id: int, max_messages: Optional[int],
                       disable_progress_bar: bool, export_path: Path) -> None:
        raw_history = self.vk_service.get_raw_history(peer_id, max_messages, disable_progress_bar)
        history = self._parse_raw_history(raw_history)
        self.repository.save_history(history, export_path)

    def export_raw_history(self, peer_id: int, max_messages: Optional[int],
                           disable_progress_bar: bool, export_path: Path) -> None:
        raw_history = self.vk_service.get_raw_history(peer_id, max_messages, disable_progress_bar)
        self.repository.save_raw_history(raw_history, export_path)

    def export_history_from_raw_input(self, raw_input_path: Path, export_path: Path) -> None:
        raw_history = self.repository.load_raw_history(raw_input_path)
        history = self._parse_raw_history(raw_history)
        self.repository.save_history(history, export_path)

    @staticmethod
    def _parse_raw_history(raw_history: ChatRawHistory) -> ChatHistory:
        photo_opt: Optional[Photo] = None
        if raw_history.photo_url_opt is not None:
            assert raw_history.photo_size_opt is not None
            photo_opt = Photo(url=raw_history.photo_url_opt,
                              width=raw_history.photo_size_opt, height=raw_history.photo_size_opt)
        return ChatHistory(
            messages=list(map(Message.parse, raw_history.raw_messages)),
            title_opt=raw_history.title_opt,
            photo_opt=photo_opt,
        )
