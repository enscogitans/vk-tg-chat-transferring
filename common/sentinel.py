from typing import Optional


class Sentinel:
    """Sentinel which is a singleton"""
    _instance: Optional["Sentinel"] = None

    def __new__(cls) -> "Sentinel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
