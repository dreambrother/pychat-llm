import json
import os
from abc import ABC, abstractmethod

from pychat_llm.domain import ChatMessage, HistoryItem


class HistoryRepository(ABC):
    @abstractmethod
    def save(self, history_item: HistoryItem) -> None:
        pass

    @abstractmethod
    def add_to_chat(self, chat_id: str, *messages: ChatMessage) -> None:
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

    def save(self, history_item: HistoryItem) -> None:
        self._history[history_item.id] = history_item

    def add_to_chat(self, chat_id: str, *messages: ChatMessage) -> None:
        self._chats.setdefault(chat_id, []).extend(messages)

    def _generate_item_id(self, history_item: HistoryItem) -> str:
        return history_item.created_at.strftime("%d%m%y-%H%M%S")

    def load(self, chat_id: str) -> list[ChatMessage]:
        return self._chats[chat_id]

    def list_chats(self) -> list[HistoryItem]:
        return list(self._history.values())


class HistoryFileRepository(HistoryRepository):
    def __init__(self, history_dir: str):
        self._history_dir = history_dir
        self._chats_dir = os.path.join(history_dir, "chats")

    def save(self, history_item: HistoryItem) -> None:
        self._ensure_dirs()
        item_path = os.path.join(self._history_dir, f"{history_item.id}.json")
        with open(item_path, "w") as f:
            json.dump(history_item.to_dict(), f)

    def add_to_chat(self, chat_id: str, *messages: ChatMessage) -> None:
        self._ensure_dirs()
        chat_path = os.path.join(self._chats_dir, f"{chat_id}.json")
        with open(chat_path, "a") as f:
            lines = [json.dumps(m.to_dict()) for m in messages]
            f.write(os.linesep.join(lines) + os.linesep)

    def _ensure_dirs(self) -> None:
        if not os.path.exists(self._history_dir):
            os.makedirs(self._history_dir)
        if not os.path.exists(self._chats_dir):
            os.makedirs(self._chats_dir)

    def load(self, chat_id: str) -> list[ChatMessage]:
        if not os.path.exists(self._chats_dir):
            return []
        with open(os.path.join(self._chats_dir, f"{chat_id}.json"), "r") as f:
            json_items = f.readlines()
            return [ChatMessage.from_dict(json.loads(i)) for i in json_items]

    def list_chats(self) -> list[HistoryItem]:
        if not os.path.exists(self._history_dir):
            return []
        result = []
        for item in os.listdir(self._history_dir):
            if not item.endswith(".json"):
                continue
            with open(os.path.join(self._history_dir, item), "r") as f:
                item_data = json.load(f)
                result.append(HistoryItem.from_dict(item_data))
        return result
