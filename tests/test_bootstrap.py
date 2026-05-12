from pathlib import Path
import sys

from scripts import bootstrap
from scripts.bootstrap import (
    command_to_text,
    has_login_state,
    node_major_version,
    run_warning_command,
    validate_app_config,
    venv_command_target,
)


def test_node_major_version_parses_v_prefix():
    assert node_major_version("v20.11.1") == 20


def test_node_major_version_rejects_invalid_text():
    assert node_major_version("not-node") is None


def test_command_to_text_quotes_arguments():
    assert command_to_text([sys.executable, "-m", "pip", "install"]) == (
        f"{sys.executable} -m pip install"
    )


def test_venv_command_target_reads_created_venv_path():
    target = venv_command_target(
        "/usr/bin/python3 -m venv /Users/neo/Projects/AITrend/.venv"
    )

    assert target == Path("/Users/neo/Projects/AITrend/.venv")


def test_validate_app_config_reports_missing_dependencies(monkeypatch, capsys):
    monkeypatch.setattr(
        bootstrap,
        "missing_config_validation_modules",
        lambda: ["PyYAML"],
    )

    assert validate_app_config() is False

    output = capsys.readouterr().out
    assert "config validation dependencies are missing: PyYAML" in output
    assert "python scripts/bootstrap.py" in output


def test_run_warning_command_does_not_fail_on_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(bootstrap, "run_command", lambda command, check: 1)

    assert (
        run_warning_command(["python", "-m", "pip", "check"], False, "pip conflict")
        is False
    )

    assert "WARN: pip conflict (exit code 1)" in capsys.readouterr().out


def test_bootstrap_runtime_dirs_include_configured_trendcrawler_path(
    tmp_path,
    monkeypatch,
):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
wechat:
  account_crawl:
    accounts:
      - 账号A
trend_crawler_runtime:
  dir: ./third_party/TrendCrawlerRuntime
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))

    paths = bootstrap.runtime_dirs_from_config()

    assert "third_party/TrendCrawlerRuntime/browser_data" in paths
    assert "third_party/TrendCrawlerRuntime/data" in paths


def test_has_login_state_requires_non_empty_file_or_directory(tmp_path):
    missing = tmp_path / "missing"
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("", encoding="utf-8")
    state_file = tmp_path / "state.json"
    state_file.write_text("{}", encoding="utf-8")
    state_dir = tmp_path / "state_dir"
    state_dir.mkdir()
    (state_dir / "profile").write_text("cookie", encoding="utf-8")

    assert has_login_state(missing) is False
    assert has_login_state(empty_dir) is False
    assert has_login_state(empty_file) is False
    assert has_login_state(state_file) is True
    assert has_login_state(state_dir) is True
