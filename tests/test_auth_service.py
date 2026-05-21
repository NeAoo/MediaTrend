from pathlib import Path
import sqlite3

from web.backend.auth_service import list_source_auth_states, source_auth_state


def test_no_login_source_is_always_not_required(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("enabled_sources:\n  - google_news\n", encoding="utf-8")

    state = source_auth_state("aihot", config_file)

    assert state["requires_login"] is False
    assert state["status"] == "not_required"
    assert state["label"] == "不需要登录"


def test_wechat_mp_state_file_marks_source_online(tmp_path: Path):
    storage_state = tmp_path / "browser_data" / "wechat_mp_state.json"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
enabled_sources:
  - google_news
wechat:
  account_crawl:
    storage_state: {storage_state}
""",
        encoding="utf-8",
    )

    assert source_auth_state("wechat_mp", config_file)["status"] == "offline"

    storage_state.parent.mkdir(parents=True)
    storage_state.write_text("{}", encoding="utf-8")

    assert source_auth_state("wechat_mp", config_file)["status"] == "online"


def test_trendcrawler_profile_marks_creator_source_online(tmp_path: Path):
    runtime_dir = tmp_path / "TrendCrawlerRuntime"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
enabled_sources:
  - google_news
trend_crawler_runtime:
  dir: {runtime_dir}
""",
        encoding="utf-8",
    )
    profile = runtime_dir / "browser_data" / "cdp_xhs_user_data_dir"

    assert source_auth_state("xiaohongshu", config_file)["status"] == "offline"

    profile.mkdir(parents=True)
    (profile / "profile-cookie").write_text("cookie", encoding="utf-8")

    assert source_auth_state("xiaohongshu", config_file)["status"] == "online"


def test_zhihu_profile_requires_z_c0_cookie(tmp_path: Path):
    runtime_dir = tmp_path / "TrendCrawlerRuntime"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
enabled_sources:
  - google_news
trend_crawler_runtime:
  dir: {runtime_dir}
""",
        encoding="utf-8",
    )
    profile = runtime_dir / "browser_data" / "cdp_zhihu_user_data_dir"

    profile.mkdir(parents=True)
    (profile / "profile-cache").write_text("not enough", encoding="utf-8")
    assert source_auth_state("zhihu", config_file)["status"] == "offline"

    cookie_db = profile / "Default" / "Cookies"
    cookie_db.parent.mkdir(parents=True)
    with sqlite3.connect(cookie_db) as connection:
        connection.execute(
            "create table cookies (host_key text, name text, value text, encrypted_value blob)"
        )
        connection.execute(
            "insert into cookies values (?, ?, ?, ?)",
            (".zhihu.com", "z_c0", "", b"encrypted"),
        )

    assert source_auth_state("zhihu", config_file)["status"] == "online"


def test_zhihu_cookie_config_marks_source_online(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - google_news
zhihu:
  login_type: cookie
""",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("ZHIHU_COOKIE=z_c0=abc; _xsrf=def\n", encoding="utf-8")

    state = source_auth_state("zhihu", config_file)

    assert state["status"] == "online"
    assert state["checked_by"] == "cookie"


def test_list_source_auth_states_contains_all_dashboard_sources(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("enabled_sources:\n  - google_news\n", encoding="utf-8")

    states = list_source_auth_states(config_file)

    assert {state["source"] for state in states} == {
        "xiaohongshu",
        "zhihu",
        "google_news",
        "aihot",
        "wechat",
        "wechat_mp",
    }
