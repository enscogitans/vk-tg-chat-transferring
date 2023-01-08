from vk_tg_converter.arguments import ConverterArguments
from vk_tg_converter.service import IConverterService


class ConverterController:
    def __init__(self, service: IConverterService) -> None:
        self.service = service

    async def __call__(self, args: ConverterArguments) -> None:
        if args.input_file_opt is None:
            assert args.contacts_file_opt is not None
            self.service.export_dummy_history(args.contacts_file_opt, args.export_file)
        else:
            await self.service.export_converted_history(
                args.input_file_opt, args.contacts_file_opt, args.export_file,
                args.media_export_dir, args.disable_progress_bar)
