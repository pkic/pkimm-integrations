---
# Not website content. This repository is mounted as Hugo content by pkic.org,
# so the file needs an explicit exclusion to stay unpublished.
build:
  render: never
  list: never
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

**Documentation and tools for integrating the PKI Maturity Model (PKIMM) with third-party platforms**, maintained by the PKI Consortium PKIMM working group. Integrations differ from one another: some ship a converter that packages the PKIMM model as an import-ready artifact for a specific platform (e.g. Eramba GRC produces a CSV), others may be documentation-only, or use a different format or tooling entirely. In every case the model's structure and content are not changed — only, where applicable, re-shaped into a target platform's import format. This repo holds each integration's editorial page plus whatever integration-specific tools/artifacts it needs; it is rendered at https://pkic.org/wg/pkimm/integrations/ as a submodule of the pkic.org site.

The PKIMM **model itself** (modules, categories, requirements, levels, and the references catalog) is defined and versioned in the separate **`pkimm`** repository. This repo vendors the pinned model data any converters read from. This separation lets integrations evolve and be re-generated on their own cadence without forcing a `pkimm` model release.

There is no application code beyond small Python authoring/conversion/validation scripts — only YAML manifests, per-integration content (docs, and where applicable generated artifacts), JSON Schema, and those scripts. Treat changes as content/data edits plus light tooling, not application development.

## Repository layout

- `README.md` — short repo overview and developer quick-start.
- `integrations.yaml` — machine-readable manifest of available integrations (source of truth for the landing-page table). Records common metadata for every integration — id, name, type, status, supported model versions, documentation link, summary. It is clean general metadata only: it says nothing about whether an integration generates a checked-in artifact — that's an internal checker concern (see `scripts/check_integrations.py` below).
- `integrations.schema-1.0.0.json` — JSON Schema for `integrations.yaml`, independently versioned. All properties (`id, name, type, status, compatibility, documentation, summary`) are required; `additionalProperties: false`.
- `_index.md` — **generated** landing page (the table of integrations). Do not edit by hand.
- `<id>/` — one folder per integration (folder name = integration `id`, kebab-case, e.g. `eramba`):
  - `<id>/_index.md` — **hand-authored** editorial overview (what the integration is, import instructions, status, caveats, and links to any downloads it produces). Always present, regardless of whether the integration ships any other artifact.
  - any integration-specific tools/artifacts it needs. For example, Eramba ships a CSV converter (`scripts/eramba_convert.py`) that generates `eramba/pkimm-<ver>.csv`, a generated import package for a given PKIMM model version — regenerated and parity-checked in CI, never hand-edited, via the checker's builder registry (`scripts/check_integrations.py`'s `BUILDERS`). Other integrations may be docs-only, or use a different format or tool entirely; there is no requirement that an integration produce a CSV, or any generated artifact at all. Each integration's downloads/artifacts, if any, are linked from its own `<id>/_index.md` page.
- `pkimm-model/` — vendored, pinned copies of the `pkimm` files converters read from:
  - `<model-version>/` — per model version, e.g. `1.0.0/`, `2.0.0/`: `pkimm-model-<ver>.yaml` and `pkimm-model.schema-<ver>.json`, plus `pkimm-references.yaml` for versions that have an independently-versioned references catalog (2.0.0 onward). No marker files — the directory name itself must equal the model YAML's own `version` field, and the checker enforces this.
- `scripts/` — authoring, conversion, and validation tooling:
  - `scripts/__init__.py`, `scripts/tests/__init__.py` — package markers.
  - `scripts/requirements-dev.txt` — pinned dev/CI dependencies (`PyYAML`, `jsonschema`, `pandas` pinned to an exact version since CSV byte-output can drift across pandas versions and generated CSVs are parity-checked, `pytest`, `check-jsonschema`).
  - `scripts/eramba_convert.py` — Eramba-specific converter: reads a vendored `pkimm-model/<ver>/` plus `pkimm-references.yaml` and writes `eramba/pkimm-<ver>.csv`. Other integrations, if they generate an artifact at all, would have their own converter here.
  - `scripts/generate_integrations_docs.py` — regenerates `_index.md` (the integrations table) from `integrations.yaml`.
  - `scripts/check_integrations.py` — the CI gate; validates `integrations.yaml` against its schema, manifest ↔ content parity (the authored `<id>/_index.md` page is always required), vendored-copy integrity (dir name equals model version), and generated-doc parity (regenerate-and-diff). Artifact regeneration/parity for integrations that generate a checked-in file (like Eramba) is driven entirely by the checker's own `BUILDERS` registry — a module-level dict mapping integration id to `(builder, output-path-template)` (currently just `eramba`, mapped to `(eramba_convert.build_csv_text, "eramba/pkimm-{version}.csv")`) — not by any manifest field. Integrations not in `BUILDERS` only get the page-existence check.
  - `scripts/tests/` — pytest unit tests for the above.
