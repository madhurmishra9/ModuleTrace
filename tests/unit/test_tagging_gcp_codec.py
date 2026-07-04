import pytest

from moduletrace.tagging.gcp_label_codec import (
    GcpLabelLookup,
    encode_gcp_label_value,
    is_hashed_gcp_label_value,
    sanitize_gcp_label_key,
)


def test_sanitize_gcp_label_key_mangles_colon():
    assert sanitize_gcp_label_key("moduletrace:module-source") == "moduletrace_module_source"


def test_sanitize_gcp_label_key_rejects_oversized_key():
    with pytest.raises(ValueError):
        sanitize_gcp_label_key("moduletrace:" + "x" * 100)


def test_short_lowercase_value_passes_through_unhashed():
    value = "platform-infra"
    encoded = encode_gcp_label_value(value)
    assert encoded == value
    assert not is_hashed_gcp_label_value(encoded)


def test_value_with_disallowed_chars_gets_hashed():
    value = "git::https://github.com/org/tf-modules//vpc"
    encoded = encode_gcp_label_value(value)
    assert is_hashed_gcp_label_value(encoded)
    assert encoded.startswith("h_")
    assert len(encoded) <= 63


def test_oversized_lowercase_value_gets_hashed():
    value = "a" * 100  # valid charset, but exceeds the 63-char limit
    encoded = encode_gcp_label_value(value)
    assert is_hashed_gcp_label_value(encoded)


def test_lookup_round_trip_resolves_hashed_value():
    lookup = GcpLabelLookup()
    original = "git::https://github.com/org/tf-modules//vpc"

    encoded = lookup.encode(original)

    assert lookup.resolve(encoded) == original


def test_lookup_resolve_passes_through_unhashed_values():
    lookup = GcpLabelLookup()
    original = "platform-infra"

    encoded = lookup.encode(original)

    assert encoded == original
    assert lookup.resolve(encoded) == original


def test_lookup_resolve_returns_none_for_unknown_hash():
    lookup = GcpLabelLookup()
    assert lookup.resolve("h_deadbeefdeadbeef") is None
