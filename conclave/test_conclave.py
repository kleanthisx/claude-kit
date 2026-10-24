from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import claude_hook
import push
from core import Conclave, ConclaveError
from mcp_server import dispatch as mcp_dispatch
from push import dispatch_pending, notification_command, wake_message


HERE = Path(__file__).resolve().parent


def plan_for(root: Path, title: str = "Council A live-test architecture") -> dict:
    return {
        "title": title,
        "objective": "Deliver the agreed live-test architecture without silent scope changes.",
        "user_intent": "Claude leads implementation; Codex guards architecture, intent, scope and acceptance.",
        "requirements": ["Two-party plan approval", "Evidence-backed final audit"],
        "constraints": ["No implementation before consensus", "Preserve unrelated user work"],
        "non_goals": ["Image and audio production implementation"],
        "architecture": ["Shared SQLite ledger", "Identity-bound stdio MCP clients"],
        "tasks": ["Implement one bounded change", "Run its relevant tests"],
        "acceptance_criteria": ["Both plan signatures recorded", "Tests pass"],
        "risks": ["A client bypasses the optional hook"],
        "budget": "One implementation cycle; escalate material expansion to the operator.",
        "allowed_paths": [str(root)],
        "allowed_commands": ["python -m unittest", "git status"],
        "change_summary": "",
    }


class ConclaveWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "conclave.db"
        self.claude = Conclave(self.db, "claude", "council-a")
        self.codex = Conclave(self.db, "codex", "council-a")
        self.claude.open_council("Council A", "Agree, execute and audit the live-test architecture")
        operator = self.claude.record_operator_message(
            "Claude leads. Codex may veto scope or corner-cutting.",
            "test",
            "operator-1",
        )
        self.codex.review_operator_message(operator["message_id"], "clarifies", "Defines authority.")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def approve_and_start(self) -> tuple[int, int]:
        submitted = self.claude.submit_plan(plan_for(self.root))
        self.claude.review_plan(submitted["plan_id"], "approve", "Executable and bounded.")
        with self.assertRaises(ConclaveError):
            self.claude.start_execution(submitted["plan_id"])
        codex_review = self.codex.review_plan(
            submitted["plan_id"], "approve", "Architecture and acceptance criteria are sufficient."
        )
        self.assertTrue(codex_review["consensus"])
        execution = self.claude.start_execution(submitted["plan_id"])
        return submitted["plan_id"], execution["execution_id"]

    def test_full_workflow_with_veto_and_acceptance(self) -> None:
        plan_id, execution_id = self.approve_and_start()

        inside = self.root / "src" / "file.py"
        allow = self.claude.gate_decision("Write", {"file_path": str(inside)}, str(self.root))
        deny = self.claude.gate_decision("Write", {"file_path": str(self.root.parent / "outside.py")})
        shell = self.claude.gate_decision("PowerShell", {"command": "python -m unittest -v"})
        self.assertEqual(allow["decision"], "allow")
        self.assertEqual(deny["decision"], "deny")
        self.assertEqual(shell["decision"], "allow")

        event = self.claude.report_event(
            "agent_spawned", "Spawned bounded implementation agent", {"task": "Implement shared state"}
        )
        self.assertEqual(event["status"], "running")

        veto = self.codex.issue_veto(
            "Acceptance criterion: tests pass",
            "The report contains no test result.",
            "Run the relevant suite and attach the result.",
        )
        self.assertEqual(self.claude.gate_decision("Agent", {})["decision"], "deny")
        self.claude.respond_veto(veto["veto_id"], "Tests now run cleanly.", ["unittest: 8 passed"])
        self.codex.resolve_veto(veto["veto_id"], "release", "Evidence satisfies the criterion.")
        self.assertEqual(self.claude.gate_decision("Agent", {})["decision"], "allow")

        self.claude.report_event("test_result", "Conclave suite passed", {"passed": 8, "failed": 0})
        completion = self.claude.report_event(
            "completion_requested", "Implementation complete", {"plan_id": plan_id}
        )
        self.assertEqual(completion["status"], "audit")
        accepted = self.codex.audit("accept", "All locked criteria are met.", ["8 tests passed"])
        self.assertEqual(accepted["execution_status"], "completed")

        state = self.codex.get_state()
        self.assertEqual(state["council"]["status"], "accepted")
        self.assertEqual(state["current_execution"]["id"], execution_id)
        self.assertGreater(len(self.codex.read_ledger()["entries"]), 8)

    def test_new_operator_message_pauses_until_codex_reviews(self) -> None:
        self.approve_and_start()
        recorded = self.claude.record_operator_message(
            "Keep image generation out of this milestone.", "test", "operator-2"
        )
        self.assertTrue(recorded["execution_paused"])
        self.assertEqual(self.claude.gate_decision("Agent", {})["decision"], "deny")

        reviewed = self.codex.review_operator_message(
            recorded["message_id"], "clarifies", "Reinforces the existing non-goal."
        )
        self.assertEqual(reviewed["pending"], 0)
        self.assertEqual(self.claude.gate_decision("Agent", {})["decision"], "allow")

    def test_scope_change_stales_plan_and_requires_revision(self) -> None:
        old_plan_id, _ = self.approve_and_start()
        recorded = self.claude.record_operator_message(
            "Add paid character publishing to this same milestone.", "test", "operator-3"
        )
        self.codex.review_operator_message(
            recorded["message_id"], "changes_scope", "Publishing is a new bounded workstream."
        )
        state = self.codex.get_state()
        self.assertEqual(state["current_plan"]["status"], "stale")
        self.assertEqual(state["current_execution"]["status"], "paused_scope")
        with self.assertRaises(ConclaveError):
            self.claude.start_execution(old_plan_id)

        revised_plan = plan_for(self.root, "Council A live test plus publishing")
        revised_plan["requirements"].append("Paid and free character publishing")
        revised_plan["change_summary"] = "Adds the operator-requested publishing workstream."
        revised = self.claude.submit_plan(revised_plan)
        self.assertEqual(revised["revision"], 2)
        self.assertNotEqual(revised["plan_id"], old_plan_id)

    def test_actor_permissions_are_bound_at_process_start(self) -> None:
        plan = self.claude.submit_plan(plan_for(self.root))
        with self.assertRaises(ConclaveError):
            self.claude.review_operator_message(1, "no_change", "Impersonation attempt")
        with self.assertRaises(ConclaveError):
            self.codex.start_execution(plan["plan_id"])
        with self.assertRaises(ConclaveError):
            self.claude.issue_veto("x", "y", "z")

    def test_peer_messages_are_bidirectional_and_cursor_based(self) -> None:
        sent = self.claude.send_message("codex", "operating_brief", "The operator prefers outcome-first updates.")
        codex_messages = self.codex.read_messages(after_id=0)
        ids = [message["id"] for message in codex_messages["messages"]]
        self.assertIn(sent["message_id"], ids)
        reply = self.codex.send_message("other", "answer", "Operating brief received.")
        claude_messages = self.claude.read_messages(after_id=sent["message_id"])
        self.assertEqual(claude_messages["messages"][-1]["id"], reply["message_id"])

    def test_push_fans_out_to_everyone_except_pusher_and_pull_consumes(self) -> None:
        self.codex.pull()  # clear the setUp operator delivery
        sent = self.claude.push("question", "Please review the architecture boundary.")
        self.assertEqual(
            [(item["recipient"], item["status"]) for item in sent["deliveries"]],
            [("codex", "pending")],
        )
        self.assertEqual(self.claude.pull()["pulled"], 0)

        received = self.codex.pull()
        self.assertEqual(received["pulled"], 1)
        self.assertEqual(received["messages"][0]["id"], sent["message_id"])
        self.assertEqual(received["messages"][0]["body"], "Please review the architecture boundary.")
        self.assertEqual(self.codex.pull()["pulled"], 0)
        self.assertEqual(self.codex.get_state()["inbox"], [])

        reply = self.codex.push("answer", "Boundary approved.")
        self.assertEqual([item["recipient"] for item in reply["deliveries"]], ["claude"])

    def test_operator_message_pushes_only_to_the_other_participant(self) -> None:
        recorded = self.claude.record_operator_message(
            "Keep the council on project-a only.", "test", "operator-fanout"
        )
        self.assertEqual([item["recipient"] for item in recorded["deliveries"]], ["codex"])

    def test_endpoint_registration_and_push_status_never_regress_after_pull(self) -> None:
        endpoint = self.codex.register_endpoint("codex_queue", "thread-123", str(self.root))
        self.assertEqual(endpoint["transport"], "codex_queue")
        self.assertEqual(self.codex.get_endpoint()["address"], "thread-123")

        self.codex.pull()
        sent = self.claude.push("status", "A durable status update.")
        claimed = self.codex.claim_deliveries()
        self.assertEqual([row["id"] for row in claimed], [sent["deliveries"][0]["delivery_id"]])
        self.codex.pull()
        marked = self.codex.mark_delivery_push(claimed[0]["id"])
        self.assertEqual(marked["status"], "pulled")


