#!/usr/bin/env python3
"""
tally-usage.py — LOCAL token-usage tally for Claude Code transcripts.

Scans <CLAUDE_HOME>/projects/**/*.jsonl (session + subagent transcripts), sums
token usage per day per model, and writes a markdown report.

Stdlib only. No network calls. This is a convenience meter, NOT a billing
source of truth — a server-reported usage ledger (if this site keeps one,
see templates/ops/OPS.template.md) is that.

    python tally-usage.py                          # scan <CLAUDE_HOME>/projects, write <CLAUDE_HOME>/usage-tally.md
    python tally-usage.py --help
    python tally-usage.py --projects-dir <dir> --out <file.md>
    python tally-usage.py --days 30
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, date

HOME = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_HOME") or os.path.join(HOME, ".claude")
DEFAULT_PROJECTS_DIR = os.path.join(CLAUDE_HOME, "projects")
DEFAULT_OUT_PATH = os.path.join(CLAUDE_HOME, "usage-tally.md")
DEFAULT_DAYS_TO_SHOW = 14


def iter_jsonl_files(root):
    """Recursively yield *.jsonl file paths under root, skipping any
    directory literally named 'memory'."""
    for dirpath, dirnames, filenames in os.walk(root):
        # skip memory/ dirs anywhere in the tree
        dirnames[:] = [d for d in dirnames if d.lower() != "memory"]
        for fn in filenames:
            if fn.lower().endswith(".jsonl"):
                yield os.path.join(dirpath, fn)


def file_mtime_date(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).date().isoformat()
    except OSError:
        return date.today().isoformat()


def line_date(obj, fallback):
    ts = obj.get("timestamp")
    if isinstance(ts, str) and ts:
        # transcript timestamps are UTC (Z suffix) -- convert to local time
        # so day-bucketing matches the machine's wall-clock "today".
        try:
            iso = ts.replace("Z", "+00:00")
            dt_utc = datetime.fromisoformat(iso)
            dt_local = dt_utc.astimezone()  # -> system local tz
            return dt_local.date().isoformat()
        except ValueError:
            pass
    return fallback


def extract_usage(obj):
    """Return (model, usage_dict) if this line is an assistant message
    carrying usage, else (None, None)."""
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None, None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None, None
    model = msg.get("model") or "unknown"
    return model, usage


def build_report(projects_dir, days_to_show):
    # agg[day][model] -> dict of sums
    agg = defaultdict(lambda: defaultdict(lambda: {
        "msgs": 0, "output": 0, "input": 0, "cache_read": 0, "cache_write": 0
    }))

    files_scanned = 0
    lines_scanned = 0

    for path in iter_jsonl_files(projects_dir):
        files_scanned += 1
        fallback_day = file_mtime_date(path)
        try:
            f = open(path, "r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with f:
            for raw_line in f:
                lines_scanned += 1
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue
                model, usage = extract_usage(obj)
                if model is None:
                    continue

                day = line_date(obj, fallback_day)
                bucket = agg[day][model]
                bucket["msgs"] += 1
                bucket["output"] += usage.get("output_tokens", 0) or 0
                bucket["input"] += usage.get("input_tokens", 0) or 0
                bucket["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
                bucket["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0

    days_sorted = sorted(agg.keys(), reverse=True)[:days_to_show]

    lines = []
    lines.append("# Claude Code Usage Tally")
    lines.append("")
    lines.append(
        "LOCAL tally from transcripts — convenience meter; a server-reported usage ledger, if this "
        "site keeps one, is ground truth."
    )
    lines.append("")
    lines.append(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    lines.append(f"_Scanned: {projects_dir}_")
    lines.append("")

    if not days_sorted:
        lines.append("No usage data found.")
    else:
        for day in days_sorted:
            lines.append(f"## {day}")
            lines.append("")
            lines.append("| Model | msgs | output | input | cacheRead | cacheWrite |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            day_totals = {"msgs": 0, "output": 0, "input": 0, "cache_read": 0, "cache_write": 0}
            for model in sorted(agg[day].keys()):
                b = agg[day][model]
                lines.append(
                    f"| {model} | {b['msgs']} | {b['output']} | {b['input']} | "
                    f"{b['cache_read']} | {b['cache_write']} |"
                )
                for k in day_totals:
                    day_totals[k] += b[k]
            lines.append(
                f"| **TOTAL** | **{day_totals['msgs']}** | **{day_totals['output']}** | "
                f"**{day_totals['input']}** | **{day_totals['cache_read']}** | "
                f"**{day_totals['cache_write']}** |"
            )
            lines.append("")

    return "\n".join(lines) + "\n", agg, files_scanned, lines_scanned


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projects-dir", default=DEFAULT_PROJECTS_DIR,
                     help=f"root to scan for *.jsonl transcripts (default: {DEFAULT_PROJECTS_DIR})")
    ap.add_argument("--out", default=DEFAULT_OUT_PATH,
                     help=f"markdown report path to write (default: {DEFAULT_OUT_PATH})")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS_TO_SHOW,
                     help=f"how many most-recent days to include (default: {DEFAULT_DAYS_TO_SHOW})")
    ap.add_argument("--dry-run", action="store_true",
                     help="scan and print the summary but do not write the report file")
    args = ap.parse_args()

    if not os.path.isdir(args.projects_dir):
        sys.exit(f"tally-usage: no such projects dir: {args.projects_dir}")

    report, agg, files_scanned, lines_scanned = build_report(args.projects_dir, args.days)

    if not args.dry_run:
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as out:
            out.write(report)

    # 3-line stdout summary: today's totals per model
    today = date.today().isoformat()
    print(f"tally-usage: scanned {files_scanned} files / {lines_scanned} lines"
          + (" (dry run, report not written)" if args.dry_run else f" -> {args.out}"))
    if today in agg and agg[today]:
        parts = []
        for model in sorted(agg[today].keys()):
            b = agg[today][model]
            parts.append(f"{model}: {b['msgs']}msgs out={b['output']} in={b['input']} cr={b['cache_read']} cw={b['cache_write']}")
        print(f"today ({today}):")
        print("  " + "\n  ".join(parts))
    else:
        print(f"today ({today}): no usage recorded yet")


if __name__ == "__main__":
    main()
