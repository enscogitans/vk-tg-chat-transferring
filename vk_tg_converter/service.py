import abc
from pathlib import Path

from config import Config
from tg_importer.storage import ITgHistoryStorage
from vk_exporter.storage import IVkHistoryStorage
from vk_tg_converter.contacts.storage import IContactsStorage
from vk_tg_converter.contacts.username_manager import ContactInfo
from vk_tg_converter.converters.history_converter_factory import IHistoryConverterFactory
from vk_tg_converter.dummy_history_provider import IDummyHistoryProvider


class IConverterService(abc.ABC):
    @abc.abstractmethod
    def export_dummy_history(self, contacts_file: Path, export_file: Path) -> None: ...

    @abc.abstractmethod
    async def export_converted_history(self, vk_history_file: Path,
                                       contacts_file_opt: None | Path, export_file: Path,
                                       media_export_dir: Path, disable_progress_bar: bool) -> None: ...


class ConverterService(IConverterService):
    def __init__(self, vk_config: Config.Vk,
                 contacts_storage: IContactsStorage,
                 history_converter_factory: IHistoryConverterFactory,
                 dummy_history_provider: IDummyHistoryProvider,
                 vk_history_storage: IVkHistoryStorage,
                 tg_history_storage: ITgHistoryStorage) -> None:
        self.vk_config = vk_config
        self.contacts_storage = contacts_storage
        self.history_converter_factory = history_converter_factory
        self.dummy_history_provider = dummy_history_provider
        self.vk_history_storage = vk_history_storage
        self.tg_history_storage = tg_history_storage

    def export_dummy_history(self, contacts_file: Path, export_file: Path) -> None:
        contacts = self.contacts_storage.load_contacts(contacts_file)
        tg_history = self.dummy_history_provider.make_history(contacts)
        self.tg_history_storage.save_history(tg_history, export_file)

    async def export_converted_history(self, vk_history_file: Path, contacts_file_opt: None | Path,
                                       export_file: Path, media_export_dir: Path, disable_progress_bar: bool) -> None:
        contacts_opt: None | list[ContactInfo] = None
        if contacts_file_opt is not None:
            contacts_opt = self.contacts_storage.load_contacts(contacts_file_opt)
        history_converter = self.history_converter_factory.create(contacts_opt, media_export_dir, disable_progress_bar)
        vk_history = self.vk_history_storage.load_history(vk_history_file)
        tg_history = await history_converter.convert(vk_history)
        self.tg_history_storage.save_history(tg_history, export_file)
