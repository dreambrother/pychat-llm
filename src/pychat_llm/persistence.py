from abc import ABC, abstractmethod
from pathlib import Path


class ChatPersistence(ABC):
    @abstractmethod
    def list_chats(self) -> list[Path]:
        raise NotImplementedError

    @abstractmethod
    def save_chat(self, messages: list[tuple[str, bool]], title: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def save_chat_to_path(
        self, messages: list[tuple[str, bool]], title: str, filepath: Path
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_chat(self, filepath: Path) -> tuple[str, list[tuple[str, bool]]]:
        raise NotImplementedError