- `.github/workflows/` — CI: installs deps, runs `pytest`, runs `python -m scripts.check_integrations` on every PR and push to `main`.

## Authoring / regeneration workflow

`integrations.yaml` and the vendored `pkimm-model/` are the sources of truth; the root `_index.md`, and (for integrations that have one) an integration's generated artifact, are produced from them. Never hand-edit generated files.

To add a new model version to an existing integration, or to regenerate after a vendored model update:

1. **Vendor the model** — if targeting a new PKIMM model version, add `pkimm-model/<new-ver>/` with that version's `pkimm-model-<new-ver>.yaml`, `pkimm-model.schema-<new-ver>.json`, and (2.0.0+) `pkimm-references.yaml`, copied byte-for-byte from the `pkimm` repo.
2. **Convert** — if the integration has a converter registered in `scripts/check_integrations.BUILDERS`, run it (e.g. `python -m scripts.eramba_convert`) to regenerate its output artifact. Docs-only integrations skip this step.
3. **Regenerate docs** — run `python -m scripts.generate_integrations_docs` to rebuild the root `_index.md` table.
4. **Update the manifest** — add/update the integration's entry in `integrations.yaml` (supported versions, status, type).
5. **Validate** — run `python -m scripts.check_integrations`; it must report `0 error(s)` before committing.

CI runs the checker on every PR/push; a stale generated artifact (source changed but output/docs not regenerated) fails the build. Run steps 2–5 locally before pushing.

## Conventions

- All markdown uses Hugo-style YAML front matter (`date`, `title`, `weight`, `sideMenu`/`build` where relevant). Ordering is by `weight`.
- `CLAUDE.md` and `README.md` are not website content: pkic.org mounts this repository as Hugo content, so both carry `build: render: never` / `list: never` front matter to stay unpublished. Keep those blocks in place.
- **Status vocabulary** (kebab-case in YAML; title-case badge on the site): `under-development`, `release-candidate`, `stable`, `deprecated`.
- Integration `id` is a stable kebab-case string (`^[a-z][a-z0-9-]*$`). **Never rename an integration `id` once published** — the folder name, manifest entry, and any downstream links depend on it.
- Generated files (`_index.md`, and any integration's generated output artifact) are never hand-edited; the checker enforces this via regenerate-and-diff.

## Adding a new integration

1. Choose a stable kebab-case `id` (the target platform name, e.g. `eramba`).
2. Create `<id>/` with a hand-authored `<id>/_index.md` (overview, import instructions, status, caveats, and links to any downloads it produces). This is always required.
3. Add the integration's entry to `integrations.yaml` (id, name, type, status, supported model versions, documentation, summary) — every field is required; the manifest has no converter/output concept.
4. If (and only if) the integration generates a checked-in artifact: add a converter under `scripts/` that reads the relevant `pkimm-model/<ver>/` and writes its output file, and register it in `scripts/check_integrations.py`'s `BUILDERS` dict as `id: (builder, "output/path/template-{version}.ext")` so CI regenerates and diffs it for staleness.
5. Run the regenerate + validate steps above.

## Vendoring policy

- `pkimm-model/` holds pinned, byte-identical copies of the model YAML and schema (plus the references catalog for 2.0.0+) per PKIMM model version. CI never fetches these over the network.
- No marker files — the vendored directory name (e.g. `2.0.0/`) must equal the model YAML's own `version` field; the checker enforces this directly against the YAML content.
- Bumping to a new model version is a deliberate PR: add `pkimm-model/<new-ver>/` with that version's files, regenerate affected converters' CSVs, and update `integrations.yaml`.

## Contribution constraints

Contributions are governed by the PKI Consortium IPR Agreement (https://pkic.org/ipr/) and the PKIMM working group charter (https://pkic.org/wg/pkimm/charter/). Substantive changes (new integrations, changes to conversion logic that alter published import packages) are working-group decisions; editorial fixes, typos, and clarifications are routine.

- **Commits & PRs:** use a single plain description of what changed — no AI/co-author attribution, no test counts, no plan/follow-up references.
- Do not commit local agent/planning scaffolding; keep it gitignored.
- Pin GitHub Actions by full commit SHA with a version comment (e.g. `actions/checkout@<sha> #v6.0.2`).
