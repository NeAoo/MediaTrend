# Migration-Friendly Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a clean clone runnable after copying `.env` and `config.yaml`, running one setup command, and scanning platform QR codes once on the new machine.

**Architecture:** Add a typed `config.yaml` loader as the source of truth for business settings, keep `.env` for secrets and machine-specific overrides, and preserve `config/settings.py` as a compatibility facade for existing imports. Add a stdlib-first bootstrap script that installs/checks dependencies, validates config, creates runtime directories, and reports login state without requiring portable browser state.

**Tech Stack:** Python 3.10+, Pydantic, PyYAML, python-dotenv, Playwright, TrendCrawlerRuntime, pytest.

---

## File Map

- Create: `config/app_config.py`
  Typed Pydantic models, YAML loading, project-root-relative path resolution, source validation.
- Create: `config.yaml.example`
  Copyable structured business config for `wechat_mp`, `xiaohongshu`, and `zhihu`.
- Modify: `config/settings.py`
  Load `.env` plus `config.yaml`, expose existing constants from typed config.
- Modify: `crawlers/wechat_mp.py`
  Add `auto` browser behavior so a missing or invalid login state opens visibly for QR login.
- Modify: `formatters/markdown.py`
  Use configurable filename pattern from settings.
- Create: `scripts/bootstrap.py`
  Fresh-clone setup and doctor command; stdlib-only until dependencies are installed.
- Modify: `.env.example`
  Keep secrets and machine-local overrides; remove routine business lists/counts.
- Modify: `.gitignore`
  Ignore root `config.yaml`.
- Modify: `requirements.txt`
  Include test dependency and align versions so root + TrendCrawlerRuntime installation is predictable.
- Modify: `README.md`
  Document the new migration flow and source naming.
- Create: `tests/test_app_config.py`
  Config loader unit tests.
- Create: `tests/test_settings.py`
  Compatibility facade tests.
- Create: `tests/test_wechat_mp_browser_mode.py`
  WeChat MP auto/visible/headless browser mode tests.
- Create: `tests/test_bootstrap.py`
  Bootstrap dry-run helper tests.

## Task 1: Add Config Loader Tests

**Files:**
- Create: `tests/test_app_config.py`

- [ ] **Step 1: Write failing tests for valid config loading**

```python
from pathlib import Path

from config.app_config import load_app_config


def test_load_app_config_reads_business_config(tmp_path, monkeypatch):
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
```

- [ ] **Step 2: Write failing tests for validation**

```python
import pytest

from config.app_config import ConfigValidationError, load_app_config


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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_app_config.py -q`
Expected: FAIL because `config.app_config` does not exist.

## Task 2: Implement Typed Config Models

**Files:**
- Create: `config/app_config.py`
- Create: `config.yaml.example`
- Modify: `.gitignore`

- [ ] **Step 1: Implement `config/app_config.py`**

