#!/usr/bin/env python3
"""Validate pkimm-integrations: manifest schema, manifest↔content parity,
vendored integrity, CSV parity, and generated-table parity. Hermetic."""
from __future__ import annotations
import argparse
import dataclasses
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts import eramba_convert as ec
from scripts import generate_integrations_docs as gen

# Registry of integrations that ship a checked-in artifact whose bytes are
# reproducible from a builder function, mapped to (builder, output-path
# template). Only entries listed here get CSV/artifact staleness checks;
# everything else is docs-and-tools and only gets the authored-page check.
# The `eramba_convert` import above stays even though it's only referenced
# here — its presence guarantees the converter module exists.
BUILDERS = {"eramba": (ec.build_csv_text, "eramba/pkimm-{version}.csv")}


@dataclasses.dataclass
class Issue:
    severity: str
    message: str


def check_all(repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    mpath = repo_root / "integrations.yaml"
    if not mpath.exists():
        return [Issue("error", "integrations.yaml not found")]
    manifest = yaml.safe_load(mpath.read_text())

    schema = json.loads((repo_root / "integrations.schema-1.0.0.json").read_text())
    for e in sorted(Draft202012Validator(schema).iter_errors(manifest), key=str):
        issues.append(Issue("error", f"integrations.yaml: schema violation: {e.message}"))

    entries = manifest.get("integrations", [])
    ids = [e.get("id") for e in entries]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        issues.append(Issue("error", f"duplicate integration id '{dup}'"))

    for entry in entries:
        iid = entry.get("id", "?")
        if not (repo_root / iid / "_index.md").exists():
            issues.append(Issue("error", f"{iid}: authored page {iid}/_index.md missing"))

        if iid in BUILDERS:
            builder, tmpl = BUILDERS[iid]
            for ver in entry.get("compatibility", []):
                out = repo_root / tmpl.format(version=ver)
                if not out.exists():
                    issues.append(Issue("error", f"{iid}: output {out.relative_to(repo_root)} missing for {ver}"))
                    continue
                try:
                    expected = builder(repo_root, ver)
                except Exception as exc:  # vendored data problem surfaces here
                    issues.append(Issue("error", f"{iid}: converter failed for {ver}: {exc}"))
                    continue
                if out.read_text() != expected:
                    issues.append(Issue("error", f"{iid}: {out.name} is stale — re-run the converter"))

    issues += _check_vendored_integrity(repo_root)

    # generated-table parity
    root_index = repo_root / "_index.md"
    expected_table = gen.render_table(manifest, gen._existing_date(root_index))
    if not root_index.exists() or root_index.read_text() != expected_table:
        issues.append(Issue("error", "_index.md is stale — re-run generate_integrations_docs"))
    return issues


def _check_vendored_integrity(repo_root: Path) -> list[Issue]:
    out: list[Issue] = []
    base = repo_root / "pkimm-model"
    if not base.exists():
        return [Issue("error", "pkimm-model/ vendored dir missing")]
    for ver_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        ver = ver_dir.name
        model_yaml = ver_dir / f"pkimm-model-{ver}.yaml"
        if model_yaml.exists():
            actual = (yaml.safe_load(model_yaml.read_text()) or {}).get("version")
            if str(actual) != ver:
                out.append(Issue("error", f"pkimm-model/{ver}/ contains model version '{actual}' (expected '{ver}')"))
    return out


def _main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".")
    issues = check_all(Path(p.parse_args().repo_root).resolve())
    errors = [i for i in issues if i.severity == "error"]
    for i in issues:
        print(("ERROR  " if i.severity == "error" else "WARN   ") + i.message)
    print(f"\n{len(errors)} error(s), {len([i for i in issues if i.severity=='warning'])} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(_main())
