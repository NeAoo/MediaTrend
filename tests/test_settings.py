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
wechat_mp:
  accounts:
    - 账号A
  max_articles_per_account: 2
  browser_mode: auto
xiaohongshu:
  keywords:
    - 小红书词
  max_results_per_keyword: 3
zhihu:
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
    assert settings.XIAOHONGSHU_SEARCH_KEYWORDS == ["小红书词"]
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
wechat_mp:
  accounts:
    - 账号A
xiaohongshu:
  keywords:
    - 小红书词
zhihu:
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
