import argparse

from common.vk_client import VkClient
from config import Config
from vk_exporter.arguments import VkExporterArguments
from vk_exporter.controller import VkExporterController
from vk_exporter.service import VkExporterService
from vk_exporter.storage import VkHistoryStorage
from vk_exporter.vk_service import VkService


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    VkExporterArguments.fill_parser(parser, config)


def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace, config: Config, vk_client: VkClient) -> None:
    args = VkExporterArguments(parser, namespace, config)
    service = VkExporterService(
        VkService(vk_client.get_api()),
        VkHistoryStorage(),
    )
    controller = VkExporterController(service)
    controller(args)
