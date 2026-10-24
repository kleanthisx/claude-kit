"""Optional Claude Code hook for Conclave.

UserPromptSubmit records the operator's words in the shared ledger. PreToolUse
enforces consensus/veto/scope state for tools wired to this hook.  Install in
observe mode first, then switch the settings entry to --mode enforce after both
MCP clients have passed conclave_health.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import Conclave, default_db_path
from push import spawn_pushes


STATE_CHANGING_TOOLS = {
    "Agent",
    "Task",
    "Workflow",
    "Edit",
    "Write",
    "NotebookEdit",
    "Bash",
    "PowerShell",
}


def last_operator_message(transcript: str) -> tuple[str, str]:
    """Return the newest real operator text and its best available stable id."""
    try:
        size = os.path.getsize(transcript)
        with open(transcript, "rb") as handle:
            handle.seek(max(0, size - 1024 * 1024))
            lines = handle.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return "", ""
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if value.get("type") != "user" or value.get("isMeta"):
            continue
        content = (value.get("message") or {}).get("content")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list) and not any(
            isinstance(item, dict) and item.get("type") == "tool_result" for item in content
        ):
            text = "\n".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        if text.strip():
            stable_id = str(value.get("uuid") or value.get("id") or size)
            return text.strip(), stable_id
    return "", ""


def hook_context(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": message,
                }
            },
            ensure_ascii=False,
        )
    )


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "CONCLAVE: " + reason,
                }
            },
            ensure_ascii=False,
        )
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--council", required=True)
    parser.add_argument("--db", default=str(default_db_path()))
    parser.add_argument("--mode", choices=("observe", "enforce"), default="observe")
    parser.add_argument(
        "--project-root",
        action="append",
        default=[],
        help="Only handle hook events whose cwd is inside one of these roots (repeatable).",
    )
    return parser.parse_args(argv)


def is_in_scope(cwd: str, project_roots: list[str]) -> bool:
    """Return whether a hook event belongs to this council's configured project."""
    if not project_roots:
        return True
    if not str(cwd or "").strip():
        return False
    try:
        candidate = Path(cwd).expanduser().resolve()
    except OSError:
        return False
    for value in project_roots:
        try:
            root = Path(value).expanduser().resolve()
            if candidate == root or root in candidate.parents:
                return True
        except OSError:
            continue
    return False


def handle_user_prompt(conclave: Conclave, data: dict[str, Any], mode: str) -> int:
    prompt = data.get("prompt") if isinstance(data.get("prompt"), str) else ""
    transcript = str(data.get("transcript_path") or "")
    transcript_id = ""
    if not prompt.strip():
        prompt, transcript_id = last_operator_message(transcript)
    if not prompt.strip():
        hook_context("CONCLAVE WARNING: the operator message could not be captured; tell the operator and do not infer new scope.")
        return 0
    session_id = str(data.get("session_id") or "unknown-session")
    if not transcript_id:
        try:
            transcript_id = str(os.path.getsize(transcript))
        except OSError:
            transcript_id = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    source_ref = f"claude:{session_id}:{transcript_id}:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]}"
    result = conclave.record_operator_message(
        prompt,
        "claude-code",
        source_ref,
        {
            "session_id": session_id,
            "cwd": str(data.get("cwd") or ""),
            "hook_mode": mode,
        },
    )
    if result.get("duplicate"):
        return 0
    spawn_pushes(conclave.db_path, conclave.council, result.get("deliveries"))
    hook_context(
        f"CONCLAVE recorded operator message #{result['message_id']} verbatim. "
        f"Codex must classify its intent impact before state-changing work continues. Gate mode: {mode}."
    )
    return 0


def handle_pre_tool(conclave: Conclave, data: dict[str, Any], mode: str) -> int:
    tool = str(data.get("tool_name") or "")
    if tool.startswith("mcp__conclave__") or tool not in STATE_CHANGING_TOOLS:
        return 0
    verdict = conclave.gate_decision(tool, data.get("tool_input") or {}, str(data.get("cwd") or ""))
    if verdict["decision"] == "deny" and mode == "enforce":
        deny(verdict["reason"])
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data = json.load(sys.stdin)
    except ValueError:
        if args.mode == "enforce":
            deny("hook input was not valid JSON; failing closed")
        return 0
    event = str(data.get("hook_event_name") or "")
    if not is_in_scope(str(data.get("cwd") or ""), args.project_root):
        return 0
    try:
        conclave = Conclave(Path(args.db), "claude", args.council)
        executable = shutil.which("claude")
        if executable:
            conclave.register_endpoint("claude_worker", executable, str(data.get("cwd") or ""))
        is_worker = os.environ.get("CONCLAVE_WORKER") == "1"
        if event == "UserPromptSubmit":
            if is_worker:
                return 0
            return handle_user_prompt(conclave, data, args.mode)
        if event == "PreToolUse":
            return handle_pre_tool(conclave, data, args.mode)
    except Exception as exc:  # a configured enforce gate must fail closed
        if event == "PreToolUse" and args.mode == "enforce":
            deny(f"governance state is unavailable ({exc}); failing closed")
        elif event == "UserPromptSubmit":
            hook_context(f"CONCLAVE WARNING: operator message was not recorded ({exc}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