class PushTransportTests(unittest.TestCase):
    def test_wake_signal_has_no_message_body_and_commands_target_registered_client(self) -> None:
        notice = wake_message("council-a", [9, 7])
        self.assertIn("conclave_pull", notice)
        self.assertIn("[7, 9]", notice)
        self.assertNotIn("secret body", notice)

        with patch("push._resolve_command", return_value="client.exe"):
            codex_command, codex_env = notification_command(
                {"transport": "codex_queue", "address": "thread-1", "cwd": ""}, notice
            )
            self.assertEqual(codex_command[:4], ["client.exe", "queue", "--thread", "thread-1"])
            self.assertEqual(codex_env, {})

            claude_command, claude_env = notification_command(
                {"transport": "claude_worker", "address": "claude", "cwd": ""}, notice
            )
            self.assertIn("--allowedTools", claude_command)
            self.assertIn("--disallowedTools", claude_command)
            self.assertIn("sonnet", claude_command)
            self.assertEqual(claude_command[-2:], ["--print", notice])
            self.assertLess(claude_command.index("--model"), claude_command.index("--print"))
            self.assertEqual(claude_env["CONCLAVE_WORKER"], "1")

    def test_spawn_is_single_flight_per_recipient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "push.db"
            lease = push._acquire_push_lock(db.resolve(), "council-a", "claude")
            assert lease is not None
            try:
                with patch("push.subprocess.Popen") as spawned:
                    started = push.spawn_pushes(db, "council-a", recipients=["claude"])
                self.assertEqual(started, [])
                spawned.assert_not_called()
            finally:
                push._release_push_lock(*lease)

    def test_dispatch_marks_success_and_failure_without_losing_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "push.db"
            claude = Conclave(db, "claude", "council-a")
            codex = Conclave(db, "codex", "council-a")
            codex.register_endpoint("codex_queue", "thread-1", tmp)
            sent = claude.push("question", "Check this.")

            with patch("push.notify") as mocked_notify:
                result = dispatch_pending(db, "council-a", "codex")
            mocked_notify.assert_called_once()
            self.assertEqual(result["status"], "pushed")
            self.assertEqual(codex.get_state()["inbox"][0]["status"], "pushed")
            self.assertEqual(codex.pull()["messages"][0]["id"], sent["message_id"])

            claude.push("question", "Retry this.")
            with patch("push.notify", side_effect=OSError("transport unavailable")):
                failed = dispatch_pending(db, "council-a", "codex")
            self.assertEqual(failed["status"], "push_failed")
            self.assertIn("transport unavailable", failed["error"])
            self.assertEqual(len(codex.pending_deliveries()), 1)

    def test_claude_worker_is_not_successful_until_it_pulls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "worker.db"
            codex = Conclave(db, "codex", "council-a")
            claude = Conclave(db, "claude", "council-a")
            claude.register_endpoint("claude_worker", "claude", tmp)
            codex.push("question", "Pull this message.")
            with patch("push.notify"):
                result = dispatch_pending(db, "council-a", "claude")
            self.assertEqual(result["status"], "push_failed")
            self.assertIn("did not call conclave_pull", result["error"])
            self.assertEqual(len(claude.pending_deliveries()), 1)


