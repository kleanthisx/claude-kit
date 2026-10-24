"""Conclave MCP server over stdio.

Run one process per client, bound to that client's identity.  Both processes
point at the same SQLite file, which makes the conversation and governance
state genuinely shared while preventing either model from impersonating the
other through tool arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import Conclave, ConclaveError, default_db_path
from push import spawn_pushes


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "title": {"type": "string", "description": "Short name for this immutable plan revision."},
        "objective": {"type": "string", "description": "The outcome this revision must deliver."},
        "user_intent": {
            "type": "string",
            "description": "Faithful summary of the operator's intent; do not turn implementation ideas into requirements.",
        },
        "requirements": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "non_goals": {"type": "array", "items": {"type": "string"}},
        "architecture": {"type": "array", "items": {"type": "string"}},
        "tasks": {"type": "array", "items": {"type": "string"}},
        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "budget": {"type": "string", "description": "Time/model/spend bound and escalation point."},
        "allowed_paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Absolute paths or working-directory-relative roots Claude may change.",
        },
        "allowed_commands": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Allowed state-changing command prefixes. Avoid '*' except for an explicit operator override.",
        },
        "change_summary": {
            "type": "string",
            "description": "For revision 2+, what changed and why. Empty is valid for revision 1.",
        },
    },
    "required": [
        "title",
        "objective",
        "user_intent",
        "requirements",
        "constraints",
        "non_goals",
        "architecture",
        "tasks",
        "acceptance_criteria",
        "risks",
        "budget",
        "allowed_paths",
        "allowed_commands",
    ],
}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "conclave_health",
        "description": "Verify this actor's Conclave connection, identity, shared database and schema.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "conclave_register_endpoint",
        "description": (
            "Register this identity's push-notification endpoint. The server may auto-register a supported "
            "client endpoint; use this only when the client supplies an explicit session address."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "transport": {
                    "type": "string",
                    "enum": ["codex_queue", "claude_worker"],
                },
                "address": {"type": "string"},
                "cwd": {"type": "string", "default": ""},
            },
            "required": ["transport", "address"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_open_council",
        "description": (
            "Open or re-open the shared project council. Call this once before deliberation. "
            "It does not approve work or start execution."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "objective": {"type": "string"},
            },
            "required": ["project", "objective"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_get_state",
        "description": (
            "Read the authoritative council state: current immutable plan, signatures, execution, "
            "unreviewed operator intent, vetoes, evidence and recent peer messages."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "recent_messages": {"type": "integer", "minimum": 0, "maximum": 100, "default": 20}
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_push",
        "description": (
            "Push a durable message to every other council participant. The push only wakes recipients; "
            "each recipient retrieves authoritative content with conclave_pull."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "description": "For example: operating_brief, question, answer, challenge, decision, status.",
                },
                "body": {"type": "string"},
                "metadata": {"type": "object", "default": {}},
            },
            "required": ["kind", "body"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_send_message",
        "description": (
            "Legacy directed form of conclave_push. Send a durable peer message and immediately wake its "
            "recipient; a message does not substitute for a plan signature or audit action."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "enum": ["codex", "claude", "other", "all"]},
                "kind": {
                    "type": "string",
                    "description": "For example: operating_brief, question, answer, challenge, decision, status.",
                },
                "body": {"type": "string"},
                "metadata": {"type": "object", "default": {}},
            },
            "required": ["recipient", "kind", "body"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_read_messages",
        "description": (
            "Read peer/operator messages after a cursor. wait_seconds performs a bounded long poll so the "
            "two AIs can deliberate without a filesystem queue or busy loop."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "after_id": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                "wait_seconds": {"type": "number", "minimum": 0, "maximum": 30, "default": 0},
                "include_own": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_pull",
        "description": (
            "Pull and acknowledge this participant's durable push inbox. A push notification is only a wake-up "
            "signal; call this tool to retrieve the authoritative messages."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_record_operator_message",
        "description": (
            "Record the operator's words verbatim with provenance. Every new operator message becomes pending "
            "intent review and pauses active execution until Codex classifies its scope impact. Do not paraphrase."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "source": {"type": "string", "description": "For example claude-session or codex-session."},
                "source_ref": {
                    "type": "string",
                    "description": "Stable session/message identifier for deduplication.",
                },
                "metadata": {"type": "object", "default": {}},
            },
            "required": ["text", "source"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_review_operator_message",
        "description": (
            "CODEx ONLY. Classify a recorded operator message against the living intent. Scope changes or "
            "conflicts stale the plan and require a new dual-approved revision."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "impact": {
                    "type": "string",
                    "enum": ["no_change", "clarifies", "changes_scope", "conflicts"],
                },
                "note": {"type": "string"},
            },
            "required": ["message_id", "impact", "note"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_submit_plan",
        "description": (
            "Submit an immutable plan revision for peer deliberation. Claude normally authors it as execution "
            "lead. Any content change creates a new hash and invalidates prior signatures."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"plan": PLAN_SCHEMA},
            "required": ["plan"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_review_plan",
        "description": (
            "Approve, request changes to, or veto the current immutable plan revision. Execution unlocks only "
            "when Claude and Codex both approve the exact same plan hash."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "integer"},
                "decision": {"type": "string", "enum": ["approve", "request_changes", "veto"]},
                "note": {"type": "string"},
            },
            "required": ["plan_id", "decision", "note"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_start_execution",
        "description": (
            "CLAUDE ONLY. Start heavy implementation after dual approval. Claude remains execution lead and "
            "may spawn agents only while the execution is running."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"plan_id": {"type": "integer"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_report_event",
        "description": (
            "CLAUDE ONLY. Report observable execution evidence. Use agent_spawned before delegation, "
            "test_result for verification, and completion_requested to hand the result to Codex for audit."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": [
                        "agent_spawned",
                        "progress",
                        "decision",
                        "test_result",
                        "risk",
                        "blocked",
                        "scope_change_requested",
                        "completion_requested",
                    ],
                },
                "summary": {"type": "string"},
                "details": {"type": "object", "default": {}},
            },
            "required": ["kind", "summary"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_issue_veto",
        "description": (
            "CODEx ONLY. Pause active execution with a concrete violated clause, evidence and correction. "
            "A veto remains blocking until Codex explicitly releases it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "clause": {"type": "string"},
                "evidence": {"type": "string"},
                "required_correction": {"type": "string"},
                "severity": {"type": "string", "enum": ["blocking", "critical"], "default": "blocking"},
            },
            "required": ["clause", "evidence", "required_correction"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_respond_veto",
        "description": "CLAUDE ONLY. Answer a veto with the correction and observable evidence; this does not self-release it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "veto_id": {"type": "integer"},
                "response": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["veto_id", "response", "evidence"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_resolve_veto",
        "description": "CODEx ONLY. Release a satisfied veto or maintain it with an actionable note.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "veto_id": {"type": "integer"},
                "decision": {"type": "string", "enum": ["release", "maintain"]},
                "note": {"type": "string"},
            },
            "required": ["veto_id", "decision", "note"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_audit",
        "description": (
            "CODEx ONLY. Record a milestone verdict, request rework, resume a resolved block, or finally accept "
            "Claude's completion request. Acceptance requires no pending intent or veto."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["approve_milestone", "rework", "resume", "accept"],
                },
                "note": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["decision", "note", "evidence"],
            "additionalProperties": False,
        },
    },
    {
        "name": "conclave_read_ledger",
        "description": "Read the append-only governance ledger for traceability and dispute resolution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "after_id": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
            },
            "additionalProperties": False,
        },
    },
]


def dispatch(conclave: Conclave, name: str, args: dict[str, Any]) -> Any:
    def message_metadata() -> dict[str, Any]:
        metadata = dict(args.get("metadata") or {})
        if os.environ.get("CONCLAVE_WORKER") == "1":
            metadata["worker"] = True
            metadata["session"] = os.environ.get("CONCLAVE_WORKER_SESSION") or "unknown"
        return metadata

    calls: dict[str, Callable[[], Any]] = {
        "conclave_health": lambda: conclave.health(),
        "conclave_register_endpoint": lambda: conclave.register_endpoint(
            args["transport"], args["address"], args.get("cwd", "")
        ),
        "conclave_open_council": lambda: conclave.open_council(args["project"], args["objective"]),
        "conclave_get_state": lambda: conclave.get_state(args.get("recent_messages", 20)),
        "conclave_push": lambda: conclave.push(args["kind"], args["body"], message_metadata()),
        "conclave_send_message": lambda: conclave.send_message(
            args["recipient"], args["kind"], args["body"], message_metadata()
        ),
        "conclave_read_messages": lambda: conclave.read_messages(
            args.get("after_id", 0),
            args.get("limit", 50),
            args.get("wait_seconds", 0),
            args.get("include_own", False),
        ),
        "conclave_pull": lambda: conclave.pull(args.get("limit", 50)),
        "conclave_record_operator_message": lambda: conclave.record_operator_message(
            args["text"], args["source"], args.get("source_ref"), args.get("metadata")
        ),
        "conclave_review_operator_message": lambda: conclave.review_operator_message(
            args["message_id"], args["impact"], args["note"]
        ),
        "conclave_submit_plan": lambda: conclave.submit_plan(args["plan"]),
        "conclave_review_plan": lambda: conclave.review_plan(
            args["plan_id"], args["decision"], args["note"]
        ),
        "conclave_start_execution": lambda: conclave.start_execution(args.get("plan_id")),
        "conclave_report_event": lambda: conclave.report_event(
            args["kind"], args["summary"], args.get("details")
        ),
        "conclave_issue_veto": lambda: conclave.issue_veto(
            args["clause"], args["evidence"], args["required_correction"], args.get("severity", "blocking")
        ),
        "conclave_respond_veto": lambda: conclave.respond_veto(
            args["veto_id"], args["response"], args["evidence"]
        ),
        "conclave_resolve_veto": lambda: conclave.resolve_veto(
            args["veto_id"], args["decision"], args["note"]
        ),
        "conclave_audit": lambda: conclave.audit(args["decision"], args["note"], args["evidence"]),
        "conclave_read_ledger": lambda: conclave.read_ledger(args.get("after_id", 0), args.get("limit", 100)),
    }
    if name not in calls:
        raise ConclaveError(f"unknown tool: {name}")
    return calls[name]()


def write_message(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def serve(conclave: Conclave) -> None:
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
        except ValueError:
            continue
        request_id = request.get("id")
        method = request.get("method")
        if request_id is None:
            continue
        try:
            if method == "initialize":
                params = request.get("params") or {}
                result = {
                    "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "conclave", "version": "1.0.0"},
                    "instructions": (
                        f"Identity is bound to {conclave.actor}; council is {conclave.council}. "
                        "Claude leads execution. Codex reviews intent, architecture and evidence and may veto."
                    ),
                }
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params") or {}
                try:
                    value = dispatch(conclave, params.get("name", ""), params.get("arguments") or {})
                    if isinstance(value, dict):
                        deliveries = value.get("deliveries")
                        recipients = None
                        if (
                            params.get("name") == "conclave_register_endpoint"
                            and conclave.pending_deliveries()
                        ):
                            recipients = [conclave.actor]
                        try:
                            started = spawn_pushes(
                                conclave.db_path,
                                conclave.council,
                                deliveries if isinstance(deliveries, list) else None,
                                recipients,
                            )
                            if started:
                                value["push_started_for"] = started
                        except OSError as exc:
                            value["push_launch_error"] = str(exc)
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True),
                            }
                        ],
                        "structuredContent": value if isinstance(value, dict) else {"value": value},
                    }
                except (ConclaveError, KeyError, TypeError, ValueError) as exc:
                    result = {
                        "content": [{"type": "text", "text": f"CONCLAVE ERROR: {exc}"}],
                        "isError": True,
                    }
            elif method == "ping":
                result = {}
            else:
                write_message(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"method not found: {method}"},
                    }
                )
                continue
            write_message({"jsonrpc": "2.0", "id": request_id, "result": result})
        except Exception as exc:  # protocol boundary: never put diagnostics on stdout outside JSON-RPC
            write_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": f"internal Conclave error: {exc}"},
                }
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shared Codex/Claude architecture council MCP server")
    parser.add_argument("--actor", required=True, choices=("codex", "claude"))
    parser.add_argument("--council", required=True, help="Stable project/council key, for example council-a")
    parser.add_argument("--db", default=str(default_db_path()), help="Shared SQLite database path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    conclave = Conclave(Path(args.db), args.actor, args.council)
    if args.actor == "codex":
        thread_id = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
        if thread_id:
            conclave.register_endpoint("codex_queue", thread_id, os.getcwd())
    else:
        executable = shutil.which("claude")
        if executable:
            conclave.register_endpoint("claude_worker", executable, os.getcwd())
    if os.environ.get("CONCLAVE_WORKER") != "1" and conclave.pending_deliveries():
        spawn_pushes(conclave.db_path, conclave.council, recipients=[conclave.actor])
    serve(conclave)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

