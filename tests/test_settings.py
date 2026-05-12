import importlib

import pytest


def test_settings_exports_config_yaml_values(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu
collection:
  initial_collect_count: 11
selection:
  top_n: 4
wechat:
  account_crawl:
    accounts:
      - 账号A
    max_results_per_account: 2
    time_range_hours:
      min: 0
      max: 72
    browser_mode: auto
xiaohongshu:
  keyword_search:
    keywords:
      - 小红书词
    max_results_per_keyword: 3
    time_range_hours:
      min: 0
      max: 36
zhihu:
  keyword_search:
    keywords:
      - 知乎词
    max_results_per_keyword: 5
output:
  dir: ./tmp-output
  longxia_candidate_export_enabled: false
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    import config.settings as settings

    settings = importlib.reload(settings)

    assert settings.ENABLED_SOURCES == ["wechat_mp", "xiaohongshu", "zhihu"]
    assert settings.INITIAL_COLLECT_COUNT == 11
    assert settings.TOP_N_SELECT_COUNT == 4
    assert settings.WECHAT_MP_ACCOUNTS == ["账号A"]
    assert settings.WECHAT_MP_BROWSER_MODE == "auto"
    assert settings.WECHAT_ACCOUNT_TIME_RANGE_HOURS == (0, 72)
    assert settings.XIAOHONGSHU_SEARCH_KEYWORDS == ["小红书词"]
    assert settings.XIAOHONGSHU_KEYWORD_TIME_RANGE_HOURS == (0, 36)
    assert settings.ZHIHU_MAX_RESULTS_PER_KEYWORD == 5
    assert settings.LLM_MODEL == "test-model"
    assert settings.LONGXIA_CANDIDATE_EXPORT_ENABLED is False


def test_settings_warns_when_migrated_env_key_is_set(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu
wechat:
  account_crawl:
    accounts:
      - 账号A
xiaohongshu:
  keyword_search:
    keywords:
      - 小红书词
zhihu:
  keyword_search:
    keywords:
      - 知乎词
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("ENABLED_SOURCES", "demo")
    monkeypatch.setenv("WECHAT_MP_HEADLESS", "true")

    with pytest.warns(RuntimeWarning, match="moved to config.yaml") as warnings:
        import config.settings as settings

        settings = importlib.reload(settings)

    message = str(warnings[0].message)
    assert "ENABLED_SOURCES" in message
    assert "WECHAT_MP_HEADLESS" in message
    assert settings.ENABLED_SOURCES == ["wechat_mp", "xiaohongshu", "zhihu"]


def test_settings_exports_log_rotation_env_values(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
wechat:
  account_crawl:
    accounts:
      - 账号A
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("LOG_ROTATION", "1 day")
    monkeypatch.setenv("LOG_RETENTION", "14 days")
    monkeypatch.setenv("LOG_COMPRESSION", "zip")

    import config.settings as settings

    settings = importlib.reload(settings)

    assert settings.LOG_ROTATION == "1 day"
    assert settings.LOG_RETENTION == "14 days"
    assert settings.LOG_COMPRESSION == "zip"


def test_settings_does_not_default_private_remote_targets(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
wechat:
  account_crawl:
    accounts:
      - 账号A
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.delenv("LONGXIA_SSH_TARGET", raising=False)
    monkeypatch.delenv("LONGXIA_REMOTE_CANDIDATE_ROOT", raising=False)

    import config.settings as settings

    settings = importlib.reload(settings)

    assert settings.LONGXIA_SSH_TARGET == ""
    assert settings.LONGXIA_REMOTE_CANDIDATE_ROOT == ""


def test_settings_exports_new_search_source_values(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat
  - xiaohongshu
  - zhihu
  - google_news
wechat:
  keyword_search:
    keywords:
      - 微信词
    max_results_per_keyword: 3
    time_range_hours:
      min: 0
      max: 24
    use_playwright: false
    fetch_detail_page: true
  account_crawl:
    accounts:
      - 账号A
    max_results_per_account: 2
    time_range_hours:
      min: 0
      max: 96
xiaohongshu:
  keyword_search:
    keywords:
      - 小红书词
    max_results_per_keyword: 4
    time_range_hours:
      min: 0
      max: 48
  account_crawl:
    creator_urls:
      - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
    max_results_per_account: 5
    time_range_hours:
      min: 0
      max: 168
zhihu:
  keyword_search:
    keywords:
      - 知乎词
    max_results_per_keyword: 6
    time_range_hours:
      min: 0
      max: 72
  account_crawl:
    creator_urls:
      - https://www.zhihu.com/people/yd1234567
    max_results_per_account: 7
    time_range_hours:
      min: 0
      max: 120
google_news:
  keywords:
    - 通用词
  max_results_per_keyword: 8
  period: 24h
  language: zh-CN
  country: CN
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("GOOGLE_NEWS_PROXY_URL", "http://127.0.0.1:9899")

    import config.settings as settings

    settings = importlib.reload(settings)

    assert settings.ENABLED_SOURCES == [
        "wechat",
        "xiaohongshu",
        "zhihu",
        "google_news",
    ]
    assert settings.WECHAT_SEARCH_KEYWORDS == ["微信词"]
    assert settings.WECHAT_MAX_RESULTS_PER_KEYWORD == 3
    assert settings.WECHAT_KEYWORD_TIME_RANGE_HOURS == (0, 24)
    assert settings.WECHAT_ACCOUNT_TIME_RANGE_HOURS == (0, 96)
    assert settings.WECHAT_USE_PLAYWRIGHT is False
    assert settings.WECHAT_FETCH_DETAIL_PAGE is True
    assert settings.XIAOHONGSHU_CREATOR_URLS[0].startswith(
        "https://www.xiaohongshu.com/user/profile/"
    )
    assert settings.XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT == 5
    assert settings.XIAOHONGSHU_ACCOUNT_TIME_RANGE_HOURS == (0, 168)
    assert settings.ZHIHU_CREATOR_URLS == ["https://www.zhihu.com/people/yd1234567"]
    assert settings.ZHIHU_MAX_RESULTS_PER_ACCOUNT == 7
    assert settings.ZHIHU_ACCOUNT_TIME_RANGE_HOURS == (0, 120)
    assert settings.get_source_creator_urls("xiaohongshu")[0].startswith(
        "https://www.xiaohongshu.com/user/profile/"
    )
    assert settings.get_source_creator_urls("zhihu") == [
        "https://www.zhihu.com/people/yd1234567"
    ]
    assert settings.GOOGLE_NEWS_KEYWORDS == ["通用词"]
    assert settings.GOOGLE_NEWS_PERIOD == "24h"
    assert settings.GOOGLE_NEWS_PROXY_URL == "http://127.0.0.1:9899"
