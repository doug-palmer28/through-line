"""Append-only, hash-chained audit log: output/audit_log.json.

The file is a JSON array. A new entry is written by overwriting only the closing
bracket at the end of the file, so the bytes of earlier entries are never
touched. Each entry stores the hash of the one before it; editing or deleting
an old entry breaks the chain, which `audit_verify` detects.

The project lives in a OneDrive folder, which can briefly lock files while
syncing: each append is retried, a failed write is rolled back to the exact
previous bytes, and a file found cut off mid-entry is repaired by dropping only
the incomplete fragment (logged as `audit_repaired`).

Privacy rule: callers pass summaries, never raw documents, passwords, or keys.
"""

import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from config import AUDIT_LOG_PATH
from models import AuditEntry

_TAIL = b"\n]\n"
_GENESIS = "0" * 64
_lock = threading.Lock()


def audit_path() -> Path:
    # Tests point this at a scratch file so they never touch the real log.
    return Path(os.getenv("THROUGH_LINE_AUDIT", AUDIT_LOG_PATH))


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def _read(path: Path) -> list[dict]:
    if not path.exists() or not path.read_bytes().strip():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _complete_prefix(raw: bytes) -> tuple[list[dict], int]:
    """Entries parsed from the start of a (possibly cut-off) array, and the byte offset after the last one."""
    text = raw.decode("utf-8", errors="replace")
    dec = json.JSONDecoder()
    i = text.index("[") + 1
    entries, end = [], i
    while True:
        while i < len(text) and text[i] in " \r\n\t,":
            i += 1
        if i >= len(text) or text[i] != "{":
            break
        try:
            obj, j = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            break
        entries.append(obj)
        end = i = j
    return entries, len(text[:end].encode("utf-8"))


def _repair(path: Path) -> dict | None:
    """Fix a file cut off mid-write. Returns what was done, or None if it was fine."""
    raw = path.read_bytes()
    try:
        json.loads(raw)
        if raw.endswith(_TAIL):
            return None
        # Valid file with a different ending (e.g. CRLF from git): rewrite only the closing bracket.
        end = len(raw.rstrip().removesuffix(b"]").rstrip())
        with path.open("r+b") as f:
            f.truncate(end)
            f.seek(end)
            f.write(_TAIL)
        return None
    except json.JSONDecodeError:
        pass
    entries, end = _complete_prefix(raw)
    dropped = len(raw) - end
    with path.open("r+b") as f:
        f.truncate(end)
        f.seek(end)
        f.write(_TAIL)
        f.flush()
        os.fsync(f.fileno())
    return {"kept_entries": len(entries), "dropped_bytes_of_incomplete_entry": dropped}


def _write_tail(path: Path, data: bytes) -> None:
    """Replace the closing bracket with `data`, rolling back on any failure."""
    size = path.stat().st_size
    with path.open("r+b") as f:
        f.seek(size - len(_TAIL))
        if f.read() != _TAIL:
            raise RuntimeError(f"{path} doesn't end the way the audit writer left it.")
        try:
            f.seek(size - len(_TAIL))
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        except OSError:
            f.seek(size - len(_TAIL))
            f.write(_TAIL)
            f.truncate(size)
            f.flush()
            raise


def _append_locked(path: Path, **fields) -> dict:
    entries = _read(path)
    last = entries[-1] if entries else None
    entry = AuditEntry(
        seq=(last["seq"] + 1) if last else 1,
        prev_hash=last["hash"] if last else _GENESIS,
        logged_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **fields,
    ).model_dump(mode="json")
    entry["hash"] = _digest(entry)
    blob = json.dumps(entry, indent=2, default=str).encode()

    path.parent.mkdir(parents=True, exist_ok=True)
    if not entries:  # missing file or the empty starter array
        path.write_bytes(b"[\n" + blob + _TAIL)
        return entry
    for attempt in range(6):
        try:
            _write_tail(path, b",\n" + blob + _TAIL)
            return entry
        except OSError:
            if attempt == 5:
                raise
            time.sleep(0.25 * (attempt + 1))  # e.g. OneDrive briefly holding the file
    return entry


def audit_append(**fields) -> dict:
    """Add one entry to the end of the log and return it."""
    path = audit_path()
    with _lock:
        if path.exists() and _read_safe(path):
            repaired = _repair(path)
            if repaired:
                _append_locked(path, event="audit_repaired", agent="system", output=repaired)
        return _append_locked(path, **fields)


def _read_safe(path: Path) -> bool:
    """True if the file has content worth checking for repair."""
    return bool(path.read_bytes().strip()) and path.read_bytes().strip() != b"[]"


def audit_verify() -> dict:
    """Check the hash chain. Returns {'ok': bool, 'entries': n, 'problem': ...}."""
    prev = _GENESIS
    entries = _read(audit_path())
    for i, e in enumerate(entries, start=1):
        if e.get("seq") != i or e.get("prev_hash") != prev or _digest(e) != e.get("hash"):
            return {"ok": False, "entries": len(entries), "problem": f"entry seq={e.get('seq')} (position {i})"}
        prev = e["hash"]
    return {"ok": True, "entries": len(entries), "problem": None}


def audit_entries(session_id: str | None = None, limit: int = 200) -> list[dict]:
    entries = _read(audit_path())
    if session_id:
        entries = [e for e in entries if e.get("session_id") == session_id]
    return entries[-limit:]
