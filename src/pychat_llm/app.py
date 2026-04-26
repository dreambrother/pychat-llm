import random

from textual.app import App, ComposeResult
from textual.containers import Container, Right, VerticalScroll
from textual.widgets import Footer, Static, TextArea

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
        padding: 1;
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


class ChatApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #chat-container {
        height: 1fr;
        padding: 1;
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
    """

    def compose(self) -> ComposeResult:
        yield Container(
            MessageContainer(id="messages"),
            id="chat-container",
        )
        yield Container(
            TextArea(id="message-input", placeholder="Type a message... (Ctrl/Cmd+Enter to send)"),
            id="input-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#message-input", TextArea).focus()

    async def on_key(self, event) -> None:
        if event.key in ("ctrl+enter", "meta+enter"):
            textarea = self.query_one("#message-input", TextArea)
            text = textarea.text.strip()
            if not text:
                return
            textarea.text = ""
            await self.add_message(text, is_user=True)
            await self.add_message(random.choice(LLM_RESPONSES), is_user=False)

    async def add_message(self, text: str, is_user: bool = False) -> None:
        container = self.query_one("#messages", MessageContainer)
        bubble = MessageBubble(text, is_user=is_user)
        bubble.add_class("user" if is_user else "assistant")
        if is_user:
            wrapper = Right(bubble)
        else:
            wrapper = bubble
        await container.mount(wrapper)
        container.scroll_end(animate=False)


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