class McpTransportTests(unittest.TestCase):
    def test_initialize_list_and_health_over_stdio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "mcp.db"
            command = [
                sys.executable,
                "-I",
                str(HERE / "mcp_server.py"),
                "--actor",
                "codex",
                "--council",
                "council-a",
                "--db",
                str(db),
            ]
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            assert process.stdin is not None
            assert process.stdout is not None

            def rpc(request: dict) -> dict:
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                return json.loads(process.stdout.readline())

            initialized = rpc(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                }
            )
            self.assertEqual(initialized["result"]["serverInfo"]["name"], "conclave")
            listed = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            tool_names = {tool["name"] for tool in listed["result"]["tools"]}
            self.assertIn("conclave_send_message", tool_names)
            self.assertIn("conclave_push", tool_names)
            self.assertIn("conclave_pull", tool_names)
            self.assertIn("conclave_register_endpoint", tool_names)
            self.assertIn("conclave_issue_veto", tool_names)
            health = rpc(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "conclave_health", "arguments": {}},
                }
            )
            self.assertTrue(health["result"]["structuredContent"]["ok"])
            process.stdin.close()
            self.assertEqual(process.wait(timeout=5), 0)
            process.stdout.close()
            assert process.stderr is not None
            process.stderr.close()


class HookTests(unittest.TestCase):
    def test_unrelated_hook_event_does_not_retry_a_pending_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "hook.db"
            project = Path(tmp) / "project-a"
            project.mkdir()
            codex = Conclave(db, "codex", "council-a")
            Conclave(db, "claude", "council-a")
            codex.open_council("Council A", "Test hook delivery behavior")
            codex.push("status", "Pending for Claude.")
            event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {},
                "cwd": str(project),
            }
            argv = [
                "--council", "council-a", "--db", str(db), "--mode", "observe",
                "--project-root", str(project),
            ]
            with (
                patch("sys.stdin", io.StringIO(json.dumps(event))),
                patch("claude_hook.shutil.which", return_value=None),
                patch("claude_hook.spawn_pushes") as spawned,
            ):
                self.assertEqual(claude_hook.main(argv), 0)
            spawned.assert_not_called()

    def test_user_prompt_capture_and_enforce_denial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "hook.db"
            project = Path(tmp) / "project-a"
            other_project = Path(tmp) / "slots"
            project.mkdir()
            other_project.mkdir()
            command = [
                sys.executable,
                "-I",
                str(HERE / "claude_hook.py"),
                "--council",
                "council-a",
                "--db",
                str(db),
                "--mode",
                "enforce",
                "--project-root",
                str(project),
            ]
            env = dict(os.environ, CONCLAVE_DISABLE_PUSH="1")
            ignored_event = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "slots-session",
                "prompt": "Change the slot maths.",
                "cwd": str(other_project),
            }
            ignored = subprocess.run(
                command,
                input=json.dumps(ignored_event),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                check=True,
                env=env,
            )
            self.assertEqual(ignored.stdout, "")
            prompt_event = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "session-1",
                "prompt": "Do not add image generation yet.",
                "cwd": str(project),
            }
            captured = subprocess.run(
                command,
                input=json.dumps(prompt_event),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                check=True,
                env=env,
            )
            self.assertIn("recorded operator message", captured.stdout)

            tool_event = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Agent",
                "tool_input": {"prompt": "implement"},
                "cwd": str(project),
            }
            denied = subprocess.run(
                command,
                input=json.dumps(tool_event),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                check=True,
                env=env,
            )
            payload = json.loads(denied.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")


class WorkerProvenanceTests(unittest.TestCase):
    def test_worker_push_is_marked_with_session_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "worker-metadata.db"
            claude = Conclave(db, "claude", "council-a")
            codex = Conclave(db, "codex", "council-a")
            claude.open_council("Council A", "Test worker provenance")
            with patch.dict(
                os.environ,
                {"CONCLAVE_WORKER": "1", "CONCLAVE_WORKER_SESSION": "worker-session-123"},
            ):
                mcp_dispatch(
                    claude,
                    "conclave_push",
                    {"kind": "status", "body": "Worker response", "metadata": {"source": "test"}},
                )
            message = codex.read_messages(after_id=0)["messages"][-1]
            self.assertEqual(message["metadata"]["source"], "test")
            self.assertIs(message["metadata"]["worker"], True)
            self.assertEqual(message["metadata"]["session"], "worker-session-123")


if __name__ == "__main__":
    unittest.main()

