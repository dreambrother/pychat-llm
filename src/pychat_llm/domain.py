from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMessage:
    id: int
    text: str
    is_user: bool
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HistoryItem:
    id: str
    title: str
    created_at: datetime
