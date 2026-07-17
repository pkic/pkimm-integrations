#!/usr/bin/env python3
"""Build Eramba-importable CSV packages from the vendored pkimm model.

Importable and deterministic: reads vendored pkimm-model/<version>/ resolved
from the repo root (derived from __file__), returns CSV text, and writes the
committed artifacts under eramba/. Reproduces the CSVs previously produced in
the pkimm repo byte-for-byte."""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path

import jsonschema
import pandas as pd
import yaml

VERSIONS = ("1.0.0", "2.0.0")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _clean_markdown_links(ref: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", ref)


def _resolve_reference_ids(ref_ids, ref_by_id) -> str:
    if not ref_ids:
        return ""
    return "\n".join(f"- {ref_by_id[r]['title']}" if r in ref_by_id else f"- {r}" for r in ref_ids)


def build_csv_text(root: Path, version: str) -> str:
    vend = root / "pkimm-model" / version
    data = yaml.safe_load((vend / f"pkimm-model-{version}.yaml").read_text())
    if str(data.get("version")) != version:
        raise ValueError(f"Vendored model {version} declares version {data.get('version')!r}")
    schema = json.loads((vend / f"pkimm-model.schema-{version}.json").read_text())
    jsonschema.validate(data, schema)

    ref_by_id = {}
    refs_path = vend / "pkimm-references.yaml"
    if refs_path.exists():
        ref_by_id = {r["id"]: r for r in (yaml.safe_load(refs_path.read_text()) or {}).get("references", [])}

    chapters, items = [], []
    for module in data.get("modules", []):
        module_id = module.get("id", "")
        for category in module.get("categories", []):
            chapter_id = f"{module_id}.{category.get('id', '')}"
            chapters.append([chapter_id, category.get("name", ""), category.get("description", "")])
            for req in category.get("requirements", []):
                item_id = f"{chapter_id}.{req.get('id', '')}"
                assessment = req.get("assessment", "")
                references = req.get("references", "")
                if version == "1.0.0":
                    refs_text = _clean_markdown_links(references if isinstance(references, str) else "")
                else:
                    refs_text = _resolve_reference_ids(references if isinstance(references, list) else [], ref_by_id)
                info = f"Assessment\n{assessment}\nReferences\n{refs_text}"
                items.append([item_id, req.get("description", ""), req.get("guidance", ""), info])

    chapters_df = pd.DataFrame(chapters, columns=["Chapter ID", "Chapter Name", "Chapter Description"])
    items_df = pd.DataFrame(items, columns=["Item ID", "Item Name", "Item Description", "Item Additional Information"])
    items_df["Chapter ID"] = items_df["Item ID"].apply(lambda x: ".".join(x.split(".")[:-1]))
    result_df = pd.merge(chapters_df, items_df, on="Chapter ID")
    result_df.drop_duplicates(inplace=True)
    return result_df.to_csv(index=False, header=False, lineterminator="\n",
                            quoting=csv.QUOTE_MINIMAL, doublequote=True, na_rep="")


def write_all(root: Path | None = None) -> None:
    root = root or _repo_root()
    for v in VERSIONS:
        (root / "eramba" / f"pkimm-{v}.csv").write_text(build_csv_text(root, v))


if __name__ == "__main__":
    write_all()
