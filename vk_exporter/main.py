from common.vk_client import VkClient
from vk_exporter.arguments import VkExporterArguments
from vk_exporter.controller import VkExporterController
from vk_exporter.service import VkExporterService
from vk_exporter.storage import VkHistoryStorage
from vk_exporter.vk_service import VkService


def main(args: VkExporterArguments, vk_client: VkClient) -> None:
    service = VkExporterService(
        VkService(vk_client.get_api()),
        VkHistoryStorage(),
    )
    controller = VkExporterController(service)
    controller(args)
