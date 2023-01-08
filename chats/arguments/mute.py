import argparse
from dataclasses import dataclass


@dataclass
class MuteArguments:
    chat_id: int


class MuteArgumentsParser:
    @staticmethod
    def fill_parser(parser: argparse.ArgumentParser) -> "MuteArgumentsParser":
        parser.add_argument("chat", type=int, metavar="CHAT_ID")
        return MuteArgumentsParser()

    @staticmethod
    def parse_arguments(namespace: argparse.Namespace) -> MuteArguments:
        chat_id = namespace.chat
        assert isinstance(chat_id, int)
        return MuteArguments(
            chat_id=chat_id,
        )