```python
"""Typed application configuration loaded from config.yaml."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SOURCES = {"wechat_mp", "xiaohongshu", "zhihu"}
LoginType = Literal["qrcode", "cookie", "phone"]
BrowserMode = Literal["auto", "visible", "headless"]


class ConfigValidationError(ValueError):
    """Raised when config.yaml is missing or invalid."""


class TimeRangeConfig(BaseModel):
    min: int = Field(0, ge=0)
    max: int = Field(24, ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> "TimeRangeConfig":
        if self.max < self.min:
            raise ValueError("time_range_hours.max must be >= min")
        return self


class CollectionConfig(BaseModel):
    initial_collect_count: int = Field(30, ge=1)
    time_range_hours: TimeRangeConfig = Field(default_factory=TimeRangeConfig)


class SelectionConfig(BaseModel):
    top_n: int = Field(10, ge=1)


class RhythmConfig(BaseModel):
    slow_mo_ms: int = Field(300, ge=0)
    action_delay_seconds: float = Field(1.5, ge=0)
    article_delay_seconds: float = Field(3.0, ge=0)
    page_delay_seconds: float = Field(4.0, ge=0)
    account_delay_seconds: float = Field(8.0, ge=0)


class WechatMpConfig(BaseModel):
    accounts: list[str] = Field(default_factory=list)
    max_articles_per_account: int = Field(10, ge=1)
    lookback_days: int = Field(7, ge=1)
    login_timeout_seconds: int = Field(180, ge=30)
    browser_mode: BrowserMode = "auto"
    fetch_detail_page: bool = True
    raw_output_dir: str = "./raw_data/wechat_mp"
    storage_state: str = "./browser_data/wechat_mp_state.json"
    rhythm: RhythmConfig = Field(default_factory=RhythmConfig)


class TrendCrawlerRuntimeConfig(BaseModel):
    dir: str = "./TrendCrawlerRuntime"
    python_bin: str = ""
    timeout_seconds: int = Field(900, ge=60)
    max_notes_count: int = Field(20, ge=1)
    login_type: LoginType = "qrcode"


class KeywordSourceConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results_per_keyword: int = Field(20, ge=1)
    login_type: LoginType = "qrcode"


class OutputConfig(BaseModel):
    dir: str = "./output"
    filename_pattern: str = "教育热点日报_{date}.md"
    longxia_candidate_export_enabled: bool = False
    longxia_candidate_export_dir: str = "./output/longxia_trend_candidates"
    longxia_candidate_content_max_chars: int = Field(5000, ge=500)
    longxia_candidate_timezone: str = "Asia/Shanghai"


class AppConfig(BaseModel):
    enabled_sources: list[str] = Field(
        default_factory=lambda: ["wechat_mp", "xiaohongshu", "zhihu"]
    )
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    wechat_mp: WechatMpConfig = Field(default_factory=WechatMpConfig)
    trend_crawler_runtime: TrendCrawlerRuntimeConfig = Field(default_factory=TrendCrawlerRuntimeConfig)
    xiaohongshu: KeywordSourceConfig = Field(default_factory=KeywordSourceConfig)
    zhihu: KeywordSourceConfig = Field(default_factory=KeywordSourceConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def validate_enabled_sources_have_inputs(self) -> "AppConfig":
        unsupported = [
            source for source in self.enabled_sources if source not in SUPPORTED_SOURCES
        ]
        if unsupported:
            raise ValueError(
                "Unsupported source names: "
                f"{', '.join(unsupported)}. Supported sources: "
                f"{', '.join(sorted(SUPPORTED_SOURCES))}"
            )
        if "wechat_mp" in self.enabled_sources and not self.wechat_mp.accounts:
            raise ValueError("wechat_mp enabled but wechat_mp.accounts is empty")
        if "xiaohongshu" in self.enabled_sources and not self.xiaohongshu.keywords:
            raise ValueError("xiaohongshu enabled but xiaohongshu.keywords is empty")
        if "zhihu" in self.enabled_sources and not self.zhihu.keywords:
            raise ValueError("zhihu enabled but zhihu.keywords is empty")
        return self

    def resolve_path(self, value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else PROJECT_ROOT / path


def load_app_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    if not config_path.exists():
        raise ConfigValidationError(f"Config file does not exist: {config_path}")

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigValidationError(f"Config root must be a mapping: {config_path}")

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc
    except ValueError as exc:
        raise ConfigValidationError(str(exc)) from exc
```

- [ ] **Step 2: Add `config.yaml.example`**

```yaml
# Copy to config.yaml and edit. config.yaml is ignored by git.

enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu

collection:
  initial_collect_count: 30
  time_range_hours:
    min: 0
    max: 24

selection:
  top_n: 10

wechat_mp:
  accounts:
    - 中国教育报
    - 人民教育
  max_articles_per_account: 10
  lookback_days: 7
  login_timeout_seconds: 180
  browser_mode: auto
  fetch_detail_page: true
  raw_output_dir: ./raw_data/wechat_mp
  storage_state: ./browser_data/wechat_mp_state.json
  rhythm:
    slow_mo_ms: 300
    action_delay_seconds: 1.5
    article_delay_seconds: 3.0
    page_delay_seconds: 4.0
    account_delay_seconds: 8.0

trend_crawler_runtime:
  dir: ./TrendCrawlerRuntime
  python_bin: ""
  timeout_seconds: 900
  max_notes_count: 20
  login_type: qrcode

xiaohongshu:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  login_type: qrcode

zhihu:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  login_type: qrcode

output:
  dir: ./output
  filename_pattern: 教育热点日报_{date}.md
  longxia_candidate_export_enabled: false
  longxia_candidate_export_dir: ./output/longxia_trend_candidates
  longxia_candidate_content_max_chars: 5000
  longxia_candidate_timezone: Asia/Shanghai
```

