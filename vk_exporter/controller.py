from vk_exporter.arguments import VkExporterArguments
from vk_exporter.service import IVkExporterService


class VkExporterController:
    def __init__(self, service: IVkExporterService) -> None:
        self.service = service

    def __call__(self, args: VkExporterArguments) -> None:
        if args.raw_import_file is not None:
            self.service.export_history_from_raw_input(args.raw_import_file, args.export_file)
        elif args.is_raw_export:
            assert args.chat_id is not None
            self.service.export_raw_history(args.chat_id, args.messages_count, args.is_disable_progress_bar,
                                            args.export_file)
        else:
            assert args.chat_id is not None
            self.service.export_history(args.chat_id, args.messages_count, args.is_disable_progress_bar,
                                        args.export_file)
