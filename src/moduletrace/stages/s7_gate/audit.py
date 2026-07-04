"""Append-only audit log writer for plan execution.

See docs/architecture.md: one JSON line per resource action (succeeded/failed/skipped_state_drift),
suitable for shipping to a SIEM/log pipeline.
"""

from __future__ import annotations

from pathlib import Path

from moduletrace.schemas.plan import AuditEntry


def append_entry(audit_log_path: Path, entry: AuditEntry) -> None:
    """Append one `AuditEntry` as a JSON line. Never truncates or rewrites existing lines —
    the log is append-only, matching the plan's own immutability.
    """
    with audit_log_path.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def read_entries(audit_log_path: Path) -> list[AuditEntry]:
    """Read all entries so `apply` can resume (skip already-executed resources) after an interruption."""
    if not audit_log_path.exists():
        return []
    entries = []
    with audit_log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(AuditEntry.model_validate_json(line))
    return entries
