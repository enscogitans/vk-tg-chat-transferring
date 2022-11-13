import argparse

from common.vk_client import VkClient
from config import Config
from vk_exporter.arguments import ExporterArguments
from vk_exporter.controller import ExporterController
from vk_exporter.service import ExporterService
from vk_exporter.repository import HistoryRepository
from vk_exporter.vk_service import VkService


def fill_parser(parser: argparse.ArgumentParser, config: Config) -> None:
    ExporterArguments.fill_parser(parser, config)


def main(parser: argparse.ArgumentParser, namespace: argparse.Namespace, config: Config, vk_client: VkClient) -> None:
    args = ExporterArguments(parser, namespace, config)
    service = ExporterService(
        VkService(vk_client.get_api()),
        HistoryRepository(),
    )
    controller = ExporterController(service)
    controller(args)
