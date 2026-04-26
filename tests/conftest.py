from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pychat_llm.app import ChatApp
from pychat_llm.service import ChatService


class MockLLMProvider:
    def __init__(self, response: str = "Mock response"):
        self._response = response

    def get_response(self, prompt: str) -> str:
        return self._response


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def mock_persistence(tmp_path):
    mock = MagicMock()
    mock.list_chats.return_value = []
    mock.save_chat.return_value = tmp_path / "test_chat.md"
    mock.load_chat.return_value = ("Test Chat", [])
    return mock


@pytest.fixture
def chat_service(mock_llm, mock_persistence):
    return ChatService(llm_provider=mock_llm, persistence=mock_persistence)


@pytest.fixture
def app_with_service(chat_service):
    return ChatApp(chat_service=chat_service)


@pytest.fixture
def app_with_real_persistence(mock_llm, tmp_path):
    import pychat_llm.history as history_module

    original_history_dir = history_module.HISTORY_DIR
    history_module.HISTORY_DIR = tmp_path

    from pychat_llm.persistence_fs import FileSystemChatPersistence

    persistence = FileSystemChatPersistence()
    service = ChatService(llm_provider=mock_llm, persistence=persistence)
    app = ChatApp(chat_service=service)

    yield app, tmp_path

    history_module.HISTORY_DIR = original_history_dir