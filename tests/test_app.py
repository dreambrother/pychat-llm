import pytest

from pychat_llm.app import ChatApp, MessageBubble
from pychat_llm.service import ChatService


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
    async def test_history_saved_on_app_unmount(self, mock_llm, tmp_path):
        import pychat_llm.history as history_module

        original_history_dir = history_module.HISTORY_DIR
        history_module.HISTORY_DIR = tmp_path

        try:
            from pychat_llm.persistence_fs import FileSystemChatPersistence

            persistence = FileSystemChatPersistence()
            service = ChatService(llm_provider=mock_llm, persistence=persistence)
            app = ChatApp(chat_service=service)

            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#message-input")
                textarea = app.query_one("#message-input")
                textarea.text = "First message"
                await pilot.press("enter")
                await pilot.pause()
                await pilot.pause()
        finally:
            history_module.HISTORY_DIR = original_history_dir

        chats = list(tmp_path.glob("*.md"))
        assert len(chats) >= 1, f"Expected at least 1 chat file, got {len(chats)}"
        content = chats[0].read_text()
        assert "First message" in content

    @pytest.mark.asyncio
    async def test_subsequent_messages_appended_to_same_file(self, mock_llm, tmp_path):
        import pychat_llm.history as history_module

        original_history_dir = history_module.HISTORY_DIR
        history_module.HISTORY_DIR = tmp_path

        try:
            from pychat_llm.persistence_fs import FileSystemChatPersistence

            persistence = FileSystemChatPersistence()
            service = ChatService(llm_provider=mock_llm, persistence=persistence)
            app = ChatApp(chat_service=service)

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
        finally:
            history_module.HISTORY_DIR = original_history_dir

        chats = list(tmp_path.glob("*.md"))
        assert len(chats) == 1, f"Expected 1 chat file, got {len(chats)}: {list(tmp_path.glob('*'))}"
        content = chats[0].read_text()
        assert "Message one" in content
        assert "Message two" in content


class TestHistoryList:
    @pytest.mark.asyncio
    async def test_history_list_displays_saved_chats(self, mock_llm, tmp_path):
        import pychat_llm.history as history_module

        original_history_dir = history_module.HISTORY_DIR
        history_module.HISTORY_DIR = tmp_path

        try:
            from pychat_llm.service import ChatService
            from pychat_llm.persistence_fs import FileSystemChatPersistence

            chat_file = tmp_path / "test_chat.md"
            chat_file.write_text("# Test Chat\n\n---\n\n### You\n\nHello\n\n### Assistant\n\nHi\n")

            persistence = FileSystemChatPersistence()
            service = ChatService(llm_provider=mock_llm, persistence=persistence)
            app = ChatApp(chat_service=service)

            async with app.run_test() as pilot:
                await pilot.pause()
                app.action_open_chat()
                await pilot.pause()
                screen = app.screen
                list_view = screen.query_one("#chat-list-view")
                items = list(list_view.query_children())
                assert len(items) >= 1
        finally:
            history_module.HISTORY_DIR = original_history_dir


class TestChatLoading:
    @pytest.mark.asyncio
    async def test_chat_loaded_from_history_file(self, mock_llm, tmp_path):
        import pychat_llm.history as history_module

        original_history_dir = history_module.HISTORY_DIR
        history_module.HISTORY_DIR = tmp_path

        try:
            from pychat_llm.service import ChatService
            from pychat_llm.persistence_fs import FileSystemChatPersistence

            chat_file = tmp_path / "existing_chat.md"
            chat_file.write_text(
                "# Existing Chat\n\n---\n\n### You\n\nUser message\n\n### Assistant\n\nAssistant reply\n"
            )

            persistence = FileSystemChatPersistence()
            service = ChatService(llm_provider=mock_llm, persistence=persistence)
            app = ChatApp(chat_service=service)

            async with app.run_test() as pilot:
                await pilot.pause()
                app._load_chat(chat_file)
                await pilot.pause()
                container = app.query_one("#messages")
                bubbles = list(container.query(MessageBubble))
                user_bubbles = [b for b in bubbles if b.is_user]
                assert any("User message" in b.text for b in user_bubbles)
        finally:
            history_module.HISTORY_DIR = original_history_dir