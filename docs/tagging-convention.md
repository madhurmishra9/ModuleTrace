# Tagging Convention

ModuleTrace joins Terraform-managed resources to billing data by tag. Billing APIs can only
group/filter by tags actually present on a resource at cost-collection time, so this convention
must be enforced when resources are *created* (by the Terraform modules themselves) — ModuleTrace
can validate it after the fact, but cannot retroactively tag anything.

## Canonical keys

| Canonical key | Meaning | Example value |
|---|---|---|
| `moduletrace:module-source` | Terraform module source | `git::https://github.com/org/tf-modules//vpc` |
| `moduletrace:module-version` | Pinned version/ref | `2.3.1` |
| `moduletrace:workspace` | Owning workspace/state name | `prod-us-east-1-networking` |
| `moduletrace:team` | Owning team | `platform-infra` |
| `moduletrace:ttl` | Optional ephemeral expiry | `2026-08-01` or `72h` |

## Per-cloud realization

- **AWS tags** — case-sensitive, allow `:` `/` `.`, up to 128 chars key / 256 value. Keys are used
  as-is: `moduletrace:module-source`, etc.
- **Azure tags** — similar to AWS (colons allowed in tag names), 512-char value limit; tag *names*
  cannot contain `< > % & \ ?` or `/`, but `:` is fine, so keys are also used as-is.
- **GCP labels** — strictly lowercase, `[a-z0-9_-]` only, 63-char max for both key and value, no
  colons, no uppercase. This is the constraint that forces a different representation:
  - Keys are mangled by replacing `:` with `_`: `moduletrace_module_source`,
    `moduletrace_module_version`, `moduletrace_workspace`, `moduletrace_team`, `moduletrace_ttl`.
  - Values need sanitizing too: something like a git module-source URL cannot fit losslessly into
    63 lowercase chars. GCP-tagged resources carry a **shortened hash** of the real value (e.g.
    the first 8 hex chars of `sha256(value)`, lowercased, already charset-safe) instead of the
    literal source string.
  - This isn't limited to source URLs: a typical semver string like `2.3.1` also contains a `.`,
    which is outside the GCP label charset, so version values get hashed too whenever they contain
    a disallowed character — not just long/URL-shaped values.
  - Because the label alone can't carry the full value back, ModuleTrace's normalizer (stage 2)
    is responsible for maintaining a hash → original-value lookup table alongside the normalized
    resource records, so a GCP resource's `moduletrace_module_source` label can still be resolved
    back to the real module source string during rollup/reporting.
  - See `src/moduletrace/tagging/gcp_label_codec.py` for the encode/decode implementation.

## Enforcement is a process concern, not a ModuleTrace guarantee

ModuleTrace cannot enforce that modules apply these tags — it can only detect whether they did
(`NormalizedResource.tag_confidence: complete | partial | missing`, set in stage 2). The
recommended enforcement path for module authors:

- Set the tags/labels that are constant per-workspace (`workspace`, `team`) once via provider
  defaults: `default_tags` on the `aws` and `azurerm` providers, `default_labels` on the `google`
  provider, populated from workspace variables.
- For the two values that are module-instance-specific (`module-source`, `module-version`),
  every wrapper module should call a small shared `moduletrace-tags` child module that produces
  the correctly-sanitized-per-cloud tag/label map for that call site, e.g.:

  ```hcl
  module "tags" {
    source  = "git::https://github.com/org/tf-modules//moduletrace-tags"
    version = "1.0.0"

    module_source  = "git::https://github.com/org/tf-modules//vpc"
    module_version = "2.3.1"
  }

  resource "aws_vpc" "this" {
    # ...
    tags = module.tags.tags
  }
  ```

Resources without these tags are not treated as errors by ModuleTrace — they show up with
`tag_confidence: missing` or `partial`, and stage 5's risk-scoring auto-escalates cleanup
candidates missing a `team` tag to `risk_level: high`, since there's no clear owner to confirm
deletion is safe.
