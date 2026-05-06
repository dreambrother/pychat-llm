import argparse

from pychat_llm.app import ChatApp
from pychat_llm.history import HistoryService
from pychat_llm.providers.mock import MockLLMProvider
from pychat_llm.repository import HistoryFileRepository, HistoryInMemoryRepository


def main():
    parser = argparse.ArgumentParser(description="PyChat LLM")
    parser.add_argument(
        "-s", "--storage",
        choices=["file", "memory"],
        default="file",
        help="Storage backend (default: file)",
    )
    args = parser.parse_args()

    if args.storage == "memory":
        repository = HistoryInMemoryRepository()
    else:
        repository = HistoryFileRepository("history")

    app = ChatApp(
        HistoryService(repository),
        MockLLMProvider(),
    )
    app.run()


if __name__ == "__main__":
    main()