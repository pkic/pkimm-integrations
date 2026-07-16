from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_eramba_page_has_front_matter_and_downloads():
    text = (ROOT / "eramba/_index.md").read_text()
    assert "title: Eramba" in text
    assert "pkimm-2.0.0.csv" in text  # links to the generated package
    assert "pkimm-1.0.0.csv" in text
