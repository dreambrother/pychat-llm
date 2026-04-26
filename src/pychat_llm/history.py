from datetime import datetime
from pathlib import Path

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
