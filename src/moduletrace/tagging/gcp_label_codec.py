"""GCP label charset codec.

GCP labels are strictly lowercase `[a-z0-9_-]`, <=63 chars, no colons — stricter than AWS/Azure
tags. ModuleTrace tag values (e.g. a git module source URL) often can't fit that charset
losslessly, so this module hashes/shortens values that don't fit and maintains a hash -> original
lookup table so the real value can be recovered during rollup/reporting.

See docs/tagging-convention.md for the full rationale.
"""

from __future__ import annotations

import hashlib
import re

_GCP_LABEL_CHARSET = re.compile(r"^[a-z0-9_-]*$")
_GCP_LABEL_MAX_LEN = 63
_HASH_PREFIX = "h_"
_HASH_LEN = 16  # hex chars of sha256; comfortably fits the 63-char budget with the prefix


def sanitize_gcp_label_key(key: str) -> str:
    """Canonical `moduletrace:x` -> GCP-safe `moduletrace_x`.

    Keys are drawn from a small fixed set (see tagging/convention.py) so they're never hashed,
    only charset-mapped.
    """
    mangled = key.replace(":", "_").replace("-", "_").lower()
    if not _GCP_LABEL_CHARSET.match(mangled) or len(mangled) > _GCP_LABEL_MAX_LEN:
        raise ValueError(f"canonical tag key {key!r} does not fit the GCP label charset")
    return mangled


def encode_gcp_label_value(value: str) -> str:
    """Return a GCP-label-safe value, hashing it if it doesn't fit the charset/length as-is."""
    lowered = value.lower()
    if _GCP_LABEL_CHARSET.match(lowered) and len(lowered) <= _GCP_LABEL_MAX_LEN:
        return lowered
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:_HASH_LEN]
    return f"{_HASH_PREFIX}{digest}"


def is_hashed_gcp_label_value(label_value: str) -> bool:
    return label_value.startswith(_HASH_PREFIX)


class GcpLabelLookup:
    """Maintains hash -> original value mappings for GCP label values that had to be hashed.

    One instance is built per stage-2 normalization run; stage 2 attaches the relevant subset of
    entries to each `NormalizedResource.gcp_label_lookup`. Note this only resolves values that were
    hashed *by this same lookup instance* (e.g. right after a wrapper module wrote them) — a value
    hashed at resource-creation time by a different process cannot be reversed from the label alone
    without that process's own side table (see docs/tagging-convention.md for this limitation).
    """

    def __init__(self) -> None:
        self._table: dict[str, str] = {}

    def encode(self, value: str) -> str:
        label_value = encode_gcp_label_value(value)
        if is_hashed_gcp_label_value(label_value):
            self._table[label_value] = value
        return label_value

    def resolve(self, label_value: str) -> str | None:
        if not is_hashed_gcp_label_value(label_value):
            return label_value
        return self._table.get(label_value)

    def as_dict(self) -> dict[str, str]:
        return dict(self._table)
