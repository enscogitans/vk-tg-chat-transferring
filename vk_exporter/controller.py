from vk_exporter.arguments import ExporterArguments
from vk_exporter.service import IExporterService


class ExporterController:
    def __init__(self, service: IExporterService) -> None:
        self.service = service

    def __call__(self, args: ExporterArguments) -> None:
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
