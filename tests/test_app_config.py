import pytest

from config.app_config import ConfigValidationError, load_app_config


def test_load_app_config_reads_business_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu
collection:
  initial_collect_count: 12
  time_range_hours:
    min: 0
    max: 48
selection:
  top_n: 6
wechat_mp:
  accounts:
    - 中国教育报
  max_articles_per_account: 3
  lookback_days: 5
xiaohongshu:
  keywords:
    - 中考
  max_results_per_keyword: 9
zhihu:
  keywords:
    - 教育改革
  max_results_per_keyword: 7
output:
  dir: ./out
  filename_pattern: report_{date}.md
  longxia_candidate_export_enabled: false
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.enabled_sources == ["wechat_mp", "xiaohongshu", "zhihu"]
    assert config.collection.initial_collect_count == 12
    assert config.collection.time_range_hours.max == 48
    assert config.selection.top_n == 6
    assert config.wechat_mp.accounts == ["中国教育报"]
    assert config.xiaohongshu.keywords == ["中考"]
    assert config.zhihu.max_results_per_keyword == 7
    assert config.output.dir == "./out"
    assert config.output.filename_pattern == "report_{date}.md"
    assert config.output.longxia_candidate_export_enabled is False


def test_enabled_source_requires_configured_keywords(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
xiaohongshu:
  keywords: []
zhihu:
  keywords:
    - 教育
wechat_mp:
  accounts:
    - 人民教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="xiaohongshu.*keywords"):
        load_app_config(config_file)


def test_unknown_enabled_source_fails(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat
wechat_mp:
  accounts:
    - 人民教育
xiaohongshu:
  keywords:
    - 教育
zhihu:
  keywords:
    - 教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="Unsupported source"):
        load_app_config(config_file)
