import pytest

from datetime import datetime
from pychat_llm.app import ChatApp, MessageBubble
from pychat_llm.domain import ChatMessage, HistoryItem
from pychat_llm.history import HistoryService


class TestWelcomeMessage:
    @pytest.mark.asyncio
    async def test_welcome_message_displayed_on_app_open(self, app_with_service):
        app = app_with_service
        async with app.run_test() as pilot:
            await pilot.pause()
            container = app.query_one("#messages")
            bubbles = list(container.query(MessageBubble))
            assert len(bubbles) >= 1
            welcome = bubbles[0]
            assert "Привет" in welcome.text or "ассистент" in welcome.text.lower()


class TestMessageSending:
    @pytest.mark.asyncio
    async def test_user_message_displayed_in_chat(self, app_with_service):
        app = app_with_service
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#message-input")
            textarea = app.query_one("#message-input")
            textarea.text = "Hello world"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            container = app.query_one("#messages")
            bubbles = list(container.query(MessageBubble))
            user_messages = [b for b in bubbles if b.is_user]
            assert len(user_messages) >= 1, f"Expected user message, got {len(user_messages)} bubbles: {[b.text for b in bubbles]}"
            assert any("Hello world" in b.text for b in user_messages)

    @pytest.mark.asyncio
    async def test_llm_response_displayed_after_user_message(self, app_with_service):
        app = app_with_service
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#message-input")
            textarea = app.query_one("#message-input")
            textarea.text = "Test message"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            container = app.query_one("#messages")
            bubbles = list(container.query(MessageBubble))
            assistant_messages = [b for b in bubbles if not b.is_user]
            assert len(assistant_messages) >= 1, f"Expected assistant message, got {len(assistant_messages)} bubbles"
            assert any("Mock response" in b.text for b in assistant_messages)


class TestHistoryPersistence:
    @pytest.mark.asyncio
    async def test_history_saved_on_app_unmount(self, mock_llm, in_mem_repo):
        history_service = HistoryService(history_repo=in_mem_repo)
        app = ChatApp(history_service=history_service, llm_provider=mock_llm)

        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#message-input")
            textarea = app.query_one("#message-input")
            textarea.text = "First message"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()

        assert len(in_mem_repo._history) >= 1, f"Expected at least 1 saved chat, got {len(in_mem_repo._history)}"
        title, messages = history_service.get_chat()
        assert any("First message" in msg.text for msg in messages)

    @pytest.mark.asyncio
    async def test_subsequent_messages_appended_to_same_chat(self, mock_llm, in_mem_repo):
        history_service = HistoryService(history_repo=in_mem_repo)
        app = ChatApp(history_service=history_service, llm_provider=mock_llm)

        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#message-input")
            textarea = app.query_one("#message-input")
            textarea.text = "Message one"
            await pilot.press("enter")
            await pilot.pause()
            textarea.text = "Message two"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()

        assert len(in_mem_repo._history) == 1, f"Expected 1 saved chat, got {len(in_mem_repo._history)}: {list(in_mem_repo._history.keys())}"
        title, messages = history_service.get_chat()
        assert any("Message one" in msg.text for msg in messages)
        assert any("Message two" in msg.text for msg in messages)


class TestHistoryList:
    @pytest.mark.asyncio
    async def test_history_list_displays_saved_chats(self, mock_llm, in_mem_repo):
        history_service = HistoryService(history_repo=in_mem_repo)
        in_mem_repo._chats["test_chat"] = [
            ChatMessage(id=1, text="Welcome", is_user=False, created_at=datetime.now()),
            ChatMessage(id=2, text="Hello", is_user=True, created_at=datetime.now()),
        ]
        in_mem_repo._history["test_chat"] = HistoryItem(id="test_chat", title="Test Chat", created_at=datetime.now())
        app = ChatApp(history_service=history_service, llm_provider=mock_llm)

        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_open_chat()
            await pilot.pause()
            screen = app.screen
            list_view = screen.query_one("#chat-list-view")
            items = list(list_view.query_children())
            assert len(items) >= 1


class TestChatLoading:
    @pytest.mark.asyncio
    async def test_chat_loaded_from_history(self, mock_llm, in_mem_repo):
        history_service = HistoryService(history_repo=in_mem_repo)
        in_mem_repo._chats["existing_chat"] = [
            ChatMessage(id=1, text="Welcome", is_user=False, created_at=datetime.now()),
            ChatMessage(id=2, text="User message", is_user=True, created_at=datetime.now()),
            ChatMessage(id=3, text="Assistant reply", is_user=False, created_at=datetime.now()),
        ]
        in_mem_repo._history["existing_chat"] = HistoryItem(id="existing_chat", title="Existing Chat", created_at=datetime.now())
        app = ChatApp(history_service=history_service, llm_provider=mock_llm)

        async with app.run_test() as pilot:
            await pilot.pause()
            app._load_chat("existing_chat")
            await pilot.pause()
            container = app.query_one("#messages")
            bubbles = list(container.query(MessageBubble))
            user_bubbles = [b for b in bubbles if b.is_user]
            assert any("User message" in b.text for b in user_bubbles)
