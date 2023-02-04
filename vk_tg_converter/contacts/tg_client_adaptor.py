import abc
from types import TracebackType
from typing import Type, Optional

from pyrogram import types

from common.tg_client import TgClient


class ITgClientAdaptor(abc.ABC):
    async def __aenter__(self) -> "ITgClientAdaptor":
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        return

    @abc.abstractmethod
    async def get_contacts(self) -> list[types.User]: ...

    @abc.abstractmethod
    async def get_me(self) -> types.User: ...


class TgClientAdaptor(ITgClientAdaptor):
    def __init__(self, client: TgClient):
        self.client = client

    async def __aenter__(self) -> "TgClientAdaptor":
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_contacts(self) -> list[types.User]:
        return await self.client.get_contacts()

    async def get_me(self) -> types.User:
        return await self.client.get_me()
