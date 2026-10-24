"""Client for `codex app-server` over stdio (JSON-RPC, one JSON object per line).

Proven 2026-10-11 by scratchpad probe_appserver.py: initialize -> initialized -> thread/start (our
baseInstructions, read-only sandbox, approvals never, ephemeral) -> turn/start (text input, outputSchema,
effort) -> item/completed (agentMessage) ... turn/completed. gpt-5.6-sol, effort medium: ~10 s a turn.
"""
import json
import os
import queue
import subprocess
import threading
import time

CODEX_JS = os.path.expandvars(r"%APPDATA%\npm\node_modules\@openai\codex\bin\codex.js")


class AppServerError(RuntimeError):
    pass


class AppServer:
    def __init__(self, cwd):
        self.cwd = cwd
        os.makedirs(cwd, exist_ok=True)
        self.p = subprocess.Popen(["node", CODEX_JS, "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1, cwd=cwd,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.lock = threading.Lock()          # one writer
        self.nid = 0
        self.replies = {}                     # id -> queue for the response
        self.turns = {}                       # turn id -> queue for its notifications
        self.pending_turn_msgs = []           # notifications that arrived before turn/start answered
        self.stderr = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=lambda: [self.stderr.append(l) for l in self.p.stderr], daemon=True).start()
        self.request("initialize", {"clientInfo": {"name": "commissar", "version": "0.1"}}, timeout=60)
        self._write({"jsonrpc": "2.0", "method": "initialized"})

    def alive(self):
        return self.p.poll() is None

    def _write(self, msg):
        with self.lock:
            self.p.stdin.write(json.dumps(msg) + "\n")
            self.p.stdin.flush()

    def _read(self):
        for line in self.p.stdout:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if "method" in m and "id" in m:   # a request from the server (approval etc.): never granted
                self._write({"jsonrpc": "2.0", "id": m["id"], "error": {"code": -32601, "message": "declined"}})
                continue
            if "id" in m and m["id"] in self.replies:
                self.replies.pop(m["id"]).put(m)
                continue
            params = m.get("params") or {}
            tid = params.get("turnId") or (params.get("turn") or {}).get("id")
            if tid and tid in self.turns:
                self.turns[tid].put(m)
            elif tid:
                self.pending_turn_msgs.append(m)

    def request(self, method, params, timeout=120):
        with self.lock:
            self.nid += 1
            rid = self.nid
        q = queue.Queue()
        self.replies[rid] = q
        self._write({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        try:
            m = q.get(timeout=timeout)
        except queue.Empty:
            raise AppServerError(f"{method}: no answer in {timeout} s; stderr: {''.join(self.stderr[-3:])}")
        if "error" in m:
            raise AppServerError(f"{method}: {m['error']}")
        return m["result"]

    def start_thread(self, base_instructions, sandbox="read-only", cwd=None):
        """read-only for reviews; workspace-write (rooted at cwd) only for her repair turns."""
        r = self.request("thread/start", {"baseInstructions": base_instructions, "sandbox": sandbox,
                                          "approvalPolicy": "never", "ephemeral": True, "cwd": cwd or self.cwd})
        return r["thread"]["id"]

    def turn(self, thread_id, text, schema, effort="medium", timeout=240):
        """Send one turn; return (final agent message text, seconds)."""
        t0 = time.perf_counter()
        r = self.request("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": text}],
                                        "outputSchema": schema, "effort": effort})
        tid = r["turn"]["id"]
        q = queue.Queue()
        self.turns[tid] = q
        for m in [m for m in self.pending_turn_msgs if ((m.get("params") or {}).get("turnId") or
                                                         ((m.get("params") or {}).get("turn") or {}).get("id")) == tid]:
            q.put(m)
        texts, end = [], time.time() + timeout
        try:
            while True:
                try:
                    m = q.get(timeout=max(1, end - time.time()))
                except queue.Empty:
                    raise AppServerError(f"turn {tid}: no completion in {timeout} s")
                meth = m.get("method")
                if meth == "item/completed" and m["params"]["item"].get("type") == "agentMessage":
                    texts.append(m["params"]["item"].get("text", ""))
                elif meth == "error":
                    raise AppServerError(f"turn error: {m.get('params')}")
                elif meth == "turn/completed":
                    break
        finally:
            self.turns.pop(tid, None)
        if not texts:
            raise AppServerError("turn completed with no agent message")
        return texts[-1], time.perf_counter() - t0

    def close(self):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except OSError:
            pass
