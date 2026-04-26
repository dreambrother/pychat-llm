import random
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Right, VerticalScroll
from textual.widgets import Footer, Static, TextArea, Button, Label, ListView, ListItem
from textual.binding import Binding
from textual.message import Message
from textual.screen import Screen

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


LLM_RESPONSES = [
    "Интересный вопрос! Дайте подумать...",
    "Понимаю вашу обеспокоенность. Вот что могу сказать.",
    "Отличная мысль! Вот мой взгляд на эту тему.",
    "Исходя из моих знаний, вот что могу поделиться.",
    "Это сложная тема. Позвольте разложить её по полочкам.",
    "Спасибо за вопрос. Вот подробный ответ.",
    "Вот что я думаю — это зависит от нескольких факторов.",
    "Интересно! Позвольте дать немного контекста.",
    "С радостью помогу. Вот моё мнение на этот счёт.",
    "Распространённый вопрос. Вот развёрнутый ответ.",
]


class ChatInput(TextArea):
    BINDINGS = [
        Binding("enter", "submit", "Submit", show=True, priority=True),
        Binding("ctrl+enter", "newline", "New line", show=True),
    ]

    def action_submit(self) -> None:
        self.post_message(self.Submitted(self))

    def action_newline(self) -> None:
        self.insert("\n")

    class Submitted(Message):
        def __init__(self, text_area: TextArea) -> None:
            super().__init__()
            self.text_area = text_area


class MessageBubble(Static):
    def __init__(self, text: str, is_user: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.is_user = is_user

    def render(self) -> str:
        return self.text


class MessageContainer(VerticalScroll):
    DEFAULT_CSS = """
    MessageContainer {
        height: 1fr;
        border: solid gray;
        padding: 1 2 1 1;
    }

    MessageBubble {
        width: auto;
        max-width: 80%;
        padding: 1 2;
        margin-bottom: 1;
    }

    MessageBubble.user {
        background: $primary;
        color: $text;
    }

    MessageBubble.assistant {
        background: $surface;
        color: $text;
    }
    """


class ChatListScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("Select a chat to open:", id="chat-list-title")
        chats = list_chats()
        if not chats:
            yield Label("No saved chats yet.", id="no-chats")
        else:
            items = []
            for chat_path in chats:
                title, _ = load_chat(chat_path)
                display = f"{title}  ({chat_path.name})"
                items.append(ListItem(Label(display), name=str(chat_path)))
            yield ListView(*items, id="chat-list-view")
        yield Button("Cancel", id="cancel-chat-list", variant="default")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        filepath = Path(event.item.name)
        self.dismiss(filepath)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-chat-list":
            self.dismiss(None)


class ChatApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #chat-container {
        height: 1fr;
        padding: 1;
    }

    #header {
        dock: top;
        text-align: center;
        padding: 1;
        margin: 1 2 0 2;
        background: $panel;
        color: $text;
    }

    #input-container {
        height: auto;
        padding: 1;
        border-top: solid gray;
    }

    #message-input {
        width: 1fr;
        height: auto;
        max-height: 5;
    }

    #chat-list-title {
        text-align: center;
        padding: 1;
    }

    #no-chats {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }

    #chat-list-view {
        height: 1fr;
        margin: 1 4;
        border: solid gray;
    }

    #cancel-chat-list {
        width: auto;
        margin: 1 4;
    }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_chat", "New Chat", show=True),
        Binding("ctrl+o", "open_chat", "Open Chat", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: list[tuple[str, bool]] = []
        self.chat_title = "Untitled"
        self.chat_file: Path | None = None

    def compose(self) -> ComposeResult:
        yield Static("PyChat LLM", id="header")
        yield Container(
            MessageContainer(id="messages"),
            id="chat-container",
        )
        yield Container(
            ChatInput(id="message-input", placeholder="Type a message... (Enter to send)"),
            id="input-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#message-input", ChatInput).focus()
        await self.add_message("Привет! Я ваш ассистент. Чем могу помочь?", is_user=False)

    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        textarea = self.query_one("#message-input", ChatInput)
        text = textarea.text.strip()
        if not text:
            return
        textarea.text = ""
        await self.add_message(text, is_user=True)
        if len(self.messages) == 2:
            self.chat_title = text[:60]
        await self.add_message(random.choice(LLM_RESPONSES), is_user=False)
        self._save_current_chat()

    async def add_message(self, text: str, is_user: bool = False) -> None:
        self.messages.append((text, is_user))
        container = self.query_one("#messages", MessageContainer)
        bubble = MessageBubble(text, is_user=is_user)
        bubble.add_class("user" if is_user else "assistant")
        if is_user:
            wrapper = Right(bubble)
        else:
            wrapper = bubble
        await container.mount(wrapper)
        container.scroll_end(animate=False)

    def _has_user_messages(self) -> bool:
        return any(is_user for _, is_user in self.messages)

    def _save_current_chat(self) -> None:
        if not self._has_user_messages():
            return
        if self.chat_file:
            save_chat_to_path(self.messages, self.chat_title, self.chat_file)
        else:
            self.chat_file = save_chat(self.messages, self.chat_title)

    def _clear_messages(self) -> None:
        container = self.query_one("#messages", MessageContainer)
        container.remove_children()
        self.messages = []
        self.chat_title = "Untitled"
        self.chat_file = None

    async def action_new_chat(self) -> None:
        self._save_current_chat()
        self._clear_messages()
        await self.add_message("Привет! Я ваш ассистент. Чем могу помочь?", is_user=False)

    def action_open_chat(self) -> None:
        def on_dismiss(filepath: Path | None) -> None:
            if filepath and filepath.exists():
                self._save_current_chat()
                self._load_chat(filepath)
        self.push_screen(ChatListScreen(), on_dismiss)

    async def _load_chat(self, filepath: Path) -> None:
        self._clear_messages()
        title, messages = load_chat(filepath)
        self.chat_title = title
        self.chat_file = filepath
        if messages:
            for text, is_user in messages:
                await self.add_message(text, is_user=is_user)
        else:
            await self.add_message("Привет! Я ваш ассистент. Чем могу помочь?", is_user=False)

    def on_unmount(self) -> None:
        self._save_current_chat()


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
