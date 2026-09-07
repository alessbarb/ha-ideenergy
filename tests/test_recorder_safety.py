"""Regression checks for the statistics-only recorder architecture."""

import json
from pathlib import Path

INTEGRATION_ROOT = Path("custom_components/ideenergy")
FORBIDDEN_RECORDER_INTERNALS = (
    "homeassistant.components.recorder.db_schema",
    "homeassistant.components.recorder.core",
    "homeassistant.components.recorder.util",
    "sqlalchemy",
    "statistics_meta",
)


def test_integration_does_not_access_recorder_database_internals():
    """Keep historical imports on Home Assistant's public statistics API path."""
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in INTEGRATION_ROOT.rglob("*.py")
    ).lower()

    for forbidden in FORBIDDEN_RECORDER_INTERNALS:
        assert forbidden.lower() not in sources


def test_historical_sensor_dependency_is_statistics_only_generation():
    """Pin the historical helper generation that removed direct state writes."""
    manifest = json.loads(
        (INTEGRATION_ROOT / "manifest.json").read_text(encoding="utf-8")
    )

    assert "homeassistant-historical-sensor==3.0.0a4" in manifest["requirements"]
