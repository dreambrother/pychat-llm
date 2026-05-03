from typing import Callable

from pychat_llm.domain import HistoryItem
from pychat_llm.history import HistoryService
from pychat_llm.llm import LLMProvider
from pychat_llm.providers.mock import MockLLMProvider
from pychat_llm.repository import HistoryFileRepository, HistoryInMemoryRepository
from textual.app import App, ComposeResult
from textual.containers import Container, Right, VerticalScroll
from textual.widgets import Footer, Static, TextArea, Label, ListView, ListItem
from textual.binding import Binding
from textual.message import Message
from textual.screen import Screen


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

    def __init__(self, history_service: HistoryService, llm_provider: LLMProvider, **kwargs):
        super().__init__(**kwargs)
        self._history_service = history_service
        self._llm_provider = llm_provider

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
        # TODO extract to LLMService
        await self.add_message("Привет! Я ваш ассистент. Чем могу помочь?", is_user=False)

    async def add_message(self, text: str, is_user: bool = False) -> None:
        self._history_service.add_message(text, is_user)
        container = self.query_one("#messages", MessageContainer)
        bubble = MessageBubble(text, is_user=is_user)
        bubble.add_class("user" if is_user else "assistant")
        if is_user:
            wrapper = Right(bubble)
        else:
            wrapper = bubble
        # TODO: why await?
        await container.mount(wrapper)
        container.scroll_end(animate=False)

    def _add_message_sync(self, text: str, is_user: bool = False) -> None:
        container = self.query_one("#messages", MessageContainer)
        bubble = MessageBubble(text, is_user=is_user)
        bubble.add_class("user" if is_user else "assistant")
        if is_user:
            wrapper = Right(bubble)
        else:
            wrapper = bubble
        # TODO: why no await?
        container.mount(wrapper)
        container.scroll_end(animate=False)

    async def action_new_chat(self) -> None:
        self._history_service.save()
        self._history_service.new_chat()
        self._clear_messages()
        await self.add_message("Привет! Я ваш ассистент. Чем могу помочь?", is_user=False)

    def action_open_chat(self) -> None:
        def on_dismiss(history_item: HistoryItem | None) -> None:
            if history_item:
                self._load_chat(history_item.id)
        chat_paths = self._history_service.list_chats()
        self.push_screen(ChatListScreen(chat_paths, self._history_service.get_chat_title), on_dismiss)

    def _load_chat(self, chat_id: str) -> None:
        title, messages = self._history_service.get_chat(chat_id)
        if not messages:
            return
        self._clear_messages()
        self.chat_title = title
        for message in messages:
            self._add_message_sync(message.text, is_user=message.is_user)

    def _clear_messages(self) -> None:
        container = self.query_one("#messages", MessageContainer)
        container.remove_children()
        self.chat_title = "Untitled"

    def on_unmount(self) -> None:
        self._history_service.save()

    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        textarea = self.query_one("#message-input", ChatInput)
        text = textarea.text.strip()
        if not text:
            return
        textarea.text = ""
        await self.add_message(text, is_user=True)
        title, messages = self._history_service.get_chat()
        if len(messages) == 2:
            # TODO is it used?
            self.chat_title = title
        await self.add_message(self._llm_provider.get_response(text), is_user=False)
        self._history_service.save()


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
    DEFAULT_CSS = """
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
    """


class ChatListScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, history_items: list[HistoryItem], load_chat_fn: Callable[[str], str], **kwargs):
        super().__init__(**kwargs)
        self._history_items = history_items
        self._load_chat_fn = load_chat_fn
        self._chat_items: dict[str, HistoryItem] = {}

    def compose(self) -> ComposeResult:
        yield Label("Select a chat to open:", id="chat-list-title")
        if not self._history_items:
            yield Label("No saved chats yet.", id="no-chats")
        else:
            items = []
            for item in self._history_items:
                title = self._load_chat_fn(item.id)
                date_str = item.created_at.strftime("%d.%m.%Y %H:%M")
                item_id = f"chat-list-item-{item.id}"
                self._chat_items[item_id] = item
                list_item = ListItem(Label(f"{date_str}  {title}"), id=item_id)
                items.append(list_item)
            yield ListView(*items, id="chat-list-view")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id:
            self.dismiss(self._chat_items[event.item.id])


def main():
    repository = HistoryFileRepository("history")
    app = ChatApp(
        HistoryService(repository),
        MockLLMProvider()
    )
    app.run()


if __name__ == "__main__":
    main()