- [ ] **Step 3: Ignore local `config.yaml`**

Add this line under the `.env` ignore rule in `.gitignore`:

```gitignore
config.yaml
```

- [ ] **Step 4: Run config tests**

Run: `python -m pytest tests/test_app_config.py -q`
Expected: PASS.

## Task 3: Wire Settings Facade

**Files:**
- Create: `tests/test_settings.py`
- Modify: `config/settings.py`
- Modify: `.env.example`

- [ ] **Step 1: Write settings facade tests**

```python
import importlib


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
```

- [ ] **Step 2: Replace business env parsing in `config/settings.py`**

Keep `_env_bool`, `_env_int`, `_env_float`, and `load_dotenv()`, then load typed config:

```python
CONFIG_PATH = os.getenv("AI_TREND_CONFIG", "config.yaml").strip() or "config.yaml"
APP_CONFIG = load_app_config(CONFIG_PATH)
```

Map constants from `APP_CONFIG`:

```python
ENABLED_SOURCES = APP_CONFIG.enabled_sources
INITIAL_COLLECT_COUNT = APP_CONFIG.collection.initial_collect_count
TOP_N_SELECT_COUNT = APP_CONFIG.selection.top_n
TIME_RANGE_MIN = APP_CONFIG.collection.time_range_hours.min
TIME_RANGE_MAX = APP_CONFIG.collection.time_range_hours.max

WECHAT_MP_ACCOUNTS = APP_CONFIG.wechat_mp.accounts
WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT = APP_CONFIG.wechat_mp.max_articles_per_account
WECHAT_MP_LOOKBACK_DAYS = APP_CONFIG.wechat_mp.lookback_days
WECHAT_MP_LOGIN_TIMEOUT_SECONDS = APP_CONFIG.wechat_mp.login_timeout_seconds
WECHAT_MP_BROWSER_MODE = APP_CONFIG.wechat_mp.browser_mode
WECHAT_MP_HEADLESS = WECHAT_MP_BROWSER_MODE == "headless"
WECHAT_MP_FETCH_DETAIL_PAGE = APP_CONFIG.wechat_mp.fetch_detail_page
WECHAT_MP_SLOW_MO_MS = APP_CONFIG.wechat_mp.rhythm.slow_mo_ms
WECHAT_MP_ACTION_DELAY_SECONDS = APP_CONFIG.wechat_mp.rhythm.action_delay_seconds
WECHAT_MP_ARTICLE_DELAY_SECONDS = APP_CONFIG.wechat_mp.rhythm.article_delay_seconds
WECHAT_MP_PAGE_DELAY_SECONDS = APP_CONFIG.wechat_mp.rhythm.page_delay_seconds
WECHAT_MP_ACCOUNT_DELAY_SECONDS = APP_CONFIG.wechat_mp.rhythm.account_delay_seconds
WECHAT_MP_RAW_OUTPUT_DIR = str(APP_CONFIG.resolve_path(APP_CONFIG.wechat_mp.raw_output_dir))
WECHAT_MP_STORAGE_STATE = str(APP_CONFIG.resolve_path(APP_CONFIG.wechat_mp.storage_state))

TREND_CRAWLER_RUNTIME_DIR = APP_CONFIG.resolve_path(APP_CONFIG.trend_crawler_runtime.dir)
TREND_CRAWLER_RUNTIME_PYTHON_BIN = (
    os.getenv("TREND_CRAWLER_RUNTIME_PYTHON_BIN", "").strip()
    or APP_CONFIG.trend_crawler_runtime.python_bin
    or sys.executable
)
TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT = APP_CONFIG.trend_crawler_runtime.max_notes_count
TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS = APP_CONFIG.trend_crawler_runtime.timeout_seconds
TREND_CRAWLER_RUNTIME_LOGIN_TYPE = APP_CONFIG.trend_crawler_runtime.login_type

XIAOHONGSHU_LOGIN_TYPE = APP_CONFIG.xiaohongshu.login_type
XIAOHONGSHU_SEARCH_KEYWORDS = APP_CONFIG.xiaohongshu.keywords
XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD = APP_CONFIG.xiaohongshu.max_results_per_keyword
XIAOHONGSHU_COOKIE = os.getenv("XIAOHONGSHU_COOKIE", "").strip()

ZHIHU_LOGIN_TYPE = APP_CONFIG.zhihu.login_type
ZHIHU_SEARCH_KEYWORDS = APP_CONFIG.zhihu.keywords
ZHIHU_MAX_RESULTS_PER_KEYWORD = APP_CONFIG.zhihu.max_results_per_keyword
ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "").strip()

OUTPUT_DIR = str(APP_CONFIG.resolve_path(APP_CONFIG.output.dir))
OUTPUT_FILENAME_PATTERN = APP_CONFIG.output.filename_pattern
LONGXIA_CANDIDATE_EXPORT_ENABLED = APP_CONFIG.output.longxia_candidate_export_enabled
LONGXIA_CANDIDATE_EXPORT_DIR = str(APP_CONFIG.resolve_path(APP_CONFIG.output.longxia_candidate_export_dir))
LONGXIA_CANDIDATE_CONTENT_MAX_CHARS = APP_CONFIG.output.longxia_candidate_content_max_chars
LONGXIA_CANDIDATE_TIMEZONE = APP_CONFIG.output.longxia_candidate_timezone
```

