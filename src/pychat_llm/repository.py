from abc import ABC, abstractmethod

from pychat_llm.domain import ChatMessage, HistoryItem


class HistoryRepository(ABC):
    @abstractmethod
    def save(self, history_item: HistoryItem, chat: list[ChatMessage]):
        pass

    @abstractmethod
    def load(self, chat_id: str) -> list[ChatMessage]:
        pass

    @abstractmethod
    def list_chats(self) -> list[HistoryItem]:
        pass


class HistoryInMemoryRepository(HistoryRepository):
    def __init__(self):
        self._chats: dict[str, list[ChatMessage]] = {}
        self._history: dict[str, HistoryItem] = {}

    def save(self, history_item: HistoryItem, chat: list[ChatMessage]):
        self._chats[history_item.id] = chat
        self._history[history_item.id] = history_item

    def _generate_item_id(self, history_item: HistoryItem) -> str:
        return history_item.created_at.strftime("%d%m%y-%H%M%S")

    def load(self, chat_id: str) -> list[ChatMessage]:
        return self._chats[chat_id]

    def list_chats(self) -> list[HistoryItem]:
        return list(self._history.values())
