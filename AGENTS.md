# pychat-llm

## What this is
Textual TUI chat app (Python). LLM responses are currently mocked with random strings.

## Setup & run
```
poetry install
poetry run pychat-llm   # or: python -m pychat_llm.app
```

## Project structure
- `src/pychat_llm/app.py` — single file, contains `ChatApp` (entrypoint) and all widgets
- `tests/` — empty (no test framework configured yet)

## Key details
- Package manager: **Poetry** (v2+ build backend)
- Python: **>=3.14**
- Only dependency: `textual`
- CLI entry: `pychat-llm` → `pychat_llm.app:main`
- Send message: **Ctrl/Cmd+Enter** in the TextArea
- No linter, formatter, typechecker, or CI configured yet
- Python code must follow **PEP 8**
- Update `AGENTS.md` whenever implementation changes
