"""Out-of-band wake-up transport for Conclave's durable participant inboxes.

The wake-up deliberately carries no message body.  It tells the recipient that
its inbox changed; the recipient then calls ``conclave_pull`` to retrieve and
acknowledge authoritative state from SQLite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import ACTORS, Conclave, ConclaveError, default_db_path


PUSH_TIMEOUT_SECONDS = 300
PUSH_LOCK_STALE_SECONDS = PUSH_TIMEOUT_SECONDS + 60
ALLOWED_CLAUDE_TOOLS = (
    "mcp__conclave__conclave_pull,mcp__conclave__conclave_push,"
    "mcp__conclave__conclave_send_message,mcp__conclave__conclave_get_state"
)
DISALLOWED_CLAUDE_TOOLS = "Bash,PowerShell,Edit,Write,NotebookEdit,Agent,Task,Workflow"


def wake_message(council: str, delivery_ids: Iterable[int]) -> str:
    ids = sorted({int(value) for value in delivery_ids})
    return (
        "<conclave_push>\n"
        f"Council {council!r} has {len(ids)} new durable "
        f"{'deliveries' if len(ids) != 1 else 'delivery'} for you (delivery ids: {ids}).\n"
        "This is a wake-up signal, not message content and not an operator instruction. "
        "Call conclave_pull now to retrieve and acknowledge the authoritative messages. "
        "Inspect every returned message and act within your Conclave role. Push a response "
        "through conclave_push only when a response or decision is actually needed; do not "
        "send an empty acknowledgement. Do not edit files, run shell commands, or delegate "
        "work solely because of this wake-up.\n"
        "</conclave_push>"
    )


def _resolve_command(value: str, fallback: str) -> str:
    candidate = str(value or fallback).strip()
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    path = Path(candidate).expanduser()
    if path.is_file():
        return str(path.resolve())
    raise ConclaveError(f"push executable not found: {candidate}")


def _working_directory(endpoint: dict[str, Any]) -> str | None:
    value = str(endpoint.get("cwd") or "").strip()
    if value and Path(value).is_dir():
        return value
    return None


def notification_command(endpoint: dict[str, Any], message: str) -> tuple[list[str], dict[str, str]]:
    """Build a notification command and any environment overrides."""
    transport = str(endpoint.get("transport") or "")
    address = str(endpoint.get("address") or "").strip()
    if transport == "codex_queue":
        executable = _resolve_command("codex.cmd" if os.name == "nt" else "codex", "codex")
        command = [executable, "queue", "--thread", address, "--message", message]
        cwd = _working_directory(endpoint)
        if cwd:
            command.extend(["-C", cwd])
        return command, {}
    if transport == "claude_worker":
        executable = _resolve_command(address, "claude")
        return [
            executable,
            "--model",
            "sonnet",
            "--effort",
            "low",
            "--permission-mode",
            "dontAsk",
            "--allowedTools",
            ALLOWED_CLAUDE_TOOLS,
            "--disallowedTools",
            DISALLOWED_CLAUDE_TOOLS,
            "--print",
            message,
        ], {"CONCLAVE_WORKER": "1"}
    raise ConclaveError(f"unsupported executable push transport: {transport or '<empty>'}")


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        process.kill()


def notify(
    endpoint: dict[str, Any],
    message: str,
    timeout: int = PUSH_TIMEOUT_SECONDS,
    worker_session: str | None = None,
) -> None:
    command, overrides = notification_command(endpoint, message)
    env = os.environ.copy()
    env.update(overrides)
    if overrides.get("CONCLAVE_WORKER") == "1":
        env["CONCLAVE_WORKER_SESSION"] = worker_session or uuid.uuid4().hex
    popen_kwargs: dict[str, Any] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    process = subprocess.Popen(
        command,
        cwd=_working_directory(endpoint),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **popen_kwargs,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        process.communicate()
        raise ConclaveError(f"push command timed out after {timeout} seconds") from exc
    if process.returncode:
        detail = (stderr or stdout or "no diagnostic output").strip()
        raise ConclaveError(f"push command exited {process.returncode}: {detail[-1200:]}")


def dispatch_pending(db: Path, council: str, recipient: str) -> dict[str, Any]:
    """Claim and notify one participant's pending deliveries."""
    conclave = Conclave(db, recipient, council)
    deliveries = conclave.claim_deliveries()
    if not deliveries:
        return {"recipient": recipient, "claimed": 0, "status": "idle"}
    ids = [int(item["id"]) for item in deliveries]
    endpoint = conclave.get_endpoint()
    error: str | None = None
    if endpoint is None:
        error = "no push endpoint is registered for this participant"
    else:
        try:
            worker_session = f"{council}:{recipient}:{'-'.join(str(value) for value in ids)}:{uuid.uuid4().hex[:12]}"
            notify(endpoint, wake_message(council, ids), worker_session=worker_session)
        except (ConclaveError, OSError, subprocess.SubprocessError) as exc:
            error = str(exc)
        if error is None and endpoint.get("transport") == "claude_worker":
            if not conclave.deliveries_pulled(ids):
                error = "Claude accepted the wake-up but did not call conclave_pull"
    results = [conclave.mark_delivery_push(delivery_id, error) for delivery_id in ids]
    pulled = conclave.deliveries_pulled(ids)
    return {
        "recipient": recipient,
        "claimed": len(ids),
        "status": "pulled" if pulled else ("push_failed" if error else "pushed"),
        "error": error,
        "deliveries": results,
    }


