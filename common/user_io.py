import abc
from typing import Any


class IUserOutput(abc.ABC):
    @abc.abstractmethod
    def print(self, *args: Any, sep: str = " ", end: str = "\n") -> None: ...


class IUserIo(IUserOutput):
    @abc.abstractmethod
    def input(self, prompt: str = "") -> str: ...

    @abc.abstractmethod
    def secure_input(self, prompt: str = "") -> str: ...


class ConsoleUserOutput(IUserOutput):
    def print(self, *args: Any, sep: str = " ", end: str = "\n") -> None:
        return print(*args, sep=sep, end=end)


class MemoryUserOutput(IUserOutput):
    def __init__(self) -> None:
        self.outputs: list[str] = []

    def print(self, *args: Any, sep: str = " ", end: str = "\n") -> None:
        self.outputs.append(sep.join(map(str, args)) + end)
