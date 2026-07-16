#!/usr/bin/env python3
"""Generate the integrations table (root _index.md) from integrations.yaml.
Idempotent; preserves existing front-matter `date`."""
from __future__ import annotations
import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DATE_LINE_RE = re.compile(r"^date:\s*(.+)$", re.MULTILINE)
STATUS_BADGE = {
    "under-development": "Under development",
    "release-candidate": "Release candidate",
    "stable": "Stable",
    "deprecated": "Deprecated",
}


def _existing_date(path: Path) -> str | None:
    if not path.exists():
        return None
    m = FRONT_MATTER_RE.match(path.read_text())
    if not m:
        return None
    d = DATE_LINE_RE.search(m.group(1))
    return d.group(1).strip() if d else None


def _flatten(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def render_table(manifest: dict[str, Any], existing_date: str | None = None) -> str:
    date_val = existing_date or dt.date.today().isoformat() + "T00:00:00Z"
    lines = [
        "---", f"date: {date_val}", "title: Integrations", "weight: 1", "sideMenu: true", "---",
        "", "# Integrations", "",
        "Converters that package the PKI Maturity Model for third-party platforms.",
        "", "| Integration | Type | Status | Compatibility | Summary |",
        "|---|---|---|---|---|",
    ]
    for i in manifest.get("integrations", []):
        badge = STATUS_BADGE.get(i["status"], i["status"])
        compat = ", ".join(i.get("compatibility", []))
        lines.append(f"| [{_flatten(i['name'])}]({i['documentation']}) | {_flatten(i['type'])} | {badge} | {compat} | {_flatten(i['summary'])} |")
    lines.append("")
    return "\n".join(lines)


def generate(repo_root: Path) -> None:
    manifest = yaml.safe_load((repo_root / "integrations.yaml").read_text())
    root_index = repo_root / "_index.md"
    root_index.write_text(render_table(manifest, _existing_date(root_index)))


def _main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".")
    generate(Path(p.parse_args().repo_root).resolve())


if __name__ == "__main__":
    _main()
