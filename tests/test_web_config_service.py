from pathlib import Path

import pytest

from web.backend.config_service import ConfigWriteError, read_yaml_config, write_validated_config
from web.backend.env_service import mask_secret


def test_write_validated_config_creates_backup(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
enabled_sources:
  - aihot
collection:
  initial_collect_count: 30
  time_range_hours: {min: 0, max: 24}
selection:
  top_n: 10
aihot:
  mode: selected
  keywords: []
  categories: []
  max_results_per_query: 10
  base_url: https://aihot.virxact.com
  request_timeout_seconds: 10
  user_agent: test-agent
""",
        encoding="utf-8",
    )
    data = read_yaml_config(config_path)
    data["scoring"] = {"enabled": False}

    write_validated_config(config_path, data)

    backups = list(tmp_path.glob("config.yaml.bak.*"))
    assert backups
    assert "scoring:" in config_path.read_text(encoding="utf-8")


def test_invalid_config_does_not_overwrite_existing_file(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    original = "enabled_sources: [wechat]\n"
    config_path.write_text(original, encoding="utf-8")

    with pytest.raises(ConfigWriteError):
        write_validated_config(config_path, {"enabled_sources": ["wechat"]})

    assert config_path.read_text(encoding="utf-8") == original


def test_mask_secret_hides_middle_characters():
    assert mask_secret("sk-1234567890") == "sk-1••••••7890"
    assert mask_secret("") == ""
