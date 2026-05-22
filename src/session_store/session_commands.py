from __future__ import annotations

from typing import Any

from cli.display import print_error, print_info
from session_store.store import SessionMeta, SessionStore


def format_short_id(session_id: str) -> str:
    return session_id[:8]


def _pad_right(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    return text + (" " * (width - len(text)))


def _pad_left(text: str, width: int) -> str:
    if len(text) >= width:
        return text[-width:]
    return (" " * (width - len(text))) + text


def format_session_row(
    session: SessionMeta,
    index: int,
    current_session_id: str | None,
    index_width: int,
    label_width: int,
) -> str:
    active = session.last_active.replace("T", " ")
    if len(active) >= 16:
        active = active[5:16]
    marker = "*" if current_session_id == session.session_id else " "
    index_cell = _pad_left(f"{marker}{index}", index_width)
    label = _pad_right(session.label, label_width)
    active_cell = _pad_right(active, 11)
    count_text = _pad_left(f"{session.message_count} 条", 6)
    return (
        f"{index_cell} | {label} | {active_cell} | "
        f"{count_text} | {format_short_id(session.session_id)}"
    )


def print_session_list(store: SessionStore) -> list[SessionMeta]:
    sessions = store.list_sessions()
    if not sessions:
        print_info("暂无会话.")
        return []
    label_width = max(8, min(24, max(len(item.label) for item in sessions)))
    index_width = max(4, len(str(len(sessions))) + 1)
    header_index = _pad_left("No.", index_width)
    header_label = _pad_right("Label", label_width)
    print_info(f"{header_index} | {header_label} | LastActive  |  消息数 | SessionID")
    for idx, session in enumerate(sessions, start=1):
        print_info(format_session_row(session, idx, store.current_session_id, index_width, label_width))
    return sessions


def _print_help() -> None:
    print_info("会话命令:")
    print_info("  /new [label]                创建并切换新会话")
    print_info("  /list                       列出会话（含当前标记、编号、消息数）")
    print_info("  /switch <index_or_prefix>   按编号或ID前缀切换会话")
    print_info("  /delete <index_or_prefix>   删除会话（支持编号或ID前缀）")
    print_info("  /help                       查看本帮助")
    print_info("示例:")
    print_info("  /new 饮食优化")
    print_info("  /switch 2")
    print_info("  /delete 2")


def handle_session_command(
    user_input: str, store: SessionStore
) -> tuple[bool, list[dict[str, Any]] | None]:
    raw = user_input.strip()
    if not raw.startswith("/"):
        return False, None

    parts = raw.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command == "/help":
        _print_help()
        return True, None

    if command == "/new":
        sid = store.create_session(arg or None)
        print_info(f"已创建并切换会话: {format_short_id(sid)} ({store.get_label(sid)})")
        return True, []

    if command == "/list":
        print_session_list(store)
        return True, None

    if command == "/switch":
        if not arg:
            print_error("用法: /switch <index_or_prefix>")
            return True, None
        sessions = store.list_sessions()
        try:
            sid = store.resolve_session(arg, sessions)
        except ValueError as exc:
            msg = str(exc)
            if "不唯一" in msg:
                matches = store.find_prefix_matches(arg)
                match_ids = {item.session_id for item in matches}
                print_error(f"{msg}，候选如下:")
                label_width = max(8, min(24, max(len(item.label) for item in sessions)))
                index_width = max(4, len(str(len(sessions))) + 1)
                for idx, session in enumerate(sessions, start=1):
                    if session.session_id in match_ids:
                        print_info(
                            format_session_row(
                                session,
                                idx,
                                store.current_session_id,
                                index_width,
                                label_width,
                            )
                        )
                print_info("请使用 /switch <编号> 重试。")
            else:
                print_error(msg)
            return True, None
        _, messages = store.switch_session(sid)
        print_info(f"已切换会话: {format_short_id(sid)}")
        return True, messages

    if command == "/delete":
        if not arg:
            print_error("用法: /delete <index_or_prefix>")
            return True, None
        sessions = store.list_sessions()
        try:
            target_id = store.resolve_session(arg, sessions)
            target_label = store.get_label(target_id)
        except ValueError as exc:
            print_error(str(exc))
            return True, None
        try:
            deleted_id, new_current_id, new_messages = store.delete_session(target_id)
        except ValueError as exc:
            print_error(str(exc))
            return True, None

        print_info(f"已删除会话: {target_label} ({format_short_id(deleted_id)})")
        if new_current_id is not None and new_messages is not None:
            new_label = store.get_label(new_current_id)
            print_info(f"当前会话切换为: {new_label} ({format_short_id(new_current_id)})")
            return True, new_messages
        return True, None

    print_error(f"未知命令: {command}，输入 /help 查看支持命令")
    return True, None