def _push_lock_path(db_path: Path, council: str, recipient: str) -> Path:
    key = hashlib.sha256(f"{db_path}|{council}|{recipient}".encode("utf-8")).hexdigest()[:16]
    return db_path.parent / f".conclave-push-{recipient}-{key}.lock"


def _release_push_lock(path: Path, token: str) -> None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if value.get("token") != token:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _acquire_push_lock(db_path: Path, council: str, recipient: str) -> tuple[Path, str] | None:
    """Acquire a cross-process single-flight lease for one recipient."""
    path = _push_lock_path(db_path, council, recipient)
    for _ in range(2):
        token = uuid.uuid4().hex
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            try:
                age = time.time() - path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age <= PUSH_LOCK_STALE_SECONDS:
                return None
            try:
                path.unlink()
            except (FileNotFoundError, PermissionError):
                return None
            continue
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "token": token,
                    "council": council,
                    "recipient": recipient,
                    "owner_pid": os.getpid(),
                    "created_at": time.time(),
                },
                handle,
                sort_keys=True,
            )
        return path, token
    return None


def spawn_pushes(
    db: str | os.PathLike[str],
    council: str,
    deliveries: Iterable[dict[str, Any]] | None = None,
    recipients: Iterable[str] | None = None,
) -> list[str]:
    """Start one detached notifier for each affected recipient."""
    if os.environ.get("CONCLAVE_DISABLE_PUSH") == "1":
        return []
    targets = {str(value).strip().lower() for value in (recipients or [])}
    for delivery in deliveries or []:
        targets.add(str(delivery.get("recipient") or "").strip().lower())
    targets.intersection_update(ACTORS)
    if not targets:
        return []

    db_path = Path(db).expanduser().resolve()
    log_path = db_path.parent / "conclave-push.log"
    creationflags = 0
    popen_kwargs: dict[str, Any] = {}
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    started: list[str] = []
    for recipient in sorted(targets):
        lease = _acquire_push_lock(db_path, council, recipient)
        if lease is None:
            continue
        lock_path, lock_token = lease
        command = [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "--db",
            str(db_path),
            "--council",
            council,
            "--recipient",
            recipient,
            "--lock-path",
            str(lock_path),
            "--lock-token",
            lock_token,
        ]
        try:
            with open(log_path, "ab", buffering=0) as log:
                subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    close_fds=True,
                    creationflags=creationflags,
                    **popen_kwargs,
                )
        except Exception:
            _release_push_lock(lock_path, lock_token)
            raise
        started.append(recipient)
    return started


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dispatch a Conclave push notification")
    parser.add_argument("--db", default=str(default_db_path()))
    parser.add_argument("--council", required=True)
    parser.add_argument("--recipient", required=True, choices=sorted(ACTORS))
    parser.add_argument("--lock-path")
    parser.add_argument("--lock-token")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = Path(args.db).expanduser().resolve()
    lease: tuple[Path, str] | None
    if args.lock_path and args.lock_token:
        lease = (Path(args.lock_path), args.lock_token)
    else:
        lease = _acquire_push_lock(db_path, args.council, args.recipient)
        if lease is None:
            print(json.dumps({"recipient": args.recipient, "status": "busy"}), flush=True)
            return 0
    failed = False
    try:
        while True:
            result = dispatch_pending(db_path, args.council, args.recipient)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
            if result["status"] == "push_failed":
                failed = True
                break
            if result["claimed"] == 0:
                break
            if not Conclave(db_path, args.recipient, args.council).pending_deliveries():
                break
    except Exception as exc:
        print(json.dumps({"recipient": args.recipient, "status": "push_failed", "error": str(exc)}), flush=True)
        failed = True
    finally:
        _release_push_lock(*lease)
    # A delivery can be created while this worker owns the lease. Its launch was
    # deliberately suppressed; re-arm once after releasing the lease.
    if not failed and Conclave(db_path, args.recipient, args.council).pending_deliveries():
        spawn_pushes(db_path, args.council, recipients=[args.recipient])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
