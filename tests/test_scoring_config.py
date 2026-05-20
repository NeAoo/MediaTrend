from datetime import datetime
from pathlib import Path

from config.app_config import load_app_config
from models.hotspot import EducationHotspot
from scorers.scorer import render_scoring_prompt


def test_scoring_config_loads_from_yaml(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
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
scoring:
  enabled: false
  base_url: https://api.openai.com/v1
  model: gpt-5.4
  timeout_seconds: 120
  max_retries: 1
  max_completion_tokens: 0
  reasoning_effort: ""
  workers: 5
  parse_failure_score: 1.0
  random_fallback_on_all_parse_failures: true
  prompt:
    system_path: ./prompts/scoring_system_prompt.md
    user_path: ./prompts/scoring_user_prompt.md
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.scoring.enabled is False
    assert config.scoring.model == "gpt-5.4"
    assert config.scoring.prompt.system_path == "./prompts/scoring_system_prompt.md"


def test_expected_minimum_defaults_to_three(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
collection:
  initial_collect_count: 30
  time_range_hours: {min: 0, max: 24}
selection:
  top_n: 10
xiaohongshu:
  keyword_search:
    keywords: ["英语启蒙"]
    max_results_per_keyword: 10
    time_range_hours: {min: 0, max: 168}
  account_crawl:
    creator_urls: []
    max_results_per_account: 10
    time_range_hours: {min: 0, max: 168}
  login_type: qrcode
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.xiaohongshu.keyword_search.expected_min_results == 3
    assert config.xiaohongshu.account_crawl.expected_min_results == 3


def test_scoring_prompt_renderer_preserves_json_braces():
    template = """请返回 JSON:
{
  "overall": 8.5,
  "reason": "demo"
}

标题: {title}
正文: {content}
"""
    hotspot = EducationHotspot(
        title="测试标题",
        source="aihot",
        publish_time=datetime(2026, 5, 20, 9, 30),
        content="测试正文",
        url="https://example.com/a",
    )

    rendered = render_scoring_prompt(template, hotspot)

    assert '"overall": 8.5' in rendered
    assert "标题: 测试标题" in rendered
    assert "正文: 测试正文" in rendered
