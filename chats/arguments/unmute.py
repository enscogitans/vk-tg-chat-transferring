import argparse
from dataclasses import dataclass


@dataclass
class UnmuteArguments:
    chat_id: int


class UnmuteArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> "UnmuteArgumentsParser":
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        return UnmuteArgumentsParser()

    @staticmethod
    def parse_arguments(namespace: argparse.Namespace) -> UnmuteArguments:
        chat_id = namespace.chat
        assert isinstance(chat_id, int)
        return UnmuteArguments(
            chat_id=chat_id,
        )
