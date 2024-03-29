from tg_importer.arguments import TgImporterArguments
from tg_importer.service import ITgImporterService


class TgImporterController:
    def __init__(self, service: ITgImporterService) -> None:
        self.service = service

    async def __call__(self, args: TgImporterArguments) -> None:
        await self.service.import_history(args.chat_id, args.tg_history_path, args.disable_progress_bar)
