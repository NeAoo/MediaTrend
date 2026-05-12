# Search Source Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a migration-friendly search tool that supports WeChat keyword search, WeChat official account collection, Xiaohongshu keyword plus account collection, Zhihu keyword plus account collection, and Google News keyword search.

**Architecture:** Keep the existing `CrawlerManager -> EducationHotspot -> DataMerger -> scorer/report` pipeline. Extend config validation and source wrappers instead of adding a second scheduler. Prepare `TrendCrawlerRuntime` for external placement through configurable paths and bootstrap logic, but do not delete the runtime directory in this implementation pass.

**Tech Stack:** Python 3.10+, Pydantic v2, Playwright, TrendCrawlerRuntime subprocess wrappers, GNews, pytest.

---

## File Structure

- Modify `config/app_config.py`: define new config models and validation rules for `wechat`, `google_news`, and creator URLs.
- Modify `config/settings.py`: export new config values and stop treating the newly migrated env keys as active business config.
- Modify `crawlers/manager.py`: register `google_news` and keep `wechat` available through config validation.
- Modify `crawlers/wechat.py`: read Sogou WeChat behavior from `config.yaml` through settings.
- Modify `crawlers/xiaohongshu.py`: run TrendCrawlerRuntime search and creator modes, then load both output file patterns.
- Modify `crawlers/zhihu.py`: run TrendCrawlerRuntime search and creator modes, then load both output file patterns.
- Create `crawlers/google_news.py`: isolate Google News search and result normalization.
- Modify `TrendCrawlerRuntime/cmd_arg/arg.py`: map `--creator_id` to `ZHIHU_CREATOR_URL_LIST` for Zhihu creator mode.
- Modify `scripts/bootstrap.py`: create runtime directories from configured `trend_crawler_runtime.dir` and install TrendCrawlerRuntime requirements from that path.
- Modify `requirements.txt`: add `gnews`.
- Modify `config.yaml.example`, `.env.example`, and `README.md`: document the new source matrix and external TrendCrawlerRuntime path.
- Add or modify tests under `tests/`: config validation, settings exports, command construction, Google News parsing, and bootstrap path behavior.

## Task 0: Branch And Dirty Worktree Guard

**Files:**
- No source files changed in this task.

- [ ] **Step 1: Review current dirty files**

Run:

```bash
git status --short
```

Expected: the output may contain unrelated modified files such as `.env.example`, `README.md`, `main.py`, and weekly reference files. Do not revert them.

- [ ] **Step 2: Create the feature branch**

Run:

```bash
git switch -c codex/search-source-expansion
```

Expected: `Switched to a new branch 'codex/search-source-expansion'`.

If the branch already exists, run:

```bash
git switch codex/search-source-expansion
```

Expected: `Switched to branch 'codex/search-source-expansion'`.

## Task 1: Config Schema And Settings Exports

