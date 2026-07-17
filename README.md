# PKI MM Integrations

Documentation and tools for integrating the [PKI Maturity Model](https://pkic.org/wg/pkimm/model/)
with third-party platforms. Rendered at https://pkic.org/wg/pkimm/integrations/.

Integrations vary: some ship a converter that generates an import artifact (e.g. Eramba produces
a CSV), others may be documentation-only or use a different format or tool entirely.

- `integrations.yaml` — manifest of available integrations: clean general metadata only
  (`id, name, type, status, compatibility, documentation, summary`). It says nothing about
  generated artifacts — regeneration/parity for integrations that produce a checked-in file (like
  Eramba) is handled internally by `scripts/check_integrations.py`'s builder registry, not by any
  manifest field.
- `<id>/_index.md` — hand-authored description + import instructions (always present), including
  links to any downloads the integration produces.
- `<id>/` may also contain integration-specific tools/artifacts. For example, Eramba's converter
  generates `eramba/pkimm-<ver>.csv` (regenerated and parity-checked); this is specific to Eramba,
  not a requirement of every integration.
- `pkimm-model/` — vendored, pinned copies of the pkimm model data per version.

## Developing

    pip install -r scripts/requirements-dev.txt
    python -m scripts.generate_integrations_docs   # regenerate the integrations table
    pytest scripts/ -q                             # unit tests
    python -m scripts.check_integrations           # full validation (CI gate)

Integrations that ship a converter regenerate their own artifact with that integration's
tool. For example, Eramba: `python -m scripts.eramba_convert` (writes `eramba/pkimm-<ver>.csv`).
