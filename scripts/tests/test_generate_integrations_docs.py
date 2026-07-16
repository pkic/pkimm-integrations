from pathlib import Path

import yaml

import scripts.generate_integrations_docs as g

ROOT = Path(__file__).resolve().parents[2]


def test_table_lists_eramba():
    manifest = yaml.safe_load((ROOT / "integrations.yaml").read_text())
    md = g.render_table(manifest)
    assert "title: Integrations" in md
    assert "sideMenu: true" in md
    assert "Eramba" in md
    assert "Stable" in md
    assert "1.0.0, 2.0.0" in md


def test_generate_idempotent(tmp_path):
    import shutil
    shutil.copy(ROOT / "integrations.yaml", tmp_path / "integrations.yaml")
    g.generate(tmp_path)
    first = (tmp_path / "_index.md").read_text()
    g.generate(tmp_path)
    assert (tmp_path / "_index.md").read_text() == first