Keep LLM values in `.env`:

```python
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4").strip() or "gpt-5.4"
```

- [ ] **Step 3: Simplify `.env.example`**

Keep these sections:

```env
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.4
LLM_TIMEOUT_SECONDS=120
LLM_MAX_RETRIES=1
LLM_MAX_COMPLETION_TOKENS=
LLM_REASONING_EFFORT=
SCORE_WORKERS=5
SCORING_PARSE_FAILURE_SCORE=1
SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES=true

# Optional: use a non-default config file.
AI_TREND_CONFIG=config.yaml

# Optional cookie login for advanced users. Default config uses qrcode.
XIAOHONGSHU_COOKIE=
ZHIHU_COOKIE=

LOG_LEVEL=INFO
LOG_FILE=./logs/agent.log
```

- [ ] **Step 4: Run settings tests**

Run: `python -m pytest tests/test_settings.py -q`
Expected: PASS.

## Task 4: Add WeChat MP Auto Login Mode

**Files:**
- Create: `tests/test_wechat_mp_browser_mode.py`
- Modify: `crawlers/wechat_mp.py`

- [ ] **Step 1: Write browser mode tests**

```python
from pathlib import Path

from crawlers.wechat_mp import resolve_wechat_mp_headless


def test_auto_mode_is_visible_without_storage(tmp_path):
    assert resolve_wechat_mp_headless("auto", tmp_path / "missing.json") is False


def test_auto_mode_is_headless_with_storage(tmp_path):
    state = tmp_path / "state.json"
    state.write_text("{}", encoding="utf-8")
    assert resolve_wechat_mp_headless("auto", state) is True


def test_visible_and_headless_modes_are_explicit(tmp_path):
    state = tmp_path / "state.json"
    assert resolve_wechat_mp_headless("visible", state) is False
    assert resolve_wechat_mp_headless("headless", state) is True
```

- [ ] **Step 2: Add resolver and import `WECHAT_MP_BROWSER_MODE`**

In `crawlers/wechat_mp.py`, import `WECHAT_MP_BROWSER_MODE` and add:

```python
def resolve_wechat_mp_headless(browser_mode: str, storage_state_path: Path) -> bool:
    if browser_mode == "visible":
        return False
    if browser_mode == "headless":
        return True
    return storage_state_path.exists()
```

- [ ] **Step 3: Split launch into a retryable helper**

Refactor `collect()` so it calls a helper:

```python
headless = resolve_wechat_mp_headless(WECHAT_MP_BROWSER_MODE, self.storage_state_path)
session_result = self._collect_with_browser(headless=headless, accounts=accounts)
if (
    not session_result.items
    and session_result.error_messages
    and headless
    and WECHAT_MP_BROWSER_MODE == "auto"
):
    logger.warning("微信公众平台登录态不可用，切换为可见浏览器重新扫码")
    session_result = self._collect_with_browser(headless=False, accounts=accounts)
return session_result
```

The helper should contain the existing Playwright launch/login/account loop and use its `headless` argument instead of `WECHAT_MP_HEADLESS`.

- [ ] **Step 4: Run browser mode tests**

Run: `python -m pytest tests/test_wechat_mp_browser_mode.py -q`
Expected: PASS.

