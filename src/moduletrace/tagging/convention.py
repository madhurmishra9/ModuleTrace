"""Canonical ModuleTrace tag keys and per-cloud realization.

See docs/tagging-convention.md for the full rationale, especially the GCP label charset caveat.
"""

from __future__ import annotations

from moduletrace.schemas.normalized import ModuleTraceTags
from moduletrace.schemas.terraform import Cloud
from moduletrace.tagging.gcp_label_codec import GcpLabelLookup, sanitize_gcp_label_key

CANONICAL_KEYS = (
    "module-source",
    "module-version",
    "workspace",
    "team",
    "ttl",
)

_FIELD_BY_CANONICAL_KEY = {
    "module-source": "module_source",
    "module-version": "module_version",
    "workspace": "workspace",
    "team": "team",
    "ttl": "ttl",
}


def aws_azure_tag_key(canonical_key: str) -> str:
    """AWS and Azure both allow colons in tag names, so the canonical key is used verbatim."""
    return f"moduletrace:{canonical_key}"


def to_cloud_tags(
    tags: ModuleTraceTags, cloud: Cloud, gcp_lookup: GcpLabelLookup | None = None
) -> dict[str, str]:
    """Render a ModuleTraceTags model as the native tag/label dict for the given cloud.

    For GCP, values that don't fit the label charset are hashed via `gcp_lookup` (required when
    cloud="gcp" so the hash -> original mapping can be recovered later).
    """
    result: dict[str, str] = {}
    for canonical_key in CANONICAL_KEYS:
        value = getattr(tags, _FIELD_BY_CANONICAL_KEY[canonical_key])
        if value is None:
            continue
        if cloud == "gcp":
            if gcp_lookup is None:
                raise ValueError("gcp_lookup is required to render GCP labels")
            key = sanitize_gcp_label_key(f"moduletrace:{canonical_key}")
            result[key] = gcp_lookup.encode(value)
        else:
            result[aws_azure_tag_key(canonical_key)] = value
    return result


def from_raw_tags(raw_tags: dict[str, str], cloud: Cloud) -> ModuleTraceTags:
    """Extract ModuleTrace convention tags from a resource's raw (cloud-native) tag/label dict.

    For GCP, values that were hashed at write-time come back as opaque `h_<hex>` strings here;
    resolving them to the original requires the write-time `GcpLabelLookup` (see its docstring).
    """
    if cloud == "gcp":
        key_lookup = {sanitize_gcp_label_key(f"moduletrace:{k}"): k for k in CANONICAL_KEYS}
    else:
        key_lookup = {aws_azure_tag_key(k): k for k in CANONICAL_KEYS}

    found: dict[str, str] = {}
    for raw_key, raw_value in raw_tags.items():
        canonical_key = key_lookup.get(raw_key)
        if canonical_key is not None:
            found[_FIELD_BY_CANONICAL_KEY[canonical_key]] = raw_value

    return ModuleTraceTags(**found)


def tag_confidence(tags: ModuleTraceTags) -> str:
    """Classify how completely a resource carries the ModuleTrace convention.

    `ttl` is intentionally excluded from the completeness check since it's optional
    (only ephemeral resources are expected to carry it).
    """
    required = (tags.module_source, tags.module_version, tags.workspace, tags.team)
    present = sum(1 for v in required if v is not None)
    if present == len(required):
        return "complete"
    if present == 0:
        return "missing"
    return "partial"