**Files:**
- Modify: `config/app_config.py`
- Modify: `config/settings.py`
- Modify: `tests/test_app_config.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Add failing config tests**

Append these tests to `tests/test_app_config.py`:

```python
def test_load_app_config_supports_keyword_and_creator_sources(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat
  - wechat_mp
  - xiaohongshu
  - zhihu
  - google_news
wechat:
  keywords:
    - 微信词
  max_results_per_keyword: 4
  use_playwright: false
  fetch_detail_page: true
wechat_mp:
  accounts:
    - 中国教育报
xiaohongshu:
  keywords:
    - 小红书词
  creator_urls:
    - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
  max_results_per_keyword: 8
  max_results_per_account: 6
zhihu:
  keywords:
    - 知乎词
  creator_urls:
    - https://www.zhihu.com/people/yd1234567
  max_results_per_keyword: 9
  max_results_per_account: 7
google_news:
  keywords:
    - 通用词
  max_results_per_keyword: 5
  period: 7d
  language: zh-CN
  country: CN
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.enabled_sources == [
        "wechat",
        "wechat_mp",
        "xiaohongshu",
        "zhihu",
        "google_news",
    ]
    assert config.wechat.keywords == ["微信词"]
    assert config.wechat.max_results_per_keyword == 4
    assert config.wechat.use_playwright is False
    assert config.wechat.fetch_detail_page is True
    assert config.xiaohongshu.creator_urls[0].startswith("https://www.xiaohongshu.com/user/profile/")
    assert config.xiaohongshu.max_results_per_account == 6
    assert config.zhihu.creator_urls == ["https://www.zhihu.com/people/yd1234567"]
    assert config.zhihu.max_results_per_account == 7
    assert config.google_news.keywords == ["通用词"]
    assert config.google_news.period == "7d"


def test_enabled_creator_source_accepts_empty_keywords_when_creator_urls_exist(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
  - zhihu
xiaohongshu:
  keywords: []
  creator_urls:
    - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
zhihu:
  keywords: []
  creator_urls:
    - https://www.zhihu.com/people/yd1234567
wechat_mp:
  accounts:
    - 人民教育
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.xiaohongshu.creator_urls
    assert config.zhihu.creator_urls


def test_google_news_requires_keywords_when_enabled(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - google_news
google_news:
  keywords: []
wechat_mp:
  accounts:
    - 人民教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="google_news.*keywords"):
        load_app_config(config_file)
```

- [ ] **Step 2: Run config tests and verify failure**

Run:

```bash
python -m pytest tests/test_app_config.py -q
```

Expected: failures mention unsupported sources or missing attributes such as `config.wechat`.

- [ ] **Step 3: Implement config models**

In `config/app_config.py`, update `SUPPORTED_SOURCES`:

```python
SUPPORTED_SOURCES = {"wechat", "wechat_mp", "xiaohongshu", "zhihu", "google_news"}
```

Add these models near the existing source config models:

```python
class WechatKeywordConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results_per_keyword: int = Field(8, ge=1)
    use_playwright: bool = True
    fetch_detail_page: bool = False


class CreatorKeywordSourceConfig(KeywordSourceConfig):
    creator_urls: list[str] = Field(default_factory=list)
    max_results_per_account: int = Field(20, ge=1)


class GoogleNewsConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results_per_keyword: int = Field(20, ge=1)
    period: str = "7d"
    language: str = "zh-CN"
    country: str = "CN"
```

Update `AppConfig` fields:

```python
    wechat: WechatKeywordConfig = Field(default_factory=WechatKeywordConfig)
    wechat_mp: WechatMpConfig = Field(default_factory=WechatMpConfig)
    trend_crawler_runtime: TrendCrawlerRuntimeConfig = Field(default_factory=TrendCrawlerRuntimeConfig)
    xiaohongshu: CreatorKeywordSourceConfig = Field(default_factory=CreatorKeywordSourceConfig)
    zhihu: CreatorKeywordSourceConfig = Field(default_factory=CreatorKeywordSourceConfig)
    google_news: GoogleNewsConfig = Field(default_factory=GoogleNewsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
```

Replace source input validation with:

```python
        if "wechat" in self.enabled_sources and not self.wechat.keywords:
            raise ValueError("wechat enabled but wechat.keywords is empty")
        if "wechat_mp" in self.enabled_sources and not self.wechat_mp.accounts:
            raise ValueError("wechat_mp enabled but wechat_mp.accounts is empty")
        if (
            "xiaohongshu" in self.enabled_sources
            and not self.xiaohongshu.keywords
            and not self.xiaohongshu.creator_urls
        ):
            raise ValueError(
                "xiaohongshu enabled but both xiaohongshu.keywords and "
                "xiaohongshu.creator_urls are empty"
            )
        if (
            "zhihu" in self.enabled_sources
            and not self.zhihu.keywords
            and not self.zhihu.creator_urls
        ):
            raise ValueError(
                "zhihu enabled but both zhihu.keywords and zhihu.creator_urls are empty"
            )
        if "google_news" in self.enabled_sources and not self.google_news.keywords:
            raise ValueError("google_news enabled but google_news.keywords is empty")
```

- [ ] **Step 4: Export settings**

In `config/settings.py`, add these keys to `MIGRATED_CONFIG_ENV_KEYS`:

```python
    "WECHAT_SEARCH_KEYWORDS",
    "WECHAT_MAX_RESULTS_PER_KEYWORD",
    "WECHAT_USE_PLAYWRIGHT",
    "WECHAT_FETCH_DETAIL_PAGE",
    "XIAOHONGSHU_CREATOR_URLS",
    "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT",
    "ZHIHU_CREATOR_URLS",
    "ZHIHU_MAX_RESULTS_PER_ACCOUNT",
    "GOOGLE_NEWS_KEYWORDS",
    "GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD",
    "GOOGLE_NEWS_PERIOD",
    "GOOGLE_NEWS_LANGUAGE",
    "GOOGLE_NEWS_COUNTRY",
```

Replace the legacy WeChat config exports with config-backed values:

```python
WECHAT_SEARCH_KEYWORDS = APP_CONFIG.wechat.keywords
SOGOU_WECHAT_COOKIE = os.getenv("SOGOU_WECHAT_COOKIE", "").strip()
WECHAT_MAX_RESULTS_PER_KEYWORD = APP_CONFIG.wechat.max_results_per_keyword
WECHAT_USE_PLAYWRIGHT = APP_CONFIG.wechat.use_playwright
WECHAT_FETCH_DETAIL_PAGE = APP_CONFIG.wechat.fetch_detail_page
```

Add creator and Google News exports below the current XHS/Zhihu keyword exports:

```python
XIAOHONGSHU_CREATOR_URLS = APP_CONFIG.xiaohongshu.creator_urls
XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT = APP_CONFIG.xiaohongshu.max_results_per_account

ZHIHU_CREATOR_URLS = APP_CONFIG.zhihu.creator_urls
ZHIHU_MAX_RESULTS_PER_ACCOUNT = APP_CONFIG.zhihu.max_results_per_account

GOOGLE_NEWS_KEYWORDS = APP_CONFIG.google_news.keywords
GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD = APP_CONFIG.google_news.max_results_per_keyword
GOOGLE_NEWS_PERIOD = APP_CONFIG.google_news.period
GOOGLE_NEWS_LANGUAGE = APP_CONFIG.google_news.language
GOOGLE_NEWS_COUNTRY = APP_CONFIG.google_news.country
GOOGLE_NEWS_PROXY_URL = os.getenv("GOOGLE_NEWS_PROXY_URL", "").strip()
```

Update `SOURCE_KEYWORDS` and `SOURCE_RESULT_LIMITS`:

```python
SOURCE_KEYWORDS = {
    "wechat": WECHAT_SEARCH_KEYWORDS,
    "wechat_mp": WECHAT_MP_ACCOUNTS,
    "xiaohongshu": XIAOHONGSHU_SEARCH_KEYWORDS,
    "zhihu": ZHIHU_SEARCH_KEYWORDS,
    "google_news": GOOGLE_NEWS_KEYWORDS,
    "general": GENERAL_SEARCH_KEYWORDS,
    "demo": [],
}

SOURCE_RESULT_LIMITS = {
    "wechat": WECHAT_MAX_RESULTS_PER_KEYWORD,
    "wechat_mp": WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
    "xiaohongshu": XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
    "zhihu": ZHIHU_MAX_RESULTS_PER_KEYWORD,
    "google_news": GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD,
    "general": GENERAL_MAX_LINKS_PER_SITE,
}
```

- [ ] **Step 5: Add settings export test**

Append this test to `tests/test_settings.py`:

```python
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
  keywords:
    - 微信词
  max_results_per_keyword: 3
  use_playwright: false
  fetch_detail_page: true
wechat_mp:
  accounts:
    - 账号A
xiaohongshu:
  keywords:
    - 小红书词
  creator_urls:
    - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
  max_results_per_keyword: 4
  max_results_per_account: 5
zhihu:
  keywords:
    - 知乎词
  creator_urls:
    - https://www.zhihu.com/people/yd1234567
  max_results_per_keyword: 6
  max_results_per_account: 7
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

    assert settings.ENABLED_SOURCES == ["wechat", "xiaohongshu", "zhihu", "google_news"]
    assert settings.WECHAT_SEARCH_KEYWORDS == ["微信词"]
    assert settings.WECHAT_USE_PLAYWRIGHT is False
    assert settings.WECHAT_FETCH_DETAIL_PAGE is True
    assert settings.XIAOHONGSHU_CREATOR_URLS[0].startswith("https://www.xiaohongshu.com/user/profile/")
    assert settings.XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT == 5
    assert settings.ZHIHU_CREATOR_URLS == ["https://www.zhihu.com/people/yd1234567"]
    assert settings.ZHIHU_MAX_RESULTS_PER_ACCOUNT == 7
    assert settings.GOOGLE_NEWS_KEYWORDS == ["通用词"]
    assert settings.GOOGLE_NEWS_PERIOD == "24h"
    assert settings.GOOGLE_NEWS_PROXY_URL == "http://127.0.0.1:9899"
```

- [ ] **Step 6: Run tests**

Run:

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py -q
```

Expected: all tests pass.

## Task 2: Manager Registration And Single Source Scripts

**Files:**
- Modify: `crawlers/manager.py`
- Create: `scripts/search_google_news.py`
- Modify: `scripts/search_common.py`

- [ ] **Step 1: Register Google News crawler**

In `crawlers/manager.py`, add `google_news` before `general`:

```python
CRAWLER_MAP = {
    "wechat": ("crawlers.wechat", "WechatCrawler"),
    "wechat_mp": ("crawlers.wechat_mp", "WechatMpCrawler"),
    "xiaohongshu": ("crawlers.xiaohongshu", "XiaohongshuCrawler"),
    "zhihu": ("crawlers.zhihu", "ZhihuCrawler"),
    "google_news": ("crawlers.google_news", "GoogleNewsCrawler"),
    "general": ("crawlers.general", "GeneralEducationCrawler"),
    "demo": ("crawlers.demo", "DemoEducationCrawler"),
}
```

- [ ] **Step 2: Create Google News single-source script**

Create `scripts/search_google_news.py`:

```python
#!/usr/bin/env python3
"""Run Google News keyword search only."""

from search_common import run_single_source_search


if __name__ == "__main__":
    raise SystemExit(run_single_source_search("google_news"))
```

- [ ] **Step 3: Clarify single source argument text**

In `scripts/search_common.py`, update the keyword help string to mention config-backed sources:

```python
            help="本次运行覆盖该搜索源的关键词，逗号分隔；不填则使用 config.yaml 配置",
```

- [ ] **Step 4: Run import smoke test**

Run:

```bash
python - <<'PY'
from crawlers.manager import AVAILABLE_SOURCES
assert "google_news" in AVAILABLE_SOURCES
assert "wechat" in AVAILABLE_SOURCES
print(",".join(AVAILABLE_SOURCES))
PY
```

Expected: output includes `wechat` and `google_news`.

## Task 3: Google News Crawler

**Files:**
- Create: `crawlers/google_news.py`
- Create: `tests/test_google_news_crawler.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependency**

Append to `requirements.txt`:

```text
gnews>=0.4.1,<1
```

- [ ] **Step 2: Add failing Google News tests**

Create `tests/test_google_news_crawler.py`:

```python
from datetime import datetime

from crawlers.google_news import GoogleNewsCrawler


def test_parse_item_uses_google_news_fields():
    crawler = GoogleNewsCrawler()
    raw = {
        "title": "教育改革新观察",
        "description": "这是一段摘要",
        "published date": "Sun, 10 May 2026 08:00:00 GMT",
        "url": "https://news.google.com/read/example",
        "publisher": {"title": "测试媒体"},
        "resolved_url": "https://example.com/article",
        "source_keyword": "教育改革",
    }

    item = crawler.parse_item(raw)

    assert item.title == "教育改革新观察"
    assert item.source == "google_news"
    assert item.author == "测试媒体"
    assert item.content == "这是一段摘要"
    assert item.url == "https://example.com/article"
    assert item.publish_time.year == 2026
    assert item.tags == ["教育", "Google News", "教育改革"]


def test_collect_uses_client_and_resolver(monkeypatch):
    crawler = GoogleNewsCrawler()
    calls = []

    class FakeClient:
        def __init__(self, language, country, period, max_results):
            calls.append((language, country, period, max_results))

        def get_news(self, keyword):
            return [
                {
                    "title": f"{keyword} 标题",
                    "description": "摘要",
                    "published date": "Sun, 10 May 2026 08:00:00 GMT",
                    "url": "https://news.google.com/read/example",
                    "publisher": {"title": "媒体"},
                }
            ]

    monkeypatch.setattr("crawlers.google_news.GNews", FakeClient)
    monkeypatch.setattr(
        crawler,
        "_resolve_google_news_url",
        lambda url: "https://example.com/resolved",
    )

    result = crawler.collect(["教育改革"], time_range_hours=(0, 48))

    assert calls == [("zh-CN", "CN", "7d", 20)]
    assert result.success_count == 1
    assert result.items[0].url == "https://example.com/resolved"
    assert isinstance(result.items[0].publish_time, datetime)
```

- [ ] **Step 3: Run test and verify failure**

Run:

```bash
python -m pytest tests/test_google_news_crawler.py -q
```

Expected: import failure because `crawlers.google_news` does not exist.

- [ ] **Step 4: Implement crawler**

Create `crawlers/google_news.py`:

```python
"""Google News keyword crawler."""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterator, List

import requests
from gnews import GNews
from loguru import logger

from config.settings import (
    GOOGLE_NEWS_COUNTRY,
    GOOGLE_NEWS_KEYWORDS,
    GOOGLE_NEWS_LANGUAGE,
    GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD,
    GOOGLE_NEWS_PERIOD,
    GOOGLE_NEWS_PROXY_URL,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


GOOGLE_NEWS_BATCH_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS = 15


class GoogleNewsCrawler(BaseCrawler):
    """Collect keyword results from Google News."""

    def __init__(self):
        super().__init__("google_news")

    def collect(
        self,
        keywords: List[str] | None = None,
        time_range_hours: tuple = (0, 24),
    ) -> CollectionResult:
        result = CollectionResult()
        selected_keywords = keywords or GOOGLE_NEWS_KEYWORDS
        if not selected_keywords:
            logger.warning("未配置 Google News 搜索关键词，无法采集")
            return result

        with self._proxy_env(GOOGLE_NEWS_PROXY_URL):
            client = GNews(
                language=GOOGLE_NEWS_LANGUAGE,
                country=GOOGLE_NEWS_COUNTRY,
                period=GOOGLE_NEWS_PERIOD,
                max_results=GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD,
            )
            for keyword in selected_keywords:
                try:
                    logger.info(f"正在搜索 Google News 关键词: {keyword}")
                    raw_items = client.get_news(keyword)
                    for raw_item in raw_items[:GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD]:
                        raw_item["source_keyword"] = keyword
                        raw_item["resolved_url"] = self._resolve_google_news_url(
                            raw_item.get("url", "")
                        )
                        hotspot = self.parse_item(raw_item)
                        if self.validate_time_range(
                            hotspot.publish_time,
                            time_range_hours[0],
                            time_range_hours[1],
                        ):
                            result.items.append(hotspot)
                            result.success_count += 1
                except Exception as exc:
                    logger.error(f"Google News 关键词 {keyword} 采集失败: {exc}")
                    result.error_messages.append(f"{keyword}: {exc}")

        result.items.sort(key=lambda item: item.publish_time, reverse=True)
        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        publish_time = self._parse_publish_time(raw_data.get("published date"))
        publisher = raw_data.get("publisher") or {}
        source_keyword = raw_data.get("source_keyword", "")
        tags = ["教育", "Google News"]
        if source_keyword:
            tags.append(source_keyword)
        return EducationHotspot(
            title=raw_data.get("title", "") or "无标题",
            source="google_news",
            author=publisher.get("title") if isinstance(publisher, dict) else None,
            publish_time=publish_time,
            content=raw_data.get("description", "") or "",
            url=raw_data.get("resolved_url") or raw_data.get("url", ""),
            popularity=None,
            cover_image=None,
            image_list=[],
            tags=tags,
        )

    def _parse_publish_time(self, value: str | None) -> datetime:
        if not value:
            return datetime.now()
        try:
            parsed = parsedate_to_datetime(value)
            return parsed.replace(tzinfo=None)
        except (TypeError, ValueError):
            logger.debug(f"Google News 时间解析失败，使用当前时间: {value}")
            return datetime.now()

    def _resolve_google_news_url(self, url: str) -> str:
        if not url or "news.google.com" not in url:
            return url
        params = self._get_google_params(url)
        if not params:
            return url
        resolved = self._get_origin_url(
            source=params["source"],
            sign=params["sign"],
            ts=params["ts"],
        )
        return resolved or url

    def _get_google_params(self, url: str) -> dict[str, str]:
        response = requests.get(url, timeout=GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        text = response.text
        sign = re.search(r'data-n-a-sg="([^"]+)"', text)
        ts = re.search(r'data-n-a-ts="([^"]+)"', text)
        source = re.search(r'data-n-a-id="([^"]+)"', text)
        if not sign or not ts or not source:
            return {}
        return {
            "sign": sign.group(1),
            "ts": ts.group(1),
            "source": source.group(1),
        }

    def _get_origin_url(self, source: str, sign: str, ts: str) -> str:
        payload = [
            "Fbv4je",
            f'["garturlreq",[[["zh-CN","CN",["FINANCE_TOP_INDICES","WEB_TEST_1_0_0"],null,null,1,1,"CN:zh-Hans",null,180,null,null,null,null,null,0,null,null,[1608992183,723341000]],"zh-CN","CN",1,[2,3,4,8],1,0,"655000234",0,0,null,0],"{source}",{ts},"{sign}"]',
        ]
        data = f"f.req={json.dumps([[payload]])}"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
        response = requests.post(
            GOOGLE_NEWS_BATCH_URL,
            headers=headers,
            data=data,
            timeout=GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        match = re.search(r'\[\\"wrb.fr\\",\\"Fbv4je\\",\\"(.*?)\\",null', response.text)
        if not match:
            return ""
        return json.loads(match.group(1))[1]

    @contextmanager
    def _proxy_env(self, proxy_url: str) -> Iterator[None]:
        if not proxy_url:
            yield
            return

        old_http = os.environ.get("http_proxy")
        old_https = os.environ.get("https_proxy")
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        try:
            yield
        finally:
            self._restore_env("http_proxy", old_http)
            self._restore_env("https_proxy", old_https)

    def _restore_env(self, key: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
```

- [ ] **Step 5: Run Google News tests**

Run:

```bash
python -m pytest tests/test_google_news_crawler.py -q
```

Expected: all tests pass.

## Task 4: Xiaohongshu Keyword Plus Creator Mode

**Files:**
- Modify: `crawlers/xiaohongshu.py`
- Create: `tests/test_xiaohongshu_crawler_modes.py`

- [ ] **Step 1: Add command construction tests**

Create `tests/test_xiaohongshu_crawler_modes.py`:

```python
import importlib


def test_xiaohongshu_runs_search_and_creator_modes(monkeypatch):
    module = importlib.import_module("crawlers.xiaohongshu")
    monkeypatch.setattr(module, "XIAOHONGSHU_CREATOR_URLS", ["https://www.xiaohongshu.com/user/profile/abc?xsec_token=token&xsec_source=pc_search"])
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD", 8)
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT", 6)
    monkeypatch.setattr(module, "XIAOHONGSHU_LOGIN_TYPE", "qrcode")
    monkeypatch.setattr(module, "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)

    crawler = module.XiaohongshuCrawler()
    commands = []

    def fake_run(mode, items, max_count, time_range_hours, timeout):
        commands.append((mode, items, max_count, time_range_hours, timeout))
        return True

    monkeypatch.setattr(crawler, "_run_trendcrawler", fake_run)
    monkeypatch.setattr(crawler, "_load_and_convert_data", lambda patterns: [])

    result = crawler.collect(["教育改革"], time_range_hours=(0, 24))

    assert result.success_count == 0
    assert commands == [
        ("search", ["教育改革"], 8, 24, 900),
        ("creator", ["https://www.xiaohongshu.com/user/profile/abc?xsec_token=token&xsec_source=pc_search"], 6, 24, 900),
    ]
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
python -m pytest tests/test_xiaohongshu_crawler_modes.py -q
```

Expected: failure because `_run_trendcrawler` does not exist and creator settings are not imported.

- [ ] **Step 3: Import creator settings**

In `crawlers/xiaohongshu.py`, add:

```python
    XIAOHONGSHU_CREATOR_URLS,
    XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT,
```

- [ ] **Step 4: Replace collect orchestration**

Inside `XiaohongshuCrawler.collect`, use this flow:

```python
        selected_keywords = keywords or []
        selected_creator_urls = XIAOHONGSHU_CREATOR_URLS
        if not selected_keywords and not selected_creator_urls:
            logger.warning("未配置小红书关键词或账号 URL，无法采集")
            return CollectionResult()

        max_hours = time_range_hours[1] if isinstance(time_range_hours, tuple) else time_range_hours
        result = CollectionResult()
        output_patterns: list[str] = []

        if selected_keywords:
            success = self._run_trendcrawler(
                mode="search",
                items=selected_keywords,
                max_count=XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
                time_range_hours=max_hours,
                timeout=TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
            )
            if success:
                output_patterns.append("search_contents_*.jsonl")
            else:
                result.error_messages.append("小红书关键词搜索执行失败或超时")

        if selected_creator_urls:
            success = self._run_trendcrawler(
                mode="creator",
                items=selected_creator_urls,
                max_count=XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT,
                time_range_hours=max_hours,
                timeout=TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
            )
            if success:
                output_patterns.append("creator_contents_*.jsonl")
            else:
                result.error_messages.append("小红书账号采集执行失败或超时")

        hotspots = self._load_and_convert_data(output_patterns)
        result.items = hotspots
        result.success_count = len(hotspots)
        logger.info(f"小红书采集完成，共 {len(hotspots)} 条内容，时间范围最近 {max_hours} 小时")
        return result
```

- [ ] **Step 5: Replace `_run_crawler` with mode-aware runner**

Rename `_run_crawler` to `_run_trendcrawler` and use this command construction:

```python
    def _run_trendcrawler(
        self,
        mode: str,
        items: List[str],
        max_count: int,
        time_range_hours: int,
        timeout: int = 900,
    ) -> bool:
        main_file = self.trendcrawler_dir / "main.py"
        if not main_file.exists():
            logger.error(f"TrendCrawlerRuntime 未找到: {main_file}")
            logger.error("请确认 config.yaml 中 trend_crawler_runtime.dir 指向有效的 TrendCrawlerRuntime 目录")
            return False

        login_type = XIAOHONGSHU_LOGIN_TYPE or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
        if login_type == "cookie" and not XIAOHONGSHU_COOKIE:
            logger.error("xiaohongshu.login_type=cookie 但未配置 XIAOHONGSHU_COOKIE")
            return False

        env = os.environ.copy()
        env["TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX"] = str(time_range_hours)
        env["TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT"] = str(max_count)
        cmd = [
            self.python_bin,
            "main.py",
            "--platform",
            "xhs",
            "--lt",
            login_type,
            "--type",
            mode,
        ]
        if mode == "search":
            keywords_str = ",".join(items)
            env["TREND_CRAWLER_RUNTIME_KEYWORDS"] = keywords_str
            cmd.extend(["--keywords", keywords_str])
        elif mode == "creator":
            cmd.extend(["--creator_id", ",".join(items)])
        else:
            logger.error(f"未知小红书采集模式: {mode}")
            return False

        if login_type == "cookie" and XIAOHONGSHU_COOKIE:
            cmd.extend(["--cookies", XIAOHONGSHU_COOKIE])

        try:
            logger.info(f"执行 TrendCrawlerRuntime 小红书 {mode}: {' '.join(cmd)}")
            completed = subprocess.run(
                cmd,
                cwd=self.trendcrawler_dir,
                env=env,
                capture_output=False,
                text=True,
                timeout=timeout,
            )
            if completed.returncode != 0:
                logger.error(f"TrendCrawlerRuntime 返回非 0 退出码: {completed.returncode}")
            return completed.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"小红书 {mode} 执行超时（{timeout / 60:.1f} 分钟）")
            return False
        except Exception as exc:
            logger.error(f"小红书 {mode} 执行异常: {exc}")
            return False
```

- [ ] **Step 6: Update loader to accept patterns**

Change `_load_and_convert_data` signature:

```python
    def _load_and_convert_data(self, patterns: List[str] | None = None) -> List[EducationHotspot]:
        jsonl_dir = self.trendcrawler_dir / "data" / "xhs" / "jsonl"
        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []

        selected_patterns = patterns or ["search_contents_*.jsonl"]
        jsonl_files = []
        for pattern in selected_patterns:
            jsonl_files.extend(jsonl_dir.glob(pattern))
        if not jsonl_files:
            logger.error(f"未找到小红书 JSONL 文件: {', '.join(selected_patterns)}")
            return []

        latest_files_by_pattern = []
        for pattern in selected_patterns:
            pattern_files = list(jsonl_dir.glob(pattern))
            if pattern_files:
                latest_files_by_pattern.append(max(pattern_files, key=lambda p: p.stat().st_mtime))

        hotspots = []
        for latest_file in latest_files_by_pattern:
            logger.info(f"使用小红书数据文件: {latest_file.name}")
            with open(latest_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_data = json.loads(line)
                        hotspots.append(self.parse_item(raw_data))
                    except json.JSONDecodeError as exc:
                        logger.warning(f"{latest_file.name} 第{line_num}行 JSON 解析失败: {exc}")
        logger.info(f"成功转换 {len(hotspots)} 条小红书数据")
        return hotspots
```

- [ ] **Step 7: Run XHS tests**

Run:

```bash
python -m pytest tests/test_xiaohongshu_crawler_modes.py -q
```

Expected: all tests pass.

## Task 5: Zhihu Keyword Plus Creator Mode

**Files:**
- Modify: `crawlers/zhihu.py`
- Modify: `TrendCrawlerRuntime/cmd_arg/arg.py`
- Create: `tests/test_zhihu_crawler_modes.py`
- Create: `tests/test_trendcrawler_arg_zhihu_creator.py`

- [ ] **Step 1: Add Zhihu wrapper test**

Create `tests/test_zhihu_crawler_modes.py`:

```python
import importlib


def test_zhihu_runs_search_and_creator_modes(monkeypatch):
    module = importlib.import_module("crawlers.zhihu")
    monkeypatch.setattr(module, "ZHIHU_CREATOR_URLS", ["https://www.zhihu.com/people/yd1234567"])
    monkeypatch.setattr(module, "ZHIHU_MAX_RESULTS_PER_KEYWORD", 8)
    monkeypatch.setattr(module, "ZHIHU_MAX_RESULTS_PER_ACCOUNT", 6)
    monkeypatch.setattr(module, "ZHIHU_LOGIN_TYPE", "qrcode")
    monkeypatch.setattr(module, "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)

    crawler = module.ZhihuCrawler()
    commands = []

    def fake_run(mode, items, max_count, time_range_hours, timeout):
        commands.append((mode, items, max_count, time_range_hours, timeout))
        return True

    monkeypatch.setattr(crawler, "_run_trendcrawler", fake_run)
    monkeypatch.setattr(crawler, "_load_and_convert_data", lambda patterns: [])

    result = crawler.collect(["教育改革"], time_range_hours=(0, 24))

    assert result.success_count == 0
    assert commands == [
        ("search", ["教育改革"], 8, 24, 900),
        ("creator", ["https://www.zhihu.com/people/yd1234567"], 6, 24, 900),
    ]
```

- [ ] **Step 2: Add TrendCrawlerRuntime CLI mapping test**

Create `tests/test_trendcrawler_arg_zhihu_creator.py`:

```python
import asyncio
import importlib
import sys
from pathlib import Path


def test_trendcrawler_maps_zhihu_creator_id(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    trendcrawler_root = project_root / "TrendCrawlerRuntime"
    monkeypatch.syspath_prepend(str(trendcrawler_root))

    arg_module = importlib.import_module("cmd_arg.arg")
    config = importlib.import_module("config")

    asyncio.run(
        arg_module.parse_cmd(
            [
                "--platform",
                "zhihu",
                "--lt",
                "qrcode",
                "--type",
                "creator",
                "--creator_id",
                "https://www.zhihu.com/people/yd1234567",
            ]
        )
    )

    assert config.ZHIHU_CREATOR_URL_LIST == ["https://www.zhihu.com/people/yd1234567"]
```

If importing `config` collides with the root project `config` package, isolate this test by removing already imported root config modules from `sys.modules` before the `monkeypatch.syspath_prepend` call:

```python
    for name in list(sys.modules):
        if name == "config" or name.startswith("config."):
            sys.modules.pop(name)
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
python -m pytest tests/test_zhihu_crawler_modes.py tests/test_trendcrawler_arg_zhihu_creator.py -q
```

Expected: Zhihu wrapper test fails on missing mode-aware runner; TrendCrawlerRuntime test fails because `ZHIHU_CREATOR_URL_LIST` is not assigned from `--creator_id`.

- [ ] **Step 4: Implement Zhihu wrapper mode flow**

Mirror the XHS changes in `crawlers/zhihu.py` with these platform-specific differences:

```python
cmd = [
    self.python_bin,
    "main.py",
    "--platform",
    "zhihu",
    "--lt",
    login_type,
    "--type",
    mode,
]
if mode == "search":
    keywords_str = ",".join(items)
    env["TREND_CRAWLER_RUNTIME_KEYWORDS"] = keywords_str
    cmd.extend(["--keywords", keywords_str])
elif mode == "creator":
    cmd.extend(["--creator_id", ",".join(items)])
else:
    logger.error(f"未知知乎采集模式: {mode}")
    return False
```

Load both patterns from `TrendCrawlerRuntime/data/zhihu/jsonl`:

```python
patterns = ["search_contents_*.jsonl", "creator_contents_*.jsonl"]
```

Keep `parse_item` unchanged unless tests show creator output uses different keys. If creator mode output lacks fields required by `parse_item`, add fallback reads for `desc`, `content`, `content_text`, `content_url`, `title`, `user_nickname`, `created_time`, and `updated_time` only.

- [ ] **Step 5: Patch TrendCrawlerRuntime Zhihu creator mapping**

In `TrendCrawlerRuntime/cmd_arg/arg.py`, inside the `if creator_id_list:` block, add:

```python
            elif platform == PlatformEnum.ZHIHU:
                config.ZHIHU_CREATOR_URL_LIST = creator_id_list
```

- [ ] **Step 6: Run Zhihu tests**

Run:

```bash
python -m pytest tests/test_zhihu_crawler_modes.py tests/test_trendcrawler_arg_zhihu_creator.py -q
```

Expected: all tests pass.

## Task 6: TrendCrawlerRuntime External Path Preparation

**Files:**
- Modify: `config.yaml.example`
- Modify: `scripts/bootstrap.py`
- Modify: `.gitignore`
- Modify: `tests/test_bootstrap.py`

- [ ] **Step 1: Add bootstrap path tests**

Open `tests/test_bootstrap.py` and add tests for runtime paths derived from config. Use existing test style in that file. Add this behavior:

```python
def test_bootstrap_runtime_dirs_include_configured_trendcrawler_path(tmp_path, monkeypatch):
    import importlib

    import scripts.bootstrap as bootstrap

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
wechat_mp:
  accounts:
    - 账号A
trend_crawler_runtime:
  dir: ./third_party/TrendCrawlerRuntime
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(bootstrap.PROJECT_ROOT)
    monkeypatch.setenv("AI_TREND_CONFIG", str(config_file))

    paths = bootstrap.runtime_dirs_from_config()

    assert "third_party/TrendCrawlerRuntime/browser_data" in paths
    assert "third_party/TrendCrawlerRuntime/data" in paths
```

- [ ] **Step 2: Run bootstrap test and verify failure**

Run:

```bash
python -m pytest tests/test_bootstrap.py -q
```

Expected: failure because `runtime_dirs_from_config` does not exist.

- [ ] **Step 3: Add external path helpers**

In `scripts/bootstrap.py`, replace the fixed `RUNTIME_DIRS` constant with:

```python
BASE_RUNTIME_DIRS = [
    "browser_data",
    "raw_data",
    "merged_data",
    "scored_data",
    "output",
    "logs",
]
```

Add:

```python
def runtime_dirs_from_config() -> list[str]:
    trend_crawler_runtime_dir = "TrendCrawlerRuntime"
    try:
        from config.app_config import load_app_config

        app_config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
        trend_crawler_runtime_path = app_config.resolve_path(app_config.trend_crawler_runtime.dir)
        if is_relative_to(trend_crawler_runtime_path.resolve(), PROJECT_ROOT.resolve()):
            trend_crawler_runtime_dir = str(trend_crawler_runtime_path.relative_to(PROJECT_ROOT))
        else:
            trend_crawler_runtime_dir = str(trend_crawler_runtime_path)
    except Exception:
        trend_crawler_runtime_dir = "TrendCrawlerRuntime"

    return BASE_RUNTIME_DIRS + [
        f"{trend_crawler_runtime_dir}/browser_data",
        f"{trend_crawler_runtime_dir}/data",
    ]
```

Update `ensure_runtime_dirs()`:

```python
def ensure_runtime_dirs() -> None:
    for item in runtime_dirs_from_config():
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        label = str(path.relative_to(PROJECT_ROOT)) if is_relative_to(path, PROJECT_ROOT) else str(path)
        print(f"OK: directory {label}")
```

Add:

```python
def trend_crawler_runtime_dir_from_config() -> Path:
    from config.app_config import load_app_config

    app_config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
    return app_config.resolve_path(app_config.trend_crawler_runtime.dir)
```

Update the TrendCrawlerRuntime install command in `main()`:

```python
    try:
        trend_crawler_runtime_dir = trend_crawler_runtime_dir_from_config()
    except Exception:
        trend_crawler_runtime_dir = PROJECT_ROOT / "TrendCrawlerRuntime"

    commands = [
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
    ]
    media_requirements = trend_crawler_runtime_dir / "requirements.txt"
    if media_requirements.exists():
        commands.append([sys.executable, "-m", "pip", "install", "-r", str(media_requirements)])
    else:
        print(f"WARN: TrendCrawlerRuntime requirements not found: {media_requirements}")
    commands.append([sys.executable, "-m", "playwright", "install", "chromium"])
```

Update `report_login_state()` to use `trend_crawler_runtime_dir_from_config()`:

```python
def report_login_state() -> None:
    try:
        trend_crawler_runtime_dir = trend_crawler_runtime_dir_from_config()
    except Exception:
        trend_crawler_runtime_dir = PROJECT_ROOT / "TrendCrawlerRuntime"
    checks = [
        ("wechat_mp", PROJECT_ROOT / "browser_data" / "wechat_mp_state.json"),
        ("trendcrawler", trend_crawler_runtime_dir / "browser_data"),
    ]
    for label, path in checks:
        if path.exists():
            display = path.relative_to(PROJECT_ROOT) if is_relative_to(path, PROJECT_ROOT) else path
            print(f"OK: {label} login state exists at {display}")
        else:
            print(f"INFO: {label} login state missing; first run will require QR login")
```

- [ ] **Step 4: Update gitignore**

Add:

```gitignore
# External third-party dependencies
third_party/
```

- [ ] **Step 5: Update config example path**

In `config.yaml.example`, set:

```yaml
trend_crawler_runtime:
  dir: ./third_party/TrendCrawlerRuntime
```

Keep the current embedded `TrendCrawlerRuntime/` directory in the repo during this task. Do not delete it in this execution pass.

- [ ] **Step 6: Run bootstrap tests**

Run:

```bash
python -m pytest tests/test_bootstrap.py -q
```

Expected: all tests pass.

## Task 7: Examples And Documentation

**Files:**
- Modify: `config.yaml.example`
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Update config example**

Set `enabled_sources` in `config.yaml.example`:

```yaml
enabled_sources:
  - wechat
  - wechat_mp
  - xiaohongshu
  - zhihu
  - google_news
```

Add:

```yaml
wechat:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 8
  use_playwright: true
  fetch_detail_page: false
```

Extend `xiaohongshu` and `zhihu`:

```yaml
xiaohongshu:
  keywords:
    - 教育改革
    - 中考
  creator_urls: []
  max_results_per_keyword: 20
  max_results_per_account: 20
  login_type: qrcode

zhihu:
  keywords:
    - 教育改革
    - 中考
  creator_urls: []
  max_results_per_keyword: 20
  max_results_per_account: 20
  login_type: qrcode
```

Add:

```yaml
google_news:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  period: 7d
  language: zh-CN
  country: CN
```

- [ ] **Step 2: Update env example**

In `.env.example`, add:

```env
SOGOU_WECHAT_COOKIE=
GOOGLE_NEWS_PROXY_URL=
TREND_CRAWLER_RUNTIME_PYTHON_BIN=
```

Keep `XIAOHONGSHU_COOKIE` and `ZHIHU_COOKIE`.

- [ ] **Step 3: Update README source matrix**

In `README.md`, replace the default source bullets with:

```markdown
推荐数据源：

- `wechat`：搜狗微信关键词搜索，按 `wechat.keywords` 采集公众号文章搜索结果。
- `wechat_mp`：微信公众平台后台，按 `wechat_mp.accounts` 固定公众号账号采集。
- `xiaohongshu`：通过 TrendCrawlerRuntime 支持关键词搜索和账号主页采集。
- `zhihu`：通过 TrendCrawlerRuntime 支持关键词搜索和用户主页采集。
- `google_news`：通过 Google News 做通用关键词搜索。
```

Add account URL rules:

```markdown
账号采集只接受明确主页 URL 或 ID，不做昵称自动选择。小红书账号采集推荐从网页登录后的账号主页复制完整 URL，URL 中应包含 `xsec_token` 和 `xsec_source`。知乎账号采集使用 `https://www.zhihu.com/people/yd1234567` 这种用户主页 URL。
```

Add TrendCrawlerRuntime externalization note:

```markdown
对外发布仓库不建议直接内嵌 TrendCrawlerRuntime。默认配置使用 `./third_party/TrendCrawlerRuntime`，可以手动 place compatible TrendCrawlerRuntime 到该目录，也可以把 `trend_crawler_runtime.dir` 指向你本机已有的 TrendCrawlerRuntime checkout。TrendCrawlerRuntime 使用内部使用说明，使用前请阅读其 LICENSE。
```

- [ ] **Step 4: Run docs grep**

Run:

```bash
rg -n "内置 `TrendCrawlerRuntime`|./TrendCrawlerRuntime|WECHAT_SEARCH_KEYWORDS" README.md config.yaml.example .env.example
```

Expected: no stale README wording that says TrendCrawlerRuntime is embedded; `./TrendCrawlerRuntime` only appears if describing legacy local checkout.

## Task 8: Full Test And Local Smoke

**Files:**
- No planned source edits unless tests reveal a defect.

- [ ] **Step 1: Run focused test suite**

Run:

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_bootstrap.py tests/test_google_news_crawler.py tests/test_xiaohongshu_crawler_modes.py tests/test_zhihu_crawler_modes.py tests/test_trendcrawler_arg_zhihu_creator.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run existing recommended tests**

Run:

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_wechat_mp_browser_mode.py tests/test_bootstrap.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run config validation smoke**

Run:

```bash
python scripts/bootstrap.py --check
```

Expected: reports config status. If `third_party/TrendCrawlerRuntime` is not present, it prints a TrendCrawlerRuntime requirements warning but config validation still reports actual config errors accurately.

- [ ] **Step 4: Run import smoke**

Run:

```bash
python - <<'PY'
from crawlers.manager import AVAILABLE_SOURCES
required = {"wechat", "wechat_mp", "xiaohongshu", "zhihu", "google_news"}
missing = required - set(AVAILABLE_SOURCES)
assert not missing, missing
print("sources ok:", ",".join(AVAILABLE_SOURCES))
PY
```

Expected: prints all required sources.

- [ ] **Step 5: Review changed files**

Run:

```bash
git diff -- config/app_config.py config/settings.py crawlers/manager.py crawlers/google_news.py crawlers/xiaohongshu.py crawlers/zhihu.py scripts/bootstrap.py requirements.txt config.yaml.example .env.example README.md
git diff -- TrendCrawlerRuntime/cmd_arg/arg.py
```

Expected: diffs only reflect this plan plus the already approved design and plan docs. Do not stage or revert unrelated dirty files.

## Post-Implementation Notes

- Do not delete the current `TrendCrawlerRuntime/` directory in this plan. Deleting it is a separate open-source cleanup step because it affects history size and login-state paths.
- For a truly clean public repository, create a fresh repo or rewrite history before publishing. Removing the directory from HEAD does not remove it from prior commits.
- If the external `TrendCrawlerRuntime` is replaced with another checkout, preserve the Zhihu `--creator_id` patch either as a small documented patch file or as a pinned fork.
