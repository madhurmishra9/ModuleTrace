from moduletrace.schemas.normalized import ModuleTraceTags
from moduletrace.tagging.convention import from_raw_tags, tag_confidence, to_cloud_tags
from moduletrace.tagging.gcp_label_codec import GcpLabelLookup


def test_aws_round_trip():
    tags = ModuleTraceTags(
        module_source="git::https://github.com/org/tf-modules//vpc",
        module_version="2.3.1",
        workspace="prod-us-east-1-networking",
        team="platform-infra",
    )

    raw = to_cloud_tags(tags, "aws")
    recovered = from_raw_tags(raw, "aws")

    assert recovered == tags
    assert raw["moduletrace:module-version"] == "2.3.1"


def test_gcp_round_trip_uses_lookup_for_long_values():
    tags = ModuleTraceTags(
        module_source="git::https://github.com/org/tf-modules//vpc",
        module_version="2-3-1",  # GCP-charset-safe (dots, like colons, aren't allowed in labels)
        workspace="prod-us-east-1-networking",
        team="platform-infra",
    )
    lookup = GcpLabelLookup()

    raw = to_cloud_tags(tags, "gcp", gcp_lookup=lookup)

    assert raw["moduletrace_module_version"] == "2-3-1"  # charset-safe value passes through
    assert lookup.resolve(raw["moduletrace_module_source"]) == tags.module_source
    # module_version ("2.3.1") with a dot would also get hashed - verify that path too
    dotted = to_cloud_tags(
        ModuleTraceTags(module_version="2.3.1"), "gcp", gcp_lookup=lookup
    )
    assert lookup.resolve(dotted["moduletrace_module_version"]) == "2.3.1"


def test_tag_confidence_levels():
    assert tag_confidence(ModuleTraceTags()) == "missing"
    assert (
        tag_confidence(ModuleTraceTags(module_source="x", module_version="1", workspace="w", team="t"))
        == "complete"
    )
    assert tag_confidence(ModuleTraceTags(team="platform-infra")) == "partial"
