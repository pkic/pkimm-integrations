import shutil
from pathlib import Path

import pytest
import yaml

import scripts.check_integrations as ci
import scripts.eramba_convert as ec
import scripts.generate_integrations_docs as gen

REAL = Path(__file__).resolve().parents[2]
SEED = [
    "integrations.schema-1.0.0.json", "integrations.yaml", "eramba/_index.md",
    "pkimm-model/1.0.0/pkimm-model-1.0.0.yaml", "pkimm-model/1.0.0/pkimm-model.schema-1.0.0.json",
    "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml", "pkimm-model/2.0.0/pkimm-model.schema-2.0.0.json",
    "pkimm-model/2.0.0/pkimm-references.yaml",
    "scripts/__init__.py", "scripts/eramba_convert.py",
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel in SEED:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REAL / rel, dst)
    ec.write_all(tmp_path)      # produce eramba/*.csv
    gen.generate(tmp_path)      # produce _index.md
    return tmp_path


def _errors(repo):
    return [i.message for i in ci.check_all(repo) if i.severity == "error"]


def test_valid_repo_has_no_errors(repo):
    assert _errors(repo) == []


def test_missing_output_csv(repo):
    (repo / "eramba/pkimm-2.0.0.csv").unlink()
    assert any("pkimm-2.0.0.csv" in m for m in _errors(repo))


def test_stale_csv(repo):
    (repo / "eramba/pkimm-2.0.0.csv").write_text("tampered\n")
    assert any("csv" in m.lower() and "stale" in m.lower() for m in _errors(repo))


def test_check_vendored_integrity_isolated(repo):
    # Call _check_vendored_integrity directly so the assertion can't be
    # satisfied by an unrelated failure elsewhere (e.g. ec.build_csv_text's
    # own version guard tripping during CSV parity checks in check_all).
    p = repo / "pkimm-model/1.0.0/pkimm-model-1.0.0.yaml"
    m = yaml.safe_load(p.read_text())
    m["version"] = "9.9.9"
    p.write_text(yaml.safe_dump(m))
    msgs = [i.message for i in ci._check_vendored_integrity(repo)]
    assert any("1.0.0" in m and "9.9.9" in m for m in msgs), msgs


def test_schema_violation(repo):
    m = yaml.safe_load((repo / "integrations.yaml").read_text())
    m["integrations"][0]["status"] = "nonsense"
    (repo / "integrations.yaml").write_text(yaml.safe_dump(m))
    assert any("schema" in msg.lower() for msg in _errors(repo))


def test_duplicate_id(repo):
    m = yaml.safe_load((repo / "integrations.yaml").read_text())
    m["integrations"].append(dict(m["integrations"][0]))
    (repo / "integrations.yaml").write_text(yaml.safe_dump(m))
    assert any("duplicate" in msg.lower() for msg in _errors(repo))


def test_missing_page(repo):
    (repo / "eramba/_index.md").unlink()
    assert any("_index.md" in msg and "missing" in msg.lower() for msg in _errors(repo))


def test_stale_table(repo):
    (repo / "_index.md").write_text("---\ntitle: Integrations\n---\n\n# tampered\n")
    assert any("_index.md" in m or "stale" in m.lower() for m in _errors(repo))


def test_docs_only_integration_needs_no_csv(repo):
    # An integration with no converter/output (docs-only) must pass the
    # existence checks without any CSV/artifact requirement.
    m = yaml.safe_load((repo / "integrations.yaml").read_text())
    m["integrations"].append({
        "id": "example",
        "name": "Example",
        "type": "Docs",
        "status": "under-development",
        "compatibility": ["2.0.0"],
        "documentation": "https://pkic.org/wg/pkimm/integrations/example/",
        "summary": "Docs-only integration with no converter or generated artifact.",
    })
    (repo / "integrations.yaml").write_text(yaml.safe_dump(m))
    (repo / "example").mkdir()
    (repo / "example/_index.md").write_text("---\ntitle: Example\n---\n\nDocs-only integration.\n")
    # Regenerate the table so this new entry doesn't itself trigger a
    # stale-table error unrelated to what this test is checking.
    gen.generate(repo)
    errors = _errors(repo)
    assert not any(m.startswith("example:") for m in errors), errors
