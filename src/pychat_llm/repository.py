import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from pychat_llm.domain import ChatMessage, HistoryItem

logger = logging.getLogger(__name__)


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

    def load(self, chat_id: str) -> list[ChatMessage]:
        return self._chats.get(chat_id, [])

    def list_chats(self) -> list[HistoryItem]:
        return list(self._history.values())


class HistoryFileRepository(HistoryRepository):
    def __init__(self, history_dir: str):
        self._history_dir = Path(history_dir)
        self._chats_dir = self._history_dir / "chats"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._chats_dir.mkdir(parents=True, exist_ok=True)

    def save(self, history_item: HistoryItem) -> None:
        item_path = self._history_dir / f"{history_item.id}.json"
        try:
            with open(item_path, "w") as f:
                json.dump(history_item.to_dict(), f)
        except OSError:
            logger.exception("Failed to save history item %s", history_item.id)
            raise

    def add_to_chat(self, chat_id: str, *messages: ChatMessage) -> None:
        chat_path = self._chats_dir / f"{chat_id}.json"
        lines = [json.dumps(m.to_dict()) for m in messages]
        try:
            with open(chat_path, "a") as f:
                f.write("\n".join(lines) + "\n")
        except OSError:
            logger.exception("Failed to append messages to chat %s", chat_id)
            raise

    def load(self, chat_id: str) -> list[ChatMessage]:
        chat_path = self._chats_dir / f"{chat_id}.json"
        if not chat_path.exists():
            return []
        try:
            with open(chat_path, "r") as f:
                json_items = f.readlines()
            return [ChatMessage.from_dict(json.loads(line)) for line in json_items if line.strip()]
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load chat %s", chat_id)
            return []

    def list_chats(self) -> list[HistoryItem]:
        if not self._history_dir.exists():
            return []
        result = []
        for item_path in self._history_dir.glob("*.json"):
            try:
                with open(item_path, "r") as f:
                    item_data = json.load(f)
                result.append(HistoryItem.from_dict(item_data))
            except (OSError, json.JSONDecodeError):
                logger.warning("Skipping corrupted history file: %s", item_path)
                continue
        return result