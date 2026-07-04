"""Stage 2 entrypoint: produce stage2_normalized.json from stage1_inventory.json.

See docs/architecture.md, "Stage 2 — Resource & Tag Normalizer" and
docs/tagging-convention.md for the tag extraction/sanitization this stage owns.
"""

from __future__ import annotations

from moduletrace.schemas.normalized import NormalizedResource
from moduletrace.schemas.terraform import TerraformResourceRecord
from moduletrace.tagging.convention import from_raw_tags, tag_confidence
from moduletrace.tagging.gcp_label_codec import GcpLabelLookup


def normalize_resource(
    record: TerraformResourceRecord, gcp_lookup: GcpLabelLookup
) -> NormalizedResource:
    """Normalize a single TerraformResourceRecord into canonical shape.

    Handles canonical resource-type mapping (provider-native type -> internal taxonomy) and tag
    extraction; the canonical-type mapping table itself is not yet implemented (needs a real
    provider-type -> taxonomy list, e.g. aws_instance/google_compute_instance/azurerm_linux_virtual_machine
    -> "compute_instance").
    """
    if record.cloud is None:
        raise ValueError(f"{record.resource_address}: cannot normalize a resource with no cloud set")

    tags = from_raw_tags(record.raw_tags, record.cloud)
    confidence = tag_confidence(tags)  # noqa: F841 (used once canonical-type mapping lands below)

    raise NotImplementedError(
        "canonical resource-type mapping is not yet implemented; "
        f"tag extraction above is functional (resolved confidence={confidence!r})"
    )


def run(records: list[TerraformResourceRecord]) -> list[NormalizedResource]:
    """Normalize every record from stage 1. See `normalize_resource` for the per-record logic."""
    gcp_lookup = GcpLabelLookup()
    return [normalize_resource(r, gcp_lookup) for r in records]