## Task 5: Use Configured Markdown Filename and Disable Longxia by Default

**Files:**
- Modify: `formatters/markdown.py`
- Modify: `main.py`

- [ ] **Step 1: Update Markdown filename generation**

Import `OUTPUT_FILENAME_PATTERN` from settings and change `generate_daily_report()`:

```python
filename = OUTPUT_FILENAME_PATTERN.format(
    date=date.strftime("%Y%m%d"),
    datetime=date.strftime("%Y%m%d_%H%M%S"),
)
```

- [ ] **Step 2: Keep longxia code but rely on config default**

No deletion is needed in `main.py`. Confirm it already checks:

```python
if LONGXIA_CANDIDATE_EXPORT_ENABLED:
    ...
```

Because `config.yaml.example` sets `longxia_candidate_export_enabled: false`, normal runs produce only the local Markdown report.

- [ ] **Step 3: Run import smoke check**

Run: `python - <<'PY'\nfrom formatters.markdown import MarkdownGenerator\nprint(MarkdownGenerator)\nPY`
Expected: prints `<class 'formatters.markdown.MarkdownGenerator'>`.

## Task 6: Add Bootstrap Script

**Files:**
- Create: `tests/test_bootstrap.py`
- Create: `scripts/bootstrap.py`

- [ ] **Step 1: Write tests for bootstrap helpers**

```python
import sys

from scripts.bootstrap import command_to_text, node_major_version


def test_node_major_version_parses_v_prefix():
    assert node_major_version("v20.11.1") == 20


def test_node_major_version_rejects_invalid_text():
    assert node_major_version("not-node") is None


def test_command_to_text_quotes_arguments():
    assert command_to_text([sys.executable, "-m", "pip", "install"]) == (
        f"{sys.executable} -m pip install"
    )
```

- [ ] **Step 2: Implement stdlib-first bootstrap**

`scripts/bootstrap.py` should contain:

