from common.tg_client import TgClient
from config import Config
from tg_importer.arguments import TgImporterArguments
from tg_importer.controller import TgImporterController
from tg_importer.encoder import WhatsAppAndroidEncoder
from tg_importer.service import TgImporterService
from tg_importer.storage import ITgHistoryStorage


async def main(args: TgImporterArguments, tg_config: Config.Telegram,
               tg_client: TgClient, tg_history_storage: ITgHistoryStorage) -> None:
    encoder = WhatsAppAndroidEncoder(tg_config.timezone)

    async with tg_client:
        service = TgImporterService(
            tg_client,
            tg_history_storage,
            encoder,
            tg_config.max_simultaneously_uploaded_files,
        )
        controller = TgImporterController(service)
        await controller(args)
