from pathlib import Path

from pychat_llm.persistence import ChatPersistence
from pychat_llm import history


class FileSystemChatPersistence(ChatPersistence):
    def list_chats(self) -> list[Path]:
        return history.list_chats()

    def save_chat(self, messages: list[tuple[str, bool]], title: str) -> Path:
        return history.save_chat(messages, title)

    def save_chat_to_path(
        self, messages: list[tuple[str, bool]], title: str, filepath: Path
    ) -> None:
        history.save_chat_to_path(messages, title, filepath)

    def load_chat(self, filepath: Path) -> tuple[str, list[tuple[str, bool]]]:
        return history.load_chat(filepath)
