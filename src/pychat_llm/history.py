from datetime import datetime

from pychat_llm.domain import ChatMessage, HistoryItem
from pychat_llm.repository import HistoryRepository


class HistoryService:
    def __init__(self, history_repo: HistoryRepository):
        self._message_seq = 1
        self._chat: list[ChatMessage] = []
        self._history_repo = history_repo

    def add_message(self, text: str, is_user: bool) -> ChatMessage:
        item = ChatMessage(id=self._msg_id(), text=text, is_user=is_user)
        self._chat.append(item)
        return item

    def _msg_id(self) -> int:
        new_id = self._message_seq
        self._message_seq += 1
        return new_id

    def list_chats(self) -> list[HistoryItem]:
        chats = self._history_repo.list_chats()
        chats.sort(key=lambda item: item.created_at, reverse=True)
        return chats

    def get_chat(self, chat_id: str | None = None) -> tuple[str, list[ChatMessage]]:
        if chat_id:
            chat = self._history_repo.load(chat_id)
        else:
            chat = self._chat
        return self._get_chat_title(chat), chat

    def save(self) -> None:
        if not self._has_user_message(self._chat):
            return
        history_item = HistoryItem(
            id=self._get_created_at(self._chat).strftime("%d%m%y-%H%M%S"),
            title=self._get_chat_title(self._chat),
            created_at=self._get_created_at(self._chat),
        )
        self._history_repo.save(history_item, self._chat)

    def get_chat_title(self, chat_id: str) -> str:
        return self._get_chat_title(self._history_repo.load(chat_id))

    def new_chat(self) -> None:
        self._chat = []

    def _get_chat_title(self, chat: list[ChatMessage]) -> str:
        if not self._has_user_message(chat):
            return ""
        return (chat[1:2])[0].text[:30]

    def _has_user_message(self, chat: list[ChatMessage]) -> bool:
        return any(item.is_user for item in chat)

    def _get_created_at(self, chat: list[ChatMessage]) -> datetime:
        return chat[0].created_at
