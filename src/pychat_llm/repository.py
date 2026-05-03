import json
import os
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


class HistoryFileRepository(HistoryRepository):
    def __init__(self, history_dir: str):
        self._history_dir = history_dir

    def save(self, history_item: HistoryItem, chat: list[ChatMessage]):
        if not os.path.exists(self._history_dir):
            os.makedirs(self._history_dir)
        chat_path = os.path.join(self._history_dir, f"{history_item.id}.json")
        with open(chat_path, "w") as f:
            chat_data = {
                "item": history_item.to_dict(),
                "chat": [m.to_dict() for m in chat],
            }
            json.dump(chat_data, f)

    def load(self, chat_id: str) -> list[ChatMessage]:
        if not os.path.exists(self._history_dir):
            return []
        with open(os.path.join(self._history_dir, f"{chat_id}.json"), "r") as f:
            chat_data = json.load(f)
            return [ChatMessage.from_dict(m) for m in chat_data["chat"]]

    def list_chats(self) -> list[HistoryItem]:
        if not os.path.exists(self._history_dir):
            return []
        result = []
        for item in os.listdir(self._history_dir):
            if not item.endswith(".json"):
                continue
            with open(os.path.join(self._history_dir, item), "r") as f:
                chat_data = json.load(f)
                result.append(HistoryItem.from_dict(chat_data["item"]))
        return result
