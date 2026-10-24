"""Conclave's persistent governance model.

The MCP transport is intentionally thin.  This module owns the state machine,
actor permissions, immutable plan revisions, dual approval, vetoes, audits and
the append-only ledger.  It uses only the Python standard library so both
Codex and Claude Code can launch it without a virtual environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ACTORS = {"codex", "claude"}
PLAN_LIST_FIELDS = (
    "requirements",
    "constraints",
    "non_goals",
    "architecture",
    "tasks",
    "acceptance_criteria",
    "risks",
    "allowed_paths",
    "allowed_commands",
)
PLAN_REQUIRED_FIELDS = ("title", "objective", "user_intent", "budget", *PLAN_LIST_FIELDS)
BLOCKING_VETO_STATUSES = ("open", "answered")
NOTIFICATION_CLAIM_STALE_SECONDS = 360


class ConclaveError(RuntimeError):
    """A user/actionable protocol error, safe to return through MCP."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def default_db_path() -> Path:
    return Path.home() / ".conclave" / "conclave.db"


def _clean_text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ConclaveError(f"{field} must be a string")
    value = value.strip()
    if not value and not allow_empty:
        raise ConclaveError(f"{field} must not be empty")
    return value


def _clean_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ConclaveError(f"{field} must be an array of strings")
    result: list[str] = []
    for item in value:
        result.append(_clean_text(item, field))
    return result


def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


