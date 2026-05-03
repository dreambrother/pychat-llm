from pychat_llm.repository import HistoryInMemoryRepository, HistoryRepository
import pytest

from pychat_llm.app import ChatApp
from pychat_llm.history import HistoryService


class MockLLMProvider:
    def __init__(self, response: str = "Mock response"):
        self._response = response

    def get_response(self, prompt: str) -> str:
        return self._response


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def in_mem_repo() -> HistoryRepository:
    return HistoryInMemoryRepository()


@pytest.fixture
def history_service(in_mem_repo):
    return HistoryService(history_repo=in_mem_repo)


@pytest.fixture
def app_with_service(history_service, mock_llm):
    return ChatApp(history_service=history_service, llm_provider=mock_llm)
