from pathlib import Path

import scripts.eramba_convert as ec

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "scripts/tests/fixtures/eramba"


def test_build_matches_reference_fixture():
    # The refactored converter must reproduce pkimm's historical CSV byte-for-byte.
    for v in ec.VERSIONS:
        assert ec.build_csv_text(ROOT, v) == (FIX / f"pkimm-{v}.csv").read_text(), f"CSV drift for {v}"


def test_write_all_creates_files(tmp_path):
    import shutil
    for rel in [
        "pkimm-model/1.0.0/pkimm-model-1.0.0.yaml", "pkimm-model/1.0.0/pkimm-model.schema-1.0.0.json",
        "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml", "pkimm-model/2.0.0/pkimm-model.schema-2.0.0.json",
        "pkimm-model/2.0.0/pkimm-references.yaml",
    ]:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dst)
    (tmp_path / "eramba").mkdir()
    ec.write_all(tmp_path)
    assert (tmp_path / "eramba/pkimm-1.0.0.csv").exists()
    assert (tmp_path / "eramba/pkimm-2.0.0.csv").exists()
