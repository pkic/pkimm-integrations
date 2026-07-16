import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_matches_schema():
    schema = json.loads((ROOT / "integrations.schema-1.0.0.json").read_text())
    data = yaml.safe_load((ROOT / "integrations.yaml").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=str)
    assert errors == [], [e.message for e in errors]
