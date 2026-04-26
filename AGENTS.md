# pychat-llm

## What this is
Textual TUI chat app (Python). LLM responses are currently mocked with random strings.

## Setup & run
```
poetry install
poetry run pychat-llm   # or: python -m pychat_llm.app
```

## Project structure
- `src/pychat_llm/app.py` — main app, UI widgets (`ChatApp`, `ChatListScreen`, `ChatInput`, `MessageBubble`, `MessageContainer`)
- `src/pychat_llm/service.py` — `ChatService` coordinating LLM and persistence
- `src/pychat_llm/llm.py` — `LLMProvider` abstract protocol
- `src/pychat_llm/providers/mock.py` — `MockLLMProvider` implementation
- `src/pychat_llm/persistence.py` — `ChatPersistence` abstract protocol
- `src/pychat_llm/persistence_fs.py` — `FileSystemChatPersistence` implementation
- `src/pychat_llm/history.py` — low-level file I/O (used by persistence_fs)
- `tests/` — empty (no test framework configured yet)

## Code organization
- **Top-to-bottom reading order** — functions/methods that call other functions must be defined before the functions they call
- **Classes in modules** — main class (entrypoint) should be defined first, before classes it uses
- CSS should be defined in the class it belongs to, not in parent containers

## Anti-patterns to avoid
- **High-level modules must not depend on low-level modules** — use abstractions (`Protocol`/`ABC`)
- Dependencies should be injected via constructor, not imported directly in modules that use them
- `ChatApp` receives `ChatService` via constructor — it should never import `history` directly

### Single Responsibility Principle
- **Each class has one reason to change** — UI classes handle UI, service classes handle business logic
- `ChatApp` manages UI state only — persistence and LLM calls go through `ChatService`
- CSS should be defined in the class it belongs to, not in parent containers

### Open/Closed Principle
- **Open for extension, closed for modification** — use abstractions to add new functionality
- To add a new LLM provider: implement `LLMProvider` protocol, inject via `ChatService`
- To add new persistence: implement `ChatPersistence` protocol

### Liskov Substitution Principle
- Subclasses must be substitutable for base classes without breaking behavior
- All `LLMProvider` implementations must return a string from `get_response()`
- All `ChatPersistence` implementations must match the `ChatPersistence` protocol signature

### Interface Segregation
- Keep interfaces narrow — prefer many small protocols over one large one
- `LLMProvider` has one method, `ChatPersistence` has four related methods

### Anti-patterns to avoid
- **No direct imports from `history` in `app.py`** — use `ChatService` instead
- **No hardcoded LLM responses in UI code** — use `LLMProvider` abstraction
- **No file I/O in Screen classes** — pass data via constructor or callbacks

## Key details
- Package manager: **Poetry** (v2+ build backend)
- Python: **>=3.14**
- Only dependency: `textual`
- CLI entry: `pychat-llm` → `pychat_llm.app:main`
- Send message: **Enter** in the TextArea (Ctrl+Enter for new line)
- No linter, formatter, typechecker, or CI configured yet
- Python code must follow **PEP 8**
- Update `AGENTS.md` whenever implementation changes