```python
#!/usr/bin/env python3
"""Set up and validate an AITrend checkout."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = [
    "browser_data",
    "raw_data",
    "merged_data",
    "scored_data",
    "output",
    "logs",
    "TrendCrawlerRuntime/browser_data",
    "TrendCrawlerRuntime/data",
]


def command_to_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run_command(command: list[str], check: bool) -> int:
    print(f"$ {command_to_text(command)}")
    if check:
        return 0
    return subprocess.call(command, cwd=PROJECT_ROOT)


def node_major_version(raw: str) -> int | None:
    text = raw.strip()
    if text.startswith("v"):
        text = text[1:]
    major = text.split(".", 1)[0]
    return int(major) if major.isdigit() else None


def check_node() -> bool:
    node = shutil.which("node")
    if not node:
        print("WARN: Node.js not found. Zhihu/TrendCrawlerRuntime may fail; install Node.js >= 16.")
        return False
    completed = subprocess.run([node, "--version"], capture_output=True, text=True)
    major = node_major_version(completed.stdout)
    if major is None or major < 16:
        print(f"WARN: Node.js >= 16 required, detected: {completed.stdout.strip()}")
        return False
    print(f"OK: Node.js {completed.stdout.strip()}")
    return True


def ensure_runtime_dirs() -> None:
    for item in RUNTIME_DIRS:
        path = PROJECT_ROOT / item
        path.mkdir(parents=True, exist_ok=True)
        print(f"OK: directory {item}")


def validate_required_files() -> bool:
    ok = True
    for name in [".env", "config.yaml"]:
        path = PROJECT_ROOT / name
        if path.exists():
            print(f"OK: found {name}")
        else:
            print(f"ERROR: missing {name}")
            ok = False
    return ok


def validate_app_config() -> bool:
    try:
        from config.app_config import load_app_config

        config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
    except Exception as exc:
        print(f"ERROR: config validation failed: {exc}")
        return False
    print(f"OK: enabled sources: {', '.join(config.enabled_sources)}")
    return True


def report_login_state() -> None:
    checks = [
        ("wechat_mp", PROJECT_ROOT / "browser_data" / "wechat_mp_state.json"),
        ("trendcrawler", PROJECT_ROOT / "TrendCrawlerRuntime" / "browser_data"),
    ]
    for label, path in checks:
        if path.exists():
            print(f"OK: {label} login state exists at {path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"INFO: {label} login state missing; first run will require QR login")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap AITrend local environment")
    parser.add_argument("--check", action="store_true", help="report actions without installing")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10+ required")
        return 1

    ensure_runtime_dirs()
    files_ok = validate_required_files()

    commands = [
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        [sys.executable, "-m", "pip", "install", "-r", "TrendCrawlerRuntime/requirements.txt"],
        [sys.executable, "-m", "playwright", "install", "chromium"],
    ]
    for command in commands:
        if run_command(command, check=args.check) != 0:
            return 1

    node_ok = check_node()
    config_ok = validate_app_config() if files_ok else False
    report_login_state()

    return 0 if files_ok and node_ok and config_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run bootstrap tests**

Run: `python -m pytest tests/test_bootstrap.py -q`
Expected: PASS.

- [ ] **Step 4: Run bootstrap check mode**

Run: `python scripts/bootstrap.py --check`
Expected: lists directories, required commands, Node status, config validation, and login-state info.

## Task 7: Normalize Requirements for Testing and Dual Install

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add pytest to root requirements**

Add:

```text
pytest==8.3.4
```

- [ ] **Step 2: Make root requirements compatible with TrendCrawlerRuntime**

Use versions that work after installing `TrendCrawlerRuntime/requirements.txt`:

```text
playwright==1.45.0
pydantic>=2.5.2,<3
python-dotenv>=1.0.1,<2
```

Keep existing root-only dependencies:

```text
APScheduler==3.11.2
beautifulsoup4==4.14.3
loguru==0.7.3
openai==2.32.0
requests==2.32.3
socksio==1.0.0
PyYAML==6.0.2
```

- [ ] **Step 3: Run dependency check**

Run: `python -m pip check`
Expected: `No broken requirements found.`

## Task 8: Update README for Migration Workflow

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace quick-start with migration-first setup**

Use this flow:

````markdown
## 快速迁移

```bash
git clone <repository_url>
cd AITrend
python -m venv .venv
source .venv/bin/activate
cp /old/AITrend/.env .env
cp /old/AITrend/config.yaml config.yaml
python scripts/bootstrap.py
python main.py run
```

新机器第一次运行会为 `wechat_mp`、`xiaohongshu`、`zhihu` 打开登录流程，按提示扫码即可。登录态保存在本机运行目录，不需要也不建议跨机器复制。
````

- [ ] **Step 2: Clarify source names**

Add:

```markdown
默认推荐的数据源是：

- `wechat_mp`：微信公众平台后台，按固定公众号账号采集。
- `xiaohongshu`：通过内置 TrendCrawlerRuntime 采集小红书搜索结果。
- `zhihu`：通过内置 TrendCrawlerRuntime 采集知乎搜索结果。

`wechat` 是旧的搜狗微信搜索源，不属于默认迁移路径。
```

- [ ] **Step 3: Document config ownership**

Add:

```markdown
`.env` 只放密钥和机器差异，例如 LLM API Key、模型、日志级别。
`config.yaml` 放业务配置，例如启用哪些源、公众号账号、关键词、数量、时间窗口和输出文件名。
```

## Task 9: Full Validation

**Files:**
- No new files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_wechat_mp_browser_mode.py tests/test_bootstrap.py -q
```

Expected: all tests PASS.

- [ ] **Step 2: Run bootstrap in check mode**

Run:

```bash
python scripts/bootstrap.py --check
```

Expected: prints install commands instead of running them, validates `.env` and `config.yaml`, and reports login-state status.

- [ ] **Step 3: Run import smoke test**

Run:

```bash
python - <<'PY'
from config.settings import ENABLED_SOURCES, LONGXIA_CANDIDATE_EXPORT_ENABLED
from main import parse_sources_arg
print(ENABLED_SOURCES)
print(LONGXIA_CANDIDATE_EXPORT_ENABLED)
print(parse_sources_arg(None))
PY
```

Expected:

```text
['wechat_mp', 'xiaohongshu', 'zhihu']
False
['wechat_mp', 'xiaohongshu', 'zhihu']
```

- [ ] **Step 4: Inspect Git diff**

Run:

```bash
git diff --stat
git diff -- config/settings.py config/app_config.py crawlers/wechat_mp.py scripts/bootstrap.py
```

Expected: changes are limited to migration-friendly config, setup, docs, and focused tests.
