from pathlib import Path

from pychat_llm.llm import LLMProvider
from pychat_llm.persistence import ChatPersistence


class ChatService:
    def __init__(self, llm_provider: LLMProvider, persistence: ChatPersistence) -> None:
        self._llm = llm_provider
        self._persistence = persistence

    def get_llm_response(self, prompt: str) -> str:
        return self._llm.get_response(prompt)

    def list_chats(self) -> list[Path]:
        return self._persistence.list_chats()

    def save_chat(self, messages: list[tuple[str, bool]], title: str) -> Path:
        return self._persistence.save_chat(messages, title)

    def save_chat_to_path(
        self, messages: list[tuple[str, bool]], title: str, filepath: Path
    ) -> None:
        self._persistence.save_chat_to_path(messages, title, filepath)

    def load_chat(self, filepath: Path) -> tuple[str, list[tuple[str, bool]]]:
        return self._persistence.load_chat(filepath)
