from datetime import datetime
from pathlib import Path

from pychat_llm.domain import ChatMessage, HistoryItem


class HistoryService:
    def __init__(self):
        self._message_seq = 1
        self._chat: list[ChatMessage] = []
        self._history: dict[str, list[ChatMessage]] = {}

    def add_message(self, text: str, is_user: bool):
        item = ChatMessage(id=self._msg_id(), text=text, is_user=is_user)
        self._chat.append(item)

    def _msg_id(self) -> int:
        new_id = self._message_seq
        self._message_seq += 1
        return new_id

    def list_chats(self) -> list[HistoryItem]:
        return [
            HistoryItem(
                id=chat_id,
                title=self._get_chat_title(chat),
                created_at=self._get_created_at(chat),
            )
            for chat_id, chat in self._history.items()
        ]

    def get_chat(self, chat_id: str | None = None) -> tuple[str, list[ChatMessage]]:
        if (chat_id):
            chat = self._history[chat_id]
        else:
            chat = self._chat
        return self._get_chat_title(chat), chat

    def save(self) -> None:
        if not self._has_user_message(self._chat):
            return
        chat_id = self._get_created_at(self._chat).strftime("%d%m%y-%H%M%S")
        self._history[chat_id] = self._chat

    def get_chat_title(self, chat_id: str) -> str:
        return self._get_chat_title(self._history[chat_id])

    def _get_chat_title(self, chat: list[ChatMessage]) -> str:
        if not self._has_user_message(chat):
            return ""
        return (chat[1:2])[0].text[:30]

    def _has_user_message(self, chat: list[ChatMessage]) -> bool:
        return any(item.is_user for item in chat)

    def _get_created_at(self, chat: list[ChatMessage]) -> datetime:
        return chat[0].created_at

    def new_chat(self) -> None:
        self._chat = []

# TODO remove
HISTORY_DIR = Path("history")


def ensure_history_dir() -> None:
    HISTORY_DIR.mkdir(exist_ok=True)


def list_chats() -> list[Path]:
    ensure_history_dir()
    return sorted(HISTORY_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def save_chat(messages: list[tuple[str, bool]], title: str) -> Path:
    ensure_history_dir()
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:50] or "untitled"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_title}.md"
    filepath = HISTORY_DIR / filename
    _write_chat_file(messages, title, filepath)
    return filepath


def save_chat_to_path(messages: list[tuple[str, bool]], title: str, filepath: Path) -> None:
    _write_chat_file(messages, title, filepath)


def _write_chat_file(messages: list[tuple[str, bool]], title: str, filepath: Path) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        for text, is_user in messages:
            sender = "You" if is_user else "Assistant"
            f.write(f"### {sender}\n\n{text}\n\n")


def load_chat(filepath: Path) -> tuple[str, list[tuple[str, bool]]]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    title = lines[0].lstrip("# ").strip() if lines else "Untitled"
    messages = []
    current_sender = None
    current_text = []
    for line in lines:
        if line.startswith("### You"):
            if current_sender and current_text:
                messages.append(("\n".join(current_text).strip(), current_sender == "You"))
            current_sender = "You"
            current_text = []
        elif line.startswith("### Assistant"):
            if current_sender and current_text:
                messages.append(("\n".join(current_text).strip(), current_sender == "You"))
            current_sender = "Assistant"
            current_text = []
        elif current_sender is not None and not line.startswith("#") and not line.startswith("---"):
            current_text.append(line)
    if current_sender and current_text:
        messages.append(("\n".join(current_text).strip(), current_sender == "You"))
    return title, messages