class Conclave:
    """One actor's view of one council, backed by a shared SQLite database."""

    def __init__(self, db_path: str | os.PathLike[str], actor: str, council: str):
        actor = actor.strip().lower()
        if actor not in ACTORS:
            raise ConclaveError(f"actor must be one of {sorted(ACTORS)}")
        council = council.strip()
        if not council:
            raise ConclaveError("council must not be empty")
        self.actor = actor
        self.council = council
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=8.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 8000")
        return conn

    def _initialize(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS councils (
                    council_key TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    objective TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'new',
                    current_plan_id INTEGER,
                    current_execution_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    sender TEXT NOT NULL,
                    reported_by TEXT,
                    recipient TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    body TEXT NOT NULL,
                    source TEXT,
                    source_ref TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS messages_source_ref_uq
                    ON messages(council_key, source_ref)
                    WHERE source_ref IS NOT NULL;
                CREATE INDEX IF NOT EXISTS messages_council_id_idx
                    ON messages(council_key, id);

                CREATE TABLE IF NOT EXISTS participant_endpoints (
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    actor TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    address TEXT NOT NULL,
                    cwd TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(council_key, actor)
                );

                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    recipient TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    push_attempted_at TEXT,
                    push_error TEXT,
                    pulled_at TEXT,
                    UNIQUE(council_key, message_id, recipient)
                );
                CREATE INDEX IF NOT EXISTS deliveries_recipient_status_idx
                    ON deliveries(council_key, recipient, status, id);

                CREATE TABLE IF NOT EXISTS intent_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    message_id INTEGER NOT NULL REFERENCES messages(id),
                    reviewer TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS intent_reviews_message_idx
                    ON intent_reviews(message_id, id);

                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    revision INTEGER NOT NULL,
                    author TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    plan_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(council_key, revision),
                    UNIQUE(council_key, plan_hash)
                );

                CREATE TABLE IF NOT EXISTS plan_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    plan_id INTEGER NOT NULL REFERENCES plans(id),
                    plan_hash TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS plan_reviews_latest_idx
                    ON plan_reviews(plan_id, reviewer, id);

                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    plan_id INTEGER NOT NULL REFERENCES plans(id),
                    lead TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resume_status TEXT,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    UNIQUE(council_key, plan_id)
                );

                CREATE TABLE IF NOT EXISTS execution_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    execution_id INTEGER NOT NULL REFERENCES executions(id),
                    actor TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vetoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    execution_id INTEGER NOT NULL REFERENCES executions(id),
                    issued_by TEXT NOT NULL,
                    clause TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    required_correction TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response TEXT,
                    response_evidence_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    released_at TEXT
                );

                CREATE TABLE IF NOT EXISTS audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    execution_id INTEGER NOT NULL REFERENCES executions(id),
                    auditor TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    council_key TEXT NOT NULL REFERENCES councils(council_key),
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ledger_council_id_idx
                    ON ledger(council_key, id);
                """
            )
            conn.execute(
                """INSERT INTO schema_meta(key, value) VALUES ('schema_version', '2')
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value"""
            )
            self._ensure_council(conn)
            conn.commit()

    @contextmanager
    def _transaction(self) -> Iterable[sqlite3.Connection]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self._ensure_council(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_council(self, conn: sqlite3.Connection) -> None:
        now = utc_now()
        conn.execute(
            """INSERT OR IGNORE INTO councils
               (council_key, project, objective, status, created_at, updated_at)
               VALUES (?, ?, '', 'new', ?, ?)""",
            (self.council, self.council, now, now),
        )

    def _touch(self, conn: sqlite3.Connection, status: str | None = None) -> None:
        if status is None:
            conn.execute(
                "UPDATE councils SET updated_at = ? WHERE council_key = ?",
                (utc_now(), self.council),
            )
        else:
            conn.execute(
                "UPDATE councils SET status = ?, updated_at = ? WHERE council_key = ?",
                (status, utc_now(), self.council),
            )

    def _log(
        self,
        conn: sqlite3.Connection,
        action: str,
        entity_type: str,
        entity_id: Any,
        payload: Any,
        *,
        actor: str | None = None,
    ) -> None:
        conn.execute(
            """INSERT INTO ledger
               (council_key, actor, action, entity_type, entity_id, payload_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                self.council,
                actor or self.actor,
                action,
                entity_type,
                None if entity_id is None else str(entity_id),
                canonical_json(payload),
                utc_now(),
            ),
        )

    def _require_actor(self, actor: str) -> None:
        if self.actor != actor:
            raise ConclaveError(f"only {actor} may perform this action; this connection is {self.actor}")

    def _council_row(self, conn: sqlite3.Connection) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM councils WHERE council_key = ?", (self.council,)
        ).fetchone()
        if row is None:
            raise ConclaveError("council does not exist")
        return row

    def _pending_intent_count(self, conn: sqlite3.Connection) -> int:
        row = conn.execute(
            """SELECT COUNT(*) AS n
               FROM messages m
               WHERE m.council_key = ? AND m.sender = 'operator'
                 AND NOT EXISTS (
                     SELECT 1 FROM intent_reviews r
                     WHERE r.message_id = m.id AND r.reviewer = 'codex'
                 )""",
            (self.council,),
        ).fetchone()
        return int(row["n"])

    def _blocking_veto_count(self, conn: sqlite3.Connection) -> int:
        row = conn.execute(
            """SELECT COUNT(*) AS n FROM vetoes
               WHERE council_key = ? AND status IN ('open', 'answered')""",
            (self.council,),
        ).fetchone()
        return int(row["n"])

    def _fanout_message(
        self, conn: sqlite3.Connection, message_id: int, recipients: Iterable[str]
    ) -> list[dict[str, Any]]:
        """Create durable push deliveries for every recipient except the pusher."""
        deliveries: list[dict[str, Any]] = []
        now = utc_now()
        for recipient in sorted(set(recipients)):
            if recipient not in ACTORS or recipient == self.actor:
                continue
            cur = conn.execute(
                """INSERT INTO deliveries
                   (council_key, message_id, recipient, status, created_at)
                   VALUES (?, ?, ?, 'pending', ?)""",
                (self.council, message_id, recipient, now),
            )
            deliveries.append(
                {
                    "delivery_id": int(cur.lastrowid),
                    "message_id": message_id,
                    "recipient": recipient,
                    "status": "pending",
                }
            )
        return deliveries

    def _current_execution(self, conn: sqlite3.Connection) -> sqlite3.Row | None:
        council = self._council_row(conn)
        if council["current_execution_id"] is None:
            return None
        return conn.execute(
            "SELECT * FROM executions WHERE id = ?", (council["current_execution_id"],)
        ).fetchone()

    def _latest_plan_reviews(self, conn: sqlite3.Connection, plan_id: int) -> dict[str, dict[str, Any]]:
        rows = conn.execute(
            """SELECT r.* FROM plan_reviews r
               JOIN (
                   SELECT reviewer, MAX(id) AS max_id
                   FROM plan_reviews WHERE plan_id = ? GROUP BY reviewer
               ) latest ON latest.max_id = r.id
               ORDER BY r.reviewer""",
            (plan_id,),
        ).fetchall()
        return {row["reviewer"]: _dict(row) or {} for row in rows}

    def open_council(self, project: str, objective: str) -> dict[str, Any]:
        project = _clean_text(project, "project")
        objective = _clean_text(objective, "objective")
        with self._transaction() as conn:
            old = self._council_row(conn)
            old_objective = old["objective"]
            conn.execute(
                """UPDATE councils SET project = ?, objective = ?, updated_at = ?
                   WHERE council_key = ?""",
                (project, objective, utc_now(), self.council),
            )
            self._log(
                conn,
                "council_opened" if not old_objective else "council_reopened",
                "council",
                self.council,
                {"project": project, "objective": objective},
            )
        return self.get_state(recent_messages=10)

    def health(self) -> dict[str, Any]:
        with closing(self._connect()) as conn:
            version = conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).fetchone()
            exists = conn.execute(
                "SELECT 1 FROM councils WHERE council_key = ?", (self.council,)
            ).fetchone()
        return {
            "ok": True,
            "actor": self.actor,
            "council": self.council,
            "database": str(self.db_path),
            "schema_version": version["value"] if version else None,
            "council_exists": bool(exists),
        }

    def register_endpoint(self, transport: str, address: str, cwd: str = "") -> dict[str, Any]:
        """Register how this actor can receive an immediate push notification."""
        transport = _clean_text(transport, "transport").lower()
        if transport not in {"codex_queue", "claude_worker"}:
            raise ConclaveError("unsupported push transport")
        address = _clean_text(address, "address")
        cwd = str(cwd or "").strip()
        with self._transaction() as conn:
            existing = conn.execute(
                """SELECT transport, address, cwd FROM participant_endpoints
                   WHERE council_key = ? AND actor = ?""",
                (self.council, self.actor),
            ).fetchone()
            conn.execute(
                """INSERT INTO participant_endpoints
                   (council_key, actor, transport, address, cwd, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(council_key, actor) DO UPDATE SET
                       transport = excluded.transport,
                       address = excluded.address,
                       cwd = excluded.cwd,
                       updated_at = excluded.updated_at""",
                (self.council, self.actor, transport, address, cwd, utc_now()),
            )
            changed = existing is None or any(
                existing[key] != value
                for key, value in (("transport", transport), ("address", address), ("cwd", cwd))
            )
            if changed:
                self._log(
                    conn,
                    "participant_endpoint_registered",
                    "participant",
                    self.actor,
                    {"transport": transport, "address": address, "cwd": cwd},
                )
        return {
            "actor": self.actor,
            "transport": transport,
            "address": address,
            "cwd": cwd,
            "changed": changed,
        }

    def get_endpoint(self, actor: str | None = None) -> dict[str, Any] | None:
        actor = (actor or self.actor).strip().lower()
        if actor not in ACTORS:
            raise ConclaveError(f"actor must be one of {sorted(ACTORS)}")
        with closing(self._connect()) as conn:
            row = conn.execute(
                """SELECT * FROM participant_endpoints
                   WHERE council_key = ? AND actor = ?""",
                (self.council, actor),
            ).fetchone()
        return _dict(row)

    def send_message(
        self,
        recipient: str,
        kind: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recipient = recipient.strip().lower()
        if recipient == "other":
            recipient = "claude" if self.actor == "codex" else "codex"
        if recipient not in {"codex", "claude", "all"}:
            raise ConclaveError("recipient must be codex, claude, other, or all")
        kind = _clean_text(kind, "kind")
        body = _clean_text(body, "body")
        metadata = metadata or {}
        if not isinstance(metadata, dict):
            raise ConclaveError("metadata must be an object")
        with self._transaction() as conn:
            cur = conn.execute(
                """INSERT INTO messages
                   (council_key, sender, reported_by, recipient, kind, body, metadata_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.council,
                    self.actor,
                    self.actor,
                    recipient,
                    kind,
                    body,
                    canonical_json(metadata),
                    utc_now(),
                ),
            )
            message_id = int(cur.lastrowid)
            self._log(
                conn,
                "message_sent",
                "message",
                message_id,
                {"recipient": recipient, "kind": kind},
            )
            targets = ACTORS if recipient == "all" else {recipient}
            deliveries = self._fanout_message(conn, message_id, targets)
            self._touch(conn)
        return {
            "message_id": message_id,
            "recipient": recipient,
            "kind": kind,
            "deliveries": deliveries,
        }

    def push(
        self,
        kind: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Push a durable message to every participant except this actor."""
        return self.send_message("all", kind, body, metadata)

    def record_operator_message(
        self,
        text: str,
        source: str,
        source_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = _clean_text(text, "text")
        source = _clean_text(source, "source")
        if source_ref is not None:
            source_ref = _clean_text(source_ref, "source_ref")
        metadata = metadata or {}
        if not isinstance(metadata, dict):
            raise ConclaveError("metadata must be an object")
        with self._transaction() as conn:
            if source_ref:
                existing = conn.execute(
                    """SELECT id, created_at FROM messages
                       WHERE council_key = ? AND source_ref = ?""",
                    (self.council, source_ref),
                ).fetchone()
                if existing:
                    return {
                        "message_id": existing["id"],
                        "duplicate": True,
                        "intent_review_pending": self._pending_intent_count(conn),
                    }
            cur = conn.execute(
                """INSERT INTO messages
                   (council_key, sender, reported_by, recipient, kind, body, source, source_ref,
                    metadata_json, created_at)
                   VALUES (?, 'operator', ?, 'all', 'operator_instruction', ?, ?, ?, ?, ?)""",
                (
                    self.council,
                    self.actor,
                    text,
                    source,
                    source_ref,
                    canonical_json(metadata),
                    utc_now(),
                ),
            )
            message_id = int(cur.lastrowid)
            execution = self._current_execution(conn)
            if execution and execution["status"] in {"running", "rework", "audit"}:
                conn.execute(
                    """UPDATE executions SET resume_status = ?, status = 'paused_intent', updated_at = ?
                       WHERE id = ?""",
                    (execution["status"], utc_now(), execution["id"]),
                )
            self._touch(conn, "intent_review")
            self._log(
                conn,
                "operator_message_recorded",
                "message",
                message_id,
                {"source": source, "source_ref": source_ref, "reported_by": self.actor},
            )
            deliveries = self._fanout_message(conn, message_id, ACTORS)
            pending = self._pending_intent_count(conn)
        return {
            "message_id": message_id,
            "duplicate": False,
            "intent_review_pending": pending,
            "execution_paused": bool(execution),
            "deliveries": deliveries,
        }

    def review_operator_message(self, message_id: int, impact: str, note: str) -> dict[str, Any]:
        self._require_actor("codex")
        impact = impact.strip().lower()
        if impact not in {"no_change", "clarifies", "changes_scope", "conflicts"}:
            raise ConclaveError("impact must be no_change, clarifies, changes_scope, or conflicts")
        note = _clean_text(note, "note")
        with self._transaction() as conn:
            message = conn.execute(
                """SELECT * FROM messages
                   WHERE id = ? AND council_key = ? AND sender = 'operator'""",
                (message_id, self.council),
            ).fetchone()
            if message is None:
                raise ConclaveError("operator message not found in this council")
            cur = conn.execute(
                """INSERT INTO intent_reviews
                   (council_key, message_id, reviewer, impact, note, created_at)
                   VALUES (?, ?, 'codex', ?, ?, ?)""",
                (self.council, message_id, impact, note, utc_now()),
            )
            review_id = int(cur.lastrowid)
            if impact in {"changes_scope", "conflicts"}:
                council = self._council_row(conn)
                if council["current_plan_id"] is not None:
                    conn.execute(
                        "UPDATE plans SET status = 'stale' WHERE id = ?",
                        (council["current_plan_id"],),
                    )
                execution = self._current_execution(conn)
                if execution and execution["status"] != "completed":
                    conn.execute(
                        """UPDATE executions SET status = 'paused_scope', updated_at = ?
                           WHERE id = ?""",
                        (utc_now(), execution["id"]),
                    )
                self._touch(conn, "deliberation")
            else:
                pending_after = self._pending_intent_count(conn)
                execution = self._current_execution(conn)
                if pending_after == 0 and execution and execution["status"] == "paused_intent":
                    resume = execution["resume_status"] or "running"
                    conn.execute(
                        """UPDATE executions SET status = ?, resume_status = NULL, updated_at = ?
                           WHERE id = ?""",
                        (resume, utc_now(), execution["id"]),
                    )
                    self._touch(conn, "audit" if resume == "audit" else "executing")
                elif pending_after == 0 and not execution:
                    council = self._council_row(conn)
                    status = "deliberation" if council["current_plan_id"] else "new"
                    self._touch(conn, status)
            self._log(
                conn,
                "operator_message_reviewed",
                "intent_review",
                review_id,
                {"message_id": message_id, "impact": impact, "note": note},
            )
            pending = self._pending_intent_count(conn)
        return {"review_id": review_id, "message_id": message_id, "impact": impact, "pending": pending}

    def _validate_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(plan, dict):
            raise ConclaveError("plan must be an object")
        missing = [field for field in PLAN_REQUIRED_FIELDS if field not in plan]
        if missing:
            raise ConclaveError("plan is missing required fields: " + ", ".join(missing))
        cleaned = dict(plan)
        for field in ("title", "objective", "user_intent", "budget"):
            cleaned[field] = _clean_text(plan[field], field)
        for field in PLAN_LIST_FIELDS:
            cleaned[field] = _clean_string_list(plan[field], field)
        if "change_summary" in cleaned:
            cleaned["change_summary"] = _clean_text(
                cleaned["change_summary"], "change_summary", allow_empty=True
            )
        return cleaned

    def submit_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        plan = self._validate_plan(plan)
        plan_hash = json_hash(plan)
        with self._transaction() as conn:
            duplicate = conn.execute(
                """SELECT * FROM plans WHERE council_key = ? AND plan_hash = ?""",
                (self.council, plan_hash),
            ).fetchone()
            if duplicate:
                return {
                    "plan_id": duplicate["id"],
                    "revision": duplicate["revision"],
                    "plan_hash": plan_hash,
                    "status": duplicate["status"],
                    "duplicate": True,
                }
            revision_row = conn.execute(
                "SELECT COALESCE(MAX(revision), 0) + 1 AS revision FROM plans WHERE council_key = ?",
                (self.council,),
            ).fetchone()
            revision = int(revision_row["revision"])
            council = self._council_row(conn)
            if council["current_plan_id"] is not None:
                conn.execute(
                    """UPDATE plans SET status = CASE
                           WHEN status = 'consensus' THEN 'stale' ELSE 'superseded' END
                       WHERE id = ?""",
                    (council["current_plan_id"],),
                )
            cur = conn.execute(
                """INSERT INTO plans
                   (council_key, revision, author, title, payload_json, plan_hash, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'deliberation', ?)""",
                (
                    self.council,
                    revision,
                    self.actor,
                    plan["title"],
                    canonical_json(plan),
                    plan_hash,
                    utc_now(),
                ),
            )
            plan_id = int(cur.lastrowid)
            execution = self._current_execution(conn)
            if execution and execution["status"] != "completed":
                conn.execute(
                    """UPDATE executions SET resume_status = status, status = 'paused_change', updated_at = ?
                       WHERE id = ?""",
                    (utc_now(), execution["id"]),
                )
            conn.execute(
                """UPDATE councils SET current_plan_id = ?, status = 'deliberation', updated_at = ?
                   WHERE council_key = ?""",
                (plan_id, utc_now(), self.council),
            )
            self._log(
                conn,
                "plan_submitted",
                "plan",
                plan_id,
                {"revision": revision, "plan_hash": plan_hash, "title": plan["title"]},
            )
        return {
            "plan_id": plan_id,
            "revision": revision,
            "plan_hash": plan_hash,
            "status": "deliberation",
            "duplicate": False,
            "next": "Both Claude and Codex must approve this exact plan hash.",
        }

    def review_plan(self, plan_id: int, decision: str, note: str) -> dict[str, Any]:
        decision = decision.strip().lower()
        if decision not in {"approve", "request_changes", "veto"}:
            raise ConclaveError("decision must be approve, request_changes, or veto")
        note = _clean_text(note, "note")
        with self._transaction() as conn:
            council = self._council_row(conn)
            plan = conn.execute(
                "SELECT * FROM plans WHERE id = ? AND council_key = ?", (plan_id, self.council)
            ).fetchone()
            if plan is None:
                raise ConclaveError("plan not found in this council")
            if council["current_plan_id"] != plan_id:
                raise ConclaveError("only the current plan revision may be reviewed")
            if plan["status"] in {"stale", "superseded"}:
                raise ConclaveError(f"plan is {plan['status']}; submit a new revision")
            if decision == "approve" and self._pending_intent_count(conn):
                raise ConclaveError("operator messages still need Codex intent review")
            cur = conn.execute(
                """INSERT INTO plan_reviews
                   (council_key, plan_id, plan_hash, reviewer, decision, note, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.council, plan_id, plan["plan_hash"], self.actor, decision, note, utc_now()),
            )
            review_id = int(cur.lastrowid)
            reviews = self._latest_plan_reviews(conn, plan_id)
            consensus = all(
                actor in reviews and reviews[actor]["decision"] == "approve" for actor in ACTORS
            )
            if decision in {"request_changes", "veto"}:
                conn.execute("UPDATE plans SET status = 'deliberation' WHERE id = ?", (plan_id,))
                self._touch(conn, "deliberation")
            elif consensus:
                if self._blocking_veto_count(conn):
                    raise ConclaveError("an execution veto is still open")
                conn.execute("UPDATE plans SET status = 'consensus' WHERE id = ?", (plan_id,))
                self._touch(conn, "consensus_locked")
            self._log(
                conn,
                "plan_reviewed",
                "plan_review",
                review_id,
                {
                    "plan_id": plan_id,
                    "plan_hash": plan["plan_hash"],
                    "decision": decision,
                    "note": note,
                    "consensus": consensus,
                },
            )
        return {
            "review_id": review_id,
            "plan_id": plan_id,
            "plan_hash": plan["plan_hash"],
            "decision": decision,
            "consensus": consensus,
            "latest_reviews": reviews,
            "next": "Claude may start execution." if consensus else "Continue deliberation or submit a revision.",
        }

    def start_execution(self, plan_id: int | None = None) -> dict[str, Any]:
        self._require_actor("claude")
        with self._transaction() as conn:
            council = self._council_row(conn)
            plan_id = int(plan_id or council["current_plan_id"] or 0)
            plan = conn.execute(
                "SELECT * FROM plans WHERE id = ? AND council_key = ?", (plan_id, self.council)
            ).fetchone()
            if plan is None or council["current_plan_id"] != plan_id:
                raise ConclaveError("current plan not found")
            if plan["status"] != "consensus":
                raise ConclaveError("execution requires dual approval of the current plan")
            if self._pending_intent_count(conn):
                raise ConclaveError("operator messages still need Codex intent review")
            if self._blocking_veto_count(conn):
                raise ConclaveError("a Codex veto is still open")
            existing = conn.execute(
                "SELECT * FROM executions WHERE council_key = ? AND plan_id = ?",
                (self.council, plan_id),
            ).fetchone()
            now = utc_now()
            if existing:
                if existing["status"] == "completed":
                    raise ConclaveError("this execution is already completed")
                if existing["status"] not in {"paused_blocked", "paused_scope"}:
                    return {
                        "execution_id": existing["id"],
                        "status": existing["status"],
                        "duplicate": True,
                    }
                raise ConclaveError("Codex must audit with decision=resume before this execution resumes")
            cur = conn.execute(
                """INSERT INTO executions
                   (council_key, plan_id, lead, status, started_at, updated_at)
                   VALUES (?, ?, 'claude', 'running', ?, ?)""",
                (self.council, plan_id, now, now),
            )
            execution_id = int(cur.lastrowid)
            conn.execute(
                """UPDATE councils SET current_execution_id = ?, status = 'executing', updated_at = ?
                   WHERE council_key = ?""",
                (execution_id, now, self.council),
            )
            self._log(
                conn,
                "execution_started",
                "execution",
                execution_id,
                {"plan_id": plan_id, "plan_hash": plan["plan_hash"], "lead": "claude"},
            )
        return {
            "execution_id": execution_id,
            "plan_id": plan_id,
            "plan_hash": plan["plan_hash"],
            "status": "running",
            "lead": "claude",
        }

    def report_event(self, kind: str, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_actor("claude")
        kind = kind.strip().lower()
        allowed = {
            "agent_spawned",
            "progress",
            "decision",
            "test_result",
            "risk",
            "blocked",
            "scope_change_requested",
            "completion_requested",
        }
        if kind not in allowed:
            raise ConclaveError("unsupported event kind: " + kind)
        summary = _clean_text(summary, "summary")
        details = details or {}
        if not isinstance(details, dict):
            raise ConclaveError("details must be an object")
        with self._transaction() as conn:
            execution = self._current_execution(conn)
            if execution is None:
                raise ConclaveError("there is no current execution")
            if execution["status"] == "completed":
                raise ConclaveError("execution is already completed")
            if kind in {"agent_spawned", "progress", "decision", "test_result"} and execution[
                "status"
            ] not in {"running", "rework"}:
                raise ConclaveError(f"cannot report {kind} while execution is {execution['status']}")
            cur = conn.execute(
                """INSERT INTO execution_events
                   (council_key, execution_id, actor, kind, summary, details_json, created_at)
                   VALUES (?, ?, 'claude', ?, ?, ?, ?)""",
                (
                    self.council,
                    execution["id"],
                    kind,
                    summary,
                    canonical_json(details),
                    utc_now(),
                ),
            )
            event_id = int(cur.lastrowid)
            new_status = execution["status"]
            council_status = self._council_row(conn)["status"]
            if kind == "completion_requested":
                if execution["status"] not in {"running", "rework"}:
                    raise ConclaveError("completion may be requested only while work is active")
                new_status, council_status = "audit", "audit"
            elif kind == "blocked":
                new_status, council_status = "paused_blocked", "paused"
            elif kind == "scope_change_requested":
                new_status, council_status = "paused_scope", "deliberation"
            if new_status != execution["status"]:
                conn.execute(
                    "UPDATE executions SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, utc_now(), execution["id"]),
                )
                self._touch(conn, council_status)
            else:
                conn.execute(
                    "UPDATE executions SET updated_at = ? WHERE id = ?", (utc_now(), execution["id"])
                )
                self._touch(conn)
            self._log(
                conn,
                "execution_event",
                "execution_event",
                event_id,
                {"execution_id": execution["id"], "kind": kind, "summary": summary},
            )
        return {"event_id": event_id, "execution_id": execution["id"], "status": new_status}

    def issue_veto(
        self,
        clause: str,
        evidence: str,
        required_correction: str,
        severity: str = "blocking",
    ) -> dict[str, Any]:
        self._require_actor("codex")
        clause = _clean_text(clause, "clause")
        evidence = _clean_text(evidence, "evidence")
        required_correction = _clean_text(required_correction, "required_correction")
        severity = severity.strip().lower()
        if severity not in {"blocking", "critical"}:
            raise ConclaveError("severity must be blocking or critical")
        with self._transaction() as conn:
            execution = self._current_execution(conn)
            if execution is None or execution["status"] == "completed":
                raise ConclaveError("a veto requires an active execution")
            now = utc_now()
            cur = conn.execute(
                """INSERT INTO vetoes
                   (council_key, execution_id, issued_by, clause, evidence, required_correction,
                    severity, status, created_at, updated_at)
                   VALUES (?, ?, 'codex', ?, ?, ?, ?, 'open', ?, ?)""",
                (
                    self.council,
                    execution["id"],
                    clause,
                    evidence,
                    required_correction,
                    severity,
                    now,
                    now,
                ),
            )
            veto_id = int(cur.lastrowid)
            resume = execution["status"] if not execution["status"].startswith("paused") else execution[
                "resume_status"
            ]
            conn.execute(
                """UPDATE executions SET status = 'paused_veto', resume_status = ?, updated_at = ?
                   WHERE id = ?""",
                (resume or "running", now, execution["id"]),
            )
            self._touch(conn, "paused")
            self._log(
                conn,
                "veto_issued",
                "veto",
                veto_id,
                {
                    "execution_id": execution["id"],
                    "clause": clause,
                    "evidence": evidence,
                    "required_correction": required_correction,
                    "severity": severity,
                },
            )
        return {
            "veto_id": veto_id,
            "execution_id": execution["id"],
            "status": "open",
            "execution_status": "paused_veto",
        }

    def respond_veto(self, veto_id: int, response: str, evidence: list[str]) -> dict[str, Any]:
        self._require_actor("claude")
        response = _clean_text(response, "response")
        evidence = _clean_string_list(evidence, "evidence")
        with self._transaction() as conn:
            veto = conn.execute(
                "SELECT * FROM vetoes WHERE id = ? AND council_key = ?", (veto_id, self.council)
            ).fetchone()
            if veto is None:
                raise ConclaveError("veto not found")
            if veto["status"] not in {"open", "answered"}:
                raise ConclaveError(f"veto is {veto['status']}")
            conn.execute(
                """UPDATE vetoes SET status = 'answered', response = ?, response_evidence_json = ?,
                   updated_at = ? WHERE id = ?""",
                (response, canonical_json(evidence), utc_now(), veto_id),
            )
            self._log(
                conn,
                "veto_answered",
                "veto",
                veto_id,
                {"response": response, "evidence": evidence},
            )
            self._touch(conn)
        return {"veto_id": veto_id, "status": "answered", "next": "Codex must release or maintain it."}

    def resolve_veto(self, veto_id: int, decision: str, note: str) -> dict[str, Any]:
        self._require_actor("codex")
        decision = decision.strip().lower()
        if decision not in {"release", "maintain"}:
            raise ConclaveError("decision must be release or maintain")
        note = _clean_text(note, "note")
        with self._transaction() as conn:
            veto = conn.execute(
                "SELECT * FROM vetoes WHERE id = ? AND council_key = ?", (veto_id, self.council)
            ).fetchone()
            if veto is None:
                raise ConclaveError("veto not found")
            if veto["status"] not in {"open", "answered"}:
                raise ConclaveError(f"veto is already {veto['status']}")
            if decision == "release":
                conn.execute(
                    """UPDATE vetoes SET status = 'released', updated_at = ?, released_at = ?
                       WHERE id = ?""",
                    (utc_now(), utc_now(), veto_id),
                )
            else:
                conn.execute(
                    "UPDATE vetoes SET status = 'open', updated_at = ? WHERE id = ?",
                    (utc_now(), veto_id),
                )
            execution = conn.execute(
                "SELECT * FROM executions WHERE id = ?", (veto["execution_id"],)
            ).fetchone()
            if (
                decision == "release"
                and execution
                and self._blocking_veto_count(conn) == 0
                and self._pending_intent_count(conn) == 0
            ):
                resume = execution["resume_status"] or "running"
                conn.execute(
                    """UPDATE executions SET status = ?, resume_status = NULL, updated_at = ?
                       WHERE id = ?""",
                    (resume, utc_now(), execution["id"]),
                )
                self._touch(conn, "audit" if resume == "audit" else "executing")
            self._log(
                conn,
                "veto_resolved",
                "veto",
                veto_id,
                {"decision": decision, "note": note},
            )
        return {
            "veto_id": veto_id,
            "status": "released" if decision == "release" else "open",
            "decision": decision,
        }

    def audit(self, decision: str, note: str, evidence: list[str]) -> dict[str, Any]:
        self._require_actor("codex")
        decision = decision.strip().lower()
        if decision not in {"approve_milestone", "rework", "resume", "accept"}:
            raise ConclaveError("decision must be approve_milestone, rework, resume, or accept")
        note = _clean_text(note, "note")
        evidence = _clean_string_list(evidence, "evidence")
        with self._transaction() as conn:
            execution = self._current_execution(conn)
            if execution is None:
                raise ConclaveError("there is no current execution")
            if self._pending_intent_count(conn):
                raise ConclaveError("operator messages still need Codex intent review")
            if self._blocking_veto_count(conn):
                raise ConclaveError("a veto is still open")
            now = utc_now()
            if decision == "accept":
                if execution["status"] != "audit":
                    raise ConclaveError("Claude must request completion before final acceptance")
                new_status, council_status = "completed", "accepted"
                conn.execute(
                    """UPDATE executions SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?""",
                    (new_status, now, now, execution["id"]),
                )
            elif decision == "rework":
                if execution["status"] not in {"audit", "running", "rework"}:
                    raise ConclaveError(f"cannot request rework while execution is {execution['status']}")
                new_status, council_status = "rework", "executing"
                conn.execute(
                    "UPDATE executions SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, now, execution["id"]),
                )
            elif decision == "resume":
                if execution["status"] not in {"paused_blocked", "paused_scope"}:
                    raise ConclaveError(f"resume is not valid while execution is {execution['status']}")
                new_status, council_status = "running", "executing"
                conn.execute(
                    "UPDATE executions SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, now, execution["id"]),
                )
            else:
                new_status = execution["status"]
                council_status = self._council_row(conn)["status"]
            cur = conn.execute(
                """INSERT INTO audits
                   (council_key, execution_id, auditor, decision, note, evidence_json, created_at)
                   VALUES (?, ?, 'codex', ?, ?, ?, ?)""",
                (
                    self.council,
                    execution["id"],
                    decision,
                    note,
                    canonical_json(evidence),
                    now,
                ),
            )
            audit_id = int(cur.lastrowid)
            self._touch(conn, council_status)
            self._log(
                conn,
                "execution_audited",
                "audit",
                audit_id,
                {"execution_id": execution["id"], "decision": decision, "note": note, "evidence": evidence},
            )
        return {
            "audit_id": audit_id,
            "execution_id": execution["id"],
            "decision": decision,
            "execution_status": new_status,
            "council_status": council_status,
        }

    def read_messages(
        self,
        after_id: int = 0,
        limit: int = 50,
        wait_seconds: float = 0,
        include_own: bool = False,
    ) -> dict[str, Any]:
        after_id = max(0, int(after_id))
        limit = max(1, min(200, int(limit)))
        wait_seconds = max(0.0, min(30.0, float(wait_seconds)))
        deadline = time.monotonic() + wait_seconds
        rows: list[sqlite3.Row] = []
        while True:
            with closing(self._connect()) as conn:
                rows = conn.execute(
                    """SELECT * FROM messages
                       WHERE council_key = ? AND id > ?
                         AND recipient IN (?, 'all')
                         AND (? = 1 OR sender != ?)
                       ORDER BY id LIMIT ?""",
                    (self.council, after_id, self.actor, int(include_own), self.actor, limit),
                ).fetchall()
            if rows or time.monotonic() >= deadline:
                break
            time.sleep(0.2)
        messages = []
        for row in rows:
            item = _dict(row) or {}
            item["metadata"] = json.loads(item.pop("metadata_json"))
            messages.append(item)
        pulled_delivery_ids: list[int] = []
        if messages:
            message_ids = [int(message["id"]) for message in messages]
            placeholders = ",".join("?" for _ in message_ids)
            with self._transaction() as conn:
                delivery_rows = conn.execute(
                    f"""SELECT id FROM deliveries
                        WHERE council_key = ? AND recipient = ?
                          AND message_id IN ({placeholders}) AND status != 'pulled'""",
                    (self.council, self.actor, *message_ids),
                ).fetchall()
                pulled_delivery_ids = [int(row["id"]) for row in delivery_rows]
                if pulled_delivery_ids:
                    delivery_placeholders = ",".join("?" for _ in pulled_delivery_ids)
                    conn.execute(
                        f"""UPDATE deliveries SET status = 'pulled', pulled_at = ?
                            WHERE id IN ({delivery_placeholders})""",
                        (utc_now(), *pulled_delivery_ids),
                    )
        return {
            "messages": messages,
            "last_id": messages[-1]["id"] if messages else after_id,
            "timed_out": not bool(messages) and wait_seconds > 0,
            "pulled_delivery_ids": pulled_delivery_ids,
        }

    def pull(self, limit: int = 50) -> dict[str, Any]:
        """Pull this participant's durable inbox and acknowledge only returned deliveries."""
        limit = max(1, min(200, int(limit)))
        with self._transaction() as conn:
            rows = conn.execute(
                """SELECT d.id AS delivery_id, d.status AS delivery_status, m.*
                   FROM deliveries d
                   JOIN messages m ON m.id = d.message_id
                   WHERE d.council_key = ? AND d.recipient = ? AND d.status != 'pulled'
                   ORDER BY d.id LIMIT ?""",
                (self.council, self.actor, limit),
            ).fetchall()
            delivery_ids = [int(row["delivery_id"]) for row in rows]
            if delivery_ids:
                placeholders = ",".join("?" for _ in delivery_ids)
                conn.execute(
                    f"""UPDATE deliveries SET status = 'pulled', pulled_at = ?
                        WHERE id IN ({placeholders})""",
                    (utc_now(), *delivery_ids),
                )
            remaining_row = conn.execute(
                """SELECT COUNT(*) AS n FROM deliveries
                   WHERE council_key = ? AND recipient = ? AND status != 'pulled'""",
                (self.council, self.actor),
            ).fetchone()
        messages: list[dict[str, Any]] = []
        for row in rows:
            item = _dict(row) or {}
            item["metadata"] = json.loads(item.pop("metadata_json"))
            item["delivery_id"] = int(item["delivery_id"])
            item["delivery_status"] = "pulled"
            messages.append(item)
        return {
            "actor": self.actor,
            "messages": messages,
            "pulled": len(delivery_ids),
            "remaining": int(remaining_row["n"]),
        }

    def pending_deliveries(self, recipient: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        recipient = (recipient or self.actor).strip().lower()
        if recipient not in ACTORS:
            raise ConclaveError(f"recipient must be one of {sorted(ACTORS)}")
        limit = max(1, min(500, int(limit)))
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """SELECT d.*, m.sender, m.recipient AS message_recipient, m.kind, m.body
                   FROM deliveries d JOIN messages m ON m.id = d.message_id
                   WHERE d.council_key = ? AND d.recipient = ?
                     AND d.status IN ('pending', 'push_failed')
                   ORDER BY d.id LIMIT ?""",
                (self.council, recipient, limit),
            ).fetchall()
        return [_dict(row) or {} for row in rows]

    def claim_deliveries(self, limit: int = 100) -> list[dict[str, Any]]:
        """Atomically claim this participant's notifications for one push worker."""
        limit = max(1, min(500, int(limit)))
        with self._transaction() as conn:
            # A worker can be terminated between claiming a delivery and recording
            # its result. Recover those claims instead of orphaning the inbox.
            stale_before = (
                datetime.now(timezone.utc) - timedelta(seconds=NOTIFICATION_CLAIM_STALE_SECONDS)
            ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            conn.execute(
                """UPDATE deliveries
                   SET status = 'push_failed', push_error = 'stale notification claim recovered'
                   WHERE council_key = ? AND recipient = ? AND status = 'notifying'
                     AND push_attempted_at < ?""",
                (self.council, self.actor, stale_before),
            )
            rows = conn.execute(
                """SELECT d.*, m.sender, m.recipient AS message_recipient, m.kind, m.body
                   FROM deliveries d JOIN messages m ON m.id = d.message_id
                   WHERE d.council_key = ? AND d.recipient = ?
                     AND d.status IN ('pending', 'push_failed')
                   ORDER BY d.id LIMIT ?""",
                (self.council, self.actor, limit),
            ).fetchall()
            delivery_ids = [int(row["id"]) for row in rows]
            if delivery_ids:
                placeholders = ",".join("?" for _ in delivery_ids)
                conn.execute(
                    f"""UPDATE deliveries SET status = 'notifying', push_attempted_at = ?, push_error = NULL
                        WHERE id IN ({placeholders})""",
                    (utc_now(), *delivery_ids),
                )
        return [_dict(row) or {} for row in rows]

    def deliveries_pulled(self, delivery_ids: Iterable[int]) -> bool:
        ids = [int(delivery_id) for delivery_id in delivery_ids]
        if not ids:
            return True
        placeholders = ",".join("?" for _ in ids)
        with closing(self._connect()) as conn:
            row = conn.execute(
                f"""SELECT COUNT(*) AS n FROM deliveries
                    WHERE council_key = ? AND recipient = ?
                      AND id IN ({placeholders}) AND status != 'pulled'""",
                (self.council, self.actor, *ids),
            ).fetchone()
        return int(row["n"]) == 0

    def mark_delivery_push(self, delivery_id: int, error: str | None = None) -> dict[str, Any]:
        with self._transaction() as conn:
            delivery = conn.execute(
                """SELECT * FROM deliveries
                   WHERE id = ? AND council_key = ? AND recipient = ?""",
                (int(delivery_id), self.council, self.actor),
            ).fetchone()
            if delivery is None:
                raise ConclaveError("delivery not found for this participant")
            if delivery["status"] == "pulled":
                return {"delivery_id": int(delivery_id), "status": "pulled", "error": None}
            status = "push_failed" if error else "pushed"
            conn.execute(
                """UPDATE deliveries
                   SET status = ?, push_attempted_at = ?, push_error = ? WHERE id = ?""",
                (status, utc_now(), str(error) if error else None, int(delivery_id)),
            )
            self._log(
                conn,
                "delivery_push_failed" if error else "delivery_pushed",
                "delivery",
                delivery_id,
                {"message_id": delivery["message_id"], "recipient": self.actor, "error": error},
            )
        return {"delivery_id": int(delivery_id), "status": status, "error": error}

    def read_ledger(self, after_id: int = 0, limit: int = 100) -> dict[str, Any]:
        after_id = max(0, int(after_id))
        limit = max(1, min(500, int(limit)))
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """SELECT * FROM ledger WHERE council_key = ? AND id > ? ORDER BY id LIMIT ?""",
                (self.council, after_id, limit),
            ).fetchall()
        entries = []
        for row in rows:
            item = _dict(row) or {}
            item["payload"] = json.loads(item.pop("payload_json"))
            entries.append(item)
        return {"entries": entries, "last_id": entries[-1]["id"] if entries else after_id}

    def get_state(self, recent_messages: int = 20) -> dict[str, Any]:
        recent_messages = max(0, min(100, int(recent_messages)))
        with closing(self._connect()) as conn:
            council = self._council_row(conn)
            plan = None
            reviews: dict[str, Any] = {}
            if council["current_plan_id"] is not None:
                plan_row = conn.execute(
                    "SELECT * FROM plans WHERE id = ?", (council["current_plan_id"],)
                ).fetchone()
                if plan_row:
                    plan = _dict(plan_row)
                    plan["payload"] = json.loads(plan.pop("payload_json"))
                    reviews = self._latest_plan_reviews(conn, plan_row["id"])
            execution_row = self._current_execution(conn)
            execution = _dict(execution_row)
            events: list[dict[str, Any]] = []
            audits: list[dict[str, Any]] = []
            if execution_row:
                event_rows = conn.execute(
                    """SELECT * FROM execution_events WHERE execution_id = ? ORDER BY id DESC LIMIT 20""",
                    (execution_row["id"],),
                ).fetchall()
                for row in reversed(event_rows):
                    item = _dict(row) or {}
                    item["details"] = json.loads(item.pop("details_json"))
                    events.append(item)
                audit_rows = conn.execute(
                    "SELECT * FROM audits WHERE execution_id = ? ORDER BY id",
                    (execution_row["id"],),
                ).fetchall()
                for row in audit_rows:
                    item = _dict(row) or {}
                    item["evidence"] = json.loads(item.pop("evidence_json"))
                    audits.append(item)
            veto_rows = conn.execute(
                """SELECT * FROM vetoes WHERE council_key = ? AND status IN ('open', 'answered')
                   ORDER BY id""",
                (self.council,),
            ).fetchall()
            vetoes = []
            for row in veto_rows:
                item = _dict(row) or {}
                raw = item.pop("response_evidence_json")
                item["response_evidence"] = json.loads(raw) if raw else []
                vetoes.append(item)
            pending_rows = conn.execute(
                """SELECT m.* FROM messages m
                   WHERE m.council_key = ? AND m.sender = 'operator'
                     AND NOT EXISTS (
                         SELECT 1 FROM intent_reviews r
                         WHERE r.message_id = m.id AND r.reviewer = 'codex'
                     )
                   ORDER BY m.id""",
                (self.council,),
            ).fetchall()
            pending = []
            for row in pending_rows:
                item = _dict(row) or {}
                item["metadata"] = json.loads(item.pop("metadata_json"))
                pending.append(item)
            message_rows = []
            if recent_messages:
                message_rows = conn.execute(
                    """SELECT * FROM messages WHERE council_key = ? ORDER BY id DESC LIMIT ?""",
                    (self.council, recent_messages),
                ).fetchall()
            messages = []
            for row in reversed(message_rows):
                item = _dict(row) or {}
                item["metadata"] = json.loads(item.pop("metadata_json"))
                messages.append(item)
            delivery_rows = conn.execute(
                """SELECT * FROM deliveries
                   WHERE council_key = ? AND recipient = ? AND status != 'pulled'
                   ORDER BY id""",
                (self.council, self.actor),
            ).fetchall()
            inbox = [_dict(row) or {} for row in delivery_rows]
            endpoint_rows = conn.execute(
                """SELECT * FROM participant_endpoints
                   WHERE council_key = ? ORDER BY actor""",
                (self.council,),
            ).fetchall()
            endpoints = [_dict(row) or {} for row in endpoint_rows]
        return {
            "actor": self.actor,
            "council": _dict(council),
            "current_plan": plan,
            "latest_plan_reviews": reviews,
            "current_execution": execution,
            "recent_events": events,
            "active_vetoes": vetoes,
            "pending_operator_messages": pending,
            "audits": audits,
            "recent_messages": messages,
            "inbox": inbox,
            "participant_endpoints": endpoints,
        }

    def gate_decision(
        self, tool_name: str, tool_input: dict[str, Any] | None = None, cwd: str = ""
    ) -> dict[str, str]:
        """Deterministic hook verdict for Claude's state-changing tools."""
        tool_input = tool_input or {}
        if tool_name.startswith("mcp__conclave__"):
            return {"decision": "allow", "reason": "Conclave communication is always allowed"}
        with closing(self._connect()) as conn:
            if self._pending_intent_count(conn):
                return {
                    "decision": "deny",
                    "reason": "new operator intent is waiting for Codex review",
                }
            if self._blocking_veto_count(conn):
                return {"decision": "deny", "reason": "a Codex veto is active"}
            execution = self._current_execution(conn)
            if execution is None:
                return {"decision": "deny", "reason": "no dual-approved execution has started"}
            if execution["status"] not in {"running", "rework"}:
                return {
                    "decision": "deny",
                    "reason": f"execution is {execution['status']}, not running",
                }
            plan_row = conn.execute("SELECT payload_json FROM plans WHERE id = ?", (execution["plan_id"],)).fetchone()
            if plan_row is None:
                return {"decision": "deny", "reason": "approved plan is missing"}
            plan = json.loads(plan_row["payload_json"])
        if tool_name in {"Edit", "Write", "NotebookEdit"}:
            target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
            if not target:
                return {"decision": "deny", "reason": "file-changing tool did not identify a target"}
            target_path = Path(target)
            if not target_path.is_absolute():
                target_path = Path(cwd or os.getcwd()) / target_path
            target_norm = os.path.normcase(str(target_path.resolve()))
            for allowed in plan.get("allowed_paths", []):
                allowed_path = Path(allowed)
                if not allowed_path.is_absolute():
                    allowed_path = Path(cwd or os.getcwd()) / allowed_path
                allowed_norm = os.path.normcase(str(allowed_path.resolve()))
                try:
                    if os.path.commonpath([target_norm, allowed_norm]) == allowed_norm:
                        return {"decision": "allow", "reason": "target is in the approved path scope"}
                except ValueError:
                    continue
            return {"decision": "deny", "reason": f"target is outside approved paths: {target}"}
        if tool_name in {"Bash", "PowerShell"}:
            command = str(tool_input.get("command", "")).strip()
            if not command:
                return {"decision": "deny", "reason": "shell tool did not identify a command"}
            prefixes = [str(x).strip() for x in plan.get("allowed_commands", [])]
            if "*" in prefixes or any(command.casefold().startswith(p.casefold()) for p in prefixes if p):
                return {"decision": "allow", "reason": "command matches an approved prefix"}
            return {"decision": "deny", "reason": "command is outside approved command prefixes"}
        return {"decision": "allow", "reason": "execution is active and the tool has no path/command scope"}

