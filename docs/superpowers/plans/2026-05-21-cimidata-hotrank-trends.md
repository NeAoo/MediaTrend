# CimiData Hotrank Trends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated `全网热榜` Web subpage that manually fetches CimiData hotrank data, aggregates platform rows into current Top 10 trend topics, and displays a local snapshot trend chart.

**Architecture:** Add a focused hotrank backend path beside existing collection jobs, not inside `CrawlerManager`. The backend owns CimiData token handling, one-at-a-time channel fetches, snapshot storage, deterministic topic clustering, trend scoring, and classification. The frontend reads cached snapshots on page load and calls the run endpoint only when the operator clicks refresh.

**Tech Stack:** FastAPI, Pydantic, Python standard HTTP client or `requests`, pytest, React, TypeScript, CSS-only charts.

---

## File Structure

- Create `web/backend/hotrank_models.py`: Pydantic models for channels, evidence rows, topics, snapshots, warnings, and API responses.
- Create `web/backend/hotrank_client.py`: CimiData environment loading, token cache, token refresh, 1 QPS hotrank fetches.
- Create `web/backend/hotrank_aggregator.py`: hot parsing, title normalization, clustering, category classification, and trend scoring.
- Create `web/backend/hotrank_store.py`: write/read `web_jobs/hotrank/latest.json` and timestamped run artifacts.
- Create `web/backend/hotrank_routes.py`: `GET /api/hotrank/latest` and `POST /api/hotrank/runs`.
- Modify `web/backend/app.py`: include the hotrank router.
- Create `web/frontend/src/hotrankTypes.ts`: frontend types that mirror backend response fields.
- Create `web/frontend/src/hotrankApi.ts`: frontend API wrappers for latest snapshot and manual run.
- Create `web/frontend/src/pages/HotrankPage.tsx`: dedicated subpage with empty state, refresh button, Top 10 chart, platform matrix, category distribution, and evidence details.
- Modify `web/frontend/src/App.tsx`: add navigation and route for `/hotrank`.
- Modify `web/frontend/src/styles.css`: add responsive layout and CSS-only chart styles.
- Modify `.env.example`: add `CIMIDATA_APP_ID` and `CIMIDATA_APP_SECRET`.
- Add tests:
  - `tests/test_hotrank_aggregator.py`
  - `tests/test_hotrank_store.py`
  - `tests/test_hotrank_routes.py`

## Task 0: Dirty Worktree Guard

**Files:**
- No source files changed in this task.

- [ ] **Step 1: Inspect current branch and dirty files**

Run:

```bash
git -C /Users/neo/Projects/AITrend-aihot status --short --branch
```

Expected: existing unrelated modified files may be present. Do not revert them.

- [ ] **Step 2: Confirm planning docs are present**

Run:

```bash
test -f /Users/neo/Projects/AITrend-aihot/docs/superpowers/specs/2026-05-21-cimidata-hotrank-trends-design.md
test -f /Users/neo/Projects/AITrend-aihot/docs/superpowers/plans/2026-05-21-cimidata-hotrank-trends.md
```

Expected: both commands exit with code 0.

## Task 1: Backend Models

**Files:**
- Create: `web/backend/hotrank_models.py`
- Test: `tests/test_hotrank_aggregator.py`

- [ ] **Step 1: Write model import smoke test**

Create `tests/test_hotrank_aggregator.py` with:

```python
from web.backend.hotrank_models import HotrankChannelConfig, HotrankEvidence


def test_hotrank_models_import_and_validate():
    channel = HotrankChannelConfig(channel_id=1, channel_name="微博")
    evidence = HotrankEvidence(
        channel_id=1,
        channel_name="微博",
        rank=1,
        title="测试热榜",
        url="https://example.com",
        hot="123",
        hot_numeric=123.0,
        hot_tag="热",
        created_at="2026-05-21T10:00:00",
    )

    assert channel.channel_id == 1
    assert evidence.title == "测试热榜"
    assert evidence.hot_numeric == 123.0
```

- [ ] **Step 2: Run the smoke test and verify it fails**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_aggregator.py::test_hotrank_models_import_and_validate -q
```

Expected: FAIL with `ModuleNotFoundError` or missing model names.

- [ ] **Step 3: Create backend models**

Create `web/backend/hotrank_models.py` with:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


DEFAULT_HOTRANK_CHANNELS = [1, 2, 3, 4, 5, 7]


class HotrankChannelConfig(BaseModel):
    channel_id: int
    channel_name: str


class HotrankEvidence(BaseModel):
    channel_id: int
    channel_name: str
    rank: int = Field(ge=1)
    title: str
    url: str
    hot: str = ""
    hot_numeric: float = 0.0
    hot_tag: str = ""
    summary: str = ""
    created_at: str = ""
    rank_score: float = 0.0
    hot_score: float = 0.0


class HotrankTopic(BaseModel):
    topic_id: str
    label: str
    category: str
    trend_score: float
    score_breakdown: dict[str, float]
    platform_count: int
    evidence_count: int
    first_seen_at: str = ""
    latest_seen_at: str = ""
    evidence: list[HotrankEvidence] = Field(default_factory=list)


class HotrankSnapshot(BaseModel):
    run_id: str
    generated_at: str
    channels_requested: list[int]
    channels_succeeded: list[int]
    channels_failed: list[int]
    raw_row_count: int
    topic_count: int
    top_topics: list[HotrankTopic]
    category_counts: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class HotrankLatestResponse(BaseModel):
    snapshot: HotrankSnapshot | None = None


class HotrankRunRequest(BaseModel):
    channel_ids: list[int] = Field(default_factory=lambda: list(DEFAULT_HOTRANK_CHANNELS))


class HotrankRunResponse(BaseModel):
    snapshot: HotrankSnapshot
```

- [ ] **Step 4: Run the smoke test and verify it passes**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_aggregator.py::test_hotrank_models_import_and_validate -q
```

Expected: PASS.

## Task 2: Aggregator Parser, Classifier, And Scoring

**Files:**
- Create: `web/backend/hotrank_aggregator.py`
- Modify: `tests/test_hotrank_aggregator.py`

- [ ] **Step 1: Add failing parser, classifier, and scoring tests**

Append to `tests/test_hotrank_aggregator.py`:

```python
from web.backend.hotrank_aggregator import (
    aggregate_hotrank_rows,
    classify_topic,
    normalize_title,
    parse_hot_value,
)


def test_parse_hot_value_supports_common_formats():
    assert parse_hot_value("7904600") == 7904600.0
    assert parse_hot_value("2208 万热度") == 22080000.0
    assert parse_hot_value("1.2亿") == 120000000.0
    assert parse_hot_value("") == 0.0


def test_normalize_title_removes_spacing_and_punctuation():
    assert normalize_title("  四大一线城市房价全涨！ ") == "四大一线城市房价全涨"


def test_classify_topic_uses_general_taxonomy():
    assert classify_topic("中俄两国联合声明", "") == "时政国际"
    assert classify_topic("A股三大指数高开 半导体产业链走强", "") == "财经商业"
    assert classify_topic("女子极端饮食月瘦20斤重度脂肪肝", "") == "健康生活"
    assert classify_topic("高考志愿填报规则发布", "") == "教育升学"


def test_aggregate_hotrank_rows_builds_cross_platform_topic():
    rows_by_channel = {
        1: [
            {
                "title": "普京结束访华",
                "url": "https://weibo.example/search",
                "hot": "1000",
                "hot_tag": "热",
                "created_at": "2026-05-21T10:00:00",
            }
        ],
        3: [
            {
                "title": "普京结束对中国的国事访问",
                "url": "https://baidu.example/search",
                "hot": "9000",
                "hot_tag": "",
                "summary": "俄罗斯总统普京结束访华。",
                "created_at": "2026-05-21T10:05:00",
            }
        ],
    }

    snapshot = aggregate_hotrank_rows(
        rows_by_channel=rows_by_channel,
        channels_requested=[1, 3],
        channels_succeeded=[1, 3],
        channels_failed=[],
        warnings=[],
        run_id="test_run",
        generated_at="2026-05-21T10:10:00",
        top_n=10,
    )

    assert snapshot.raw_row_count == 2
    assert snapshot.topic_count == 1
    assert snapshot.top_topics[0].platform_count == 2
    assert snapshot.top_topics[0].trend_score > 70
```

- [ ] **Step 2: Run aggregator tests and verify they fail**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_aggregator.py -q
```

Expected: FAIL because `web.backend.hotrank_aggregator` is missing.

- [ ] **Step 3: Implement aggregator**

Create `web/backend/hotrank_aggregator.py` with these public functions and helpers:

```python
from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime
from statistics import mean
from typing import Any

from web.backend.hotrank_models import HotrankEvidence, HotrankSnapshot, HotrankTopic


CHANNEL_NAMES = {
    1: "微博",
    2: "知乎",
    3: "百度",
    4: "抖音",
    5: "头条",
    7: "B站",
}

STOP_TOKENS = {
    "回应", "现场", "官方", "为何", "怎么", "怎样", "最新", "热搜",
    "视频", "高清", "图文", "一文", "宣布", "发声", "通报",
}

CATEGORY_RULES = [
    ("时政国际", ("中俄", "普京", "特朗普", "国防部", "外交", "总统", "联合声明", "台海", "美国", "俄罗斯")),
    ("健康生活", ("医院", "医生", "健康", "脂肪肝", "睡眠", "食品", "乳膏", "药", "癌", "病")),
    ("教育升学", ("学校", "小学", "高考", "中考", "招生", "志愿", "教育", "学生", "教材", "字典")),
    ("财经商业", ("A股", "股", "IPO", "招股", "公司", "营收", "车企", "订单", "商业", "赔偿")),
    ("科技数码", ("AI", "人工智能", "机器人", "芯片", "半导体", "特斯拉", "FSD", "SpaceX", "星链")),
    ("汽车出行", ("汽车", "车企", "电车", "高铁", "航母", "航班", "出行", "交通")),
    ("体育赛事", ("NBA", "比赛", "冠军", "球队", "马刺", "雷霆", "赛事")),
    ("文娱影视", ("主演", "演员", "电影", "综艺", "明星", "怀孕", "内娱", "直播卖书")),
    ("平台争议/舆情", ("网红", "偷拍", "仅退款", "退货", "平台", "热搜", "直播", "录播", "争议")),
]


def parse_hot_value(value: Any) -> float:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0.0
    number = float(match.group(1))
    if "亿" in text:
        return number * 100_000_000
    if "万" in text:
        return number * 10_000
    return number


def normalize_title(title: str) -> str:
    text = str(title or "").strip().lower()
    text = re.sub(r"[\s　]+", "", text)
    text = re.sub(r"[，。！？、：；“”‘’《》（）()\\[\\]【】,.;:!?\"'`~_-]+", "", text)
    return text


def _tokens(title: str) -> set[str]:
    normalized = normalize_title(title)
    ascii_tokens = set(re.findall(r"[a-z0-9]{2,}", normalized))
    cjk = "".join(re.findall(r"[\u4e00-\u9fff]+", normalized))
    cjk_tokens = set()
    for size in (2, 3):
        for index in range(max(0, len(cjk) - size + 1)):
            token = cjk[index:index + size]
            if token not in STOP_TOKENS:
                cjk_tokens.add(token)
    return ascii_tokens | cjk_tokens


def _similarity(left_title: str, right_title: str) -> float:
    left = _tokens(left_title)
    right = _tokens(right_title)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _should_join_topic(title: str, topic: dict[str, Any]) -> bool:
    normalized = normalize_title(title)
    topic_titles = topic["titles"]
    for existing_title in topic_titles:
        existing = normalize_title(existing_title)
        if normalized == existing:
            return True
        shorter, longer = sorted([normalized, existing], key=len)
        if len(shorter) >= 6 and shorter in longer:
            return True
        if _similarity(title, existing_title) >= 0.34:
            shared = _tokens(title) & _tokens(existing_title)
            if any(len(token) >= 2 and token not in STOP_TOKENS for token in shared):
                return True
    return False


def classify_topic(title: str, summary: str) -> str:
    text = f"{title} {summary}"
    for label, keywords in CATEGORY_RULES:
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return label
    return "社会民生"


def _freshness_score(latest_seen_at: str, generated_at: str) -> float:
    try:
        latest = datetime.fromisoformat(latest_seen_at)
        generated = datetime.fromisoformat(generated_at)
    except ValueError:
        return 15.0
    age_hours = max(0.0, (generated - latest).total_seconds() / 3600)
    if age_hours <= 1:
        return 100.0
    if age_hours <= 3:
        return 85.0
    if age_hours <= 6:
        return 70.0
    if age_hours <= 12:
        return 55.0
    if age_hours <= 24:
        return 35.0
    return 15.0


def _topic_id(label: str, evidence: list[HotrankEvidence]) -> str:
    seed = "|".join([normalize_title(label), *sorted(item.url for item in evidence)[:3]])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _score_topic(evidence: list[HotrankEvidence], generated_at: str) -> tuple[float, dict[str, float]]:
    platform_rank_score = max((item.rank_score for item in evidence), default=0.0)
    top_hot_scores = sorted((item.hot_score for item in evidence), reverse=True)[:3]
    normalized_hot_score = mean(top_hot_scores) if top_hot_scores else platform_rank_score
    platform_count = len({item.channel_id for item in evidence})
    cross_platform_score = min(100.0, 35.0 + platform_count * 15.0 + min(len(evidence), 5) * 3.0)
    latest_seen_at = max((item.created_at for item in evidence if item.created_at), default=generated_at)
    freshness_score = _freshness_score(latest_seen_at, generated_at)
    trend_score = (
        platform_rank_score * 0.40
        + normalized_hot_score * 0.25
        + cross_platform_score * 0.25
        + freshness_score * 0.10
    )
    breakdown = {
        "platform_rank_score": round(platform_rank_score, 2),
        "normalized_hot_score": round(normalized_hot_score, 2),
        "cross_platform_score": round(cross_platform_score, 2),
        "freshness_score": round(freshness_score, 2),
    }
    return round(trend_score, 2), breakdown


def _build_evidence_rows(rows_by_channel: dict[int, list[dict[str, Any]]]) -> list[HotrankEvidence]:
    evidence_rows: list[HotrankEvidence] = []
    channel_hot_values: dict[int, list[float]] = {}
    for channel_id, rows in rows_by_channel.items():
        channel_hot_values[channel_id] = [parse_hot_value(row.get("hot")) for row in rows]

    for channel_id, rows in rows_by_channel.items():
        channel_name = CHANNEL_NAMES.get(channel_id, str(channel_id))
        channel_count = max(1, len(rows))
        hot_values = channel_hot_values.get(channel_id, [])
        min_hot = min(hot_values) if hot_values else 0.0
        max_hot = max(hot_values) if hot_values else 0.0
        for index, row in enumerate(rows, start=1):
            hot_numeric = parse_hot_value(row.get("hot"))
            rank_score = 100.0 * (channel_count - index + 1) / channel_count
            if math.isclose(max_hot, min_hot):
                hot_score = rank_score
            else:
                hot_score = 100.0 * (hot_numeric - min_hot) / (max_hot - min_hot)
            evidence_rows.append(
                HotrankEvidence(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    rank=index,
                    title=str(row.get("title") or "").strip(),
                    url=str(row.get("url") or "").strip(),
                    hot=str(row.get("hot") or "").strip(),
                    hot_numeric=hot_numeric,
                    hot_tag=str(row.get("hot_tag") or "").strip(),
                    summary=str(row.get("summary") or "").strip(),
                    created_at=str(row.get("created_at") or "").strip(),
                    rank_score=round(rank_score, 2),
                    hot_score=round(max(0.0, min(100.0, hot_score)), 2),
                )
            )
    return evidence_rows


def aggregate_hotrank_rows(
    rows_by_channel: dict[int, list[dict[str, Any]]],
    channels_requested: list[int],
    channels_succeeded: list[int],
    channels_failed: list[int],
    warnings: list[str],
    run_id: str,
    generated_at: str,
    top_n: int = 10,
) -> HotrankSnapshot:
    evidence_rows = _build_evidence_rows(rows_by_channel)
    topic_buckets: list[dict[str, Any]] = []
    for evidence in evidence_rows:
        joined = False
        for topic in topic_buckets:
            if _should_join_topic(evidence.title, topic):
                topic["evidence"].append(evidence)
                topic["titles"].append(evidence.title)
                joined = True
                break
        if not joined:
            topic_buckets.append({"titles": [evidence.title], "evidence": [evidence]})

    topics: list[HotrankTopic] = []
    category_counts: dict[str, int] = {}
    for bucket in topic_buckets:
        evidence = sorted(bucket["evidence"], key=lambda item: (item.rank_score, item.hot_score), reverse=True)
        label = evidence[0].title
        summary = " ".join(item.summary for item in evidence if item.summary)
        category = classify_topic(label, summary)
        trend_score, breakdown = _score_topic(evidence, generated_at)
        first_seen_at = min((item.created_at for item in evidence if item.created_at), default="")
        latest_seen_at = max((item.created_at for item in evidence if item.created_at), default="")
        category_counts[category] = category_counts.get(category, 0) + 1
        topics.append(
            HotrankTopic(
                topic_id=_topic_id(label, evidence),
                label=label,
                category=category,
                trend_score=trend_score,
                score_breakdown=breakdown,
                platform_count=len({item.channel_id for item in evidence}),
                evidence_count=len(evidence),
                first_seen_at=first_seen_at,
                latest_seen_at=latest_seen_at,
                evidence=evidence,
            )
        )

    topics.sort(key=lambda item: item.trend_score, reverse=True)
    return HotrankSnapshot(
        run_id=run_id,
        generated_at=generated_at,
        channels_requested=channels_requested,
        channels_succeeded=channels_succeeded,
        channels_failed=channels_failed,
        raw_row_count=len(evidence_rows),
        topic_count=len(topics),
        top_topics=topics[:top_n],
        category_counts=category_counts,
        warnings=warnings,
    )
```

- [ ] **Step 4: Run aggregator tests and verify they pass**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_aggregator.py -q
```

Expected: PASS.

## Task 3: Snapshot Store

**Files:**
- Create: `web/backend/hotrank_store.py`
- Create: `tests/test_hotrank_store.py`

- [ ] **Step 1: Add failing store tests**

Create `tests/test_hotrank_store.py` with:

```python
from pathlib import Path

from web.backend.hotrank_models import HotrankSnapshot
from web.backend.hotrank_store import HotrankStore


def _snapshot() -> HotrankSnapshot:
    return HotrankSnapshot(
        run_id="20260521_101010",
        generated_at="2026-05-21T10:10:10",
        channels_requested=[1],
        channels_succeeded=[1],
        channels_failed=[],
        raw_row_count=1,
        topic_count=0,
        top_topics=[],
        category_counts={},
        warnings=[],
    )


def test_hotrank_store_writes_latest_and_run_files(tmp_path: Path):
    store = HotrankStore(root=tmp_path / "hotrank")

    paths = store.save_run(
        run_id="20260521_101010",
        raw_payload={"channels": []},
        snapshot=_snapshot(),
    )

    assert paths["raw"].exists()
    assert paths["trends"].exists()
    assert (tmp_path / "hotrank" / "latest.json").exists()
    assert store.load_latest().run_id == "20260521_101010"


def test_hotrank_store_returns_none_when_latest_missing(tmp_path: Path):
    store = HotrankStore(root=tmp_path / "hotrank")

    assert store.load_latest() is None
```

- [ ] **Step 2: Run store tests and verify they fail**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_store.py -q
```

Expected: FAIL because `web.backend.hotrank_store` is missing.

- [ ] **Step 3: Implement store**

Create `web/backend/hotrank_store.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from web.backend.hotrank_models import HotrankSnapshot


class HotrankStore:
    def __init__(self, root: Path = Path("web_jobs/hotrank")) -> None:
        self.root = root
        self.runs_root = self.root / "runs"
        self.latest_path = self.root / "latest.json"

    def load_latest(self) -> HotrankSnapshot | None:
        if not self.latest_path.exists():
            return None
        data = json.loads(self.latest_path.read_text(encoding="utf-8"))
        return HotrankSnapshot.model_validate(data)

    def save_run(
        self,
        run_id: str,
        raw_payload: dict[str, Any],
        snapshot: HotrankSnapshot,
    ) -> dict[str, Path]:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
        raw_path = run_dir / "raw.json"
        trends_path = run_dir / "trends.json"
        raw_path.write_text(
            json.dumps(raw_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        snapshot_json = snapshot.model_dump(mode="json")
        trends_path.write_text(
            json.dumps(snapshot_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.latest_path.write_text(
            json.dumps(snapshot_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"raw": raw_path, "trends": trends_path, "latest": self.latest_path}
```

- [ ] **Step 4: Run store tests and verify they pass**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_store.py -q
```

Expected: PASS.

## Task 4: CimiData Client

**Files:**
- Create: `web/backend/hotrank_client.py`
- Modify: `.env.example`
- Test: `tests/test_hotrank_routes.py`

- [ ] **Step 1: Add environment keys to `.env.example`**

Append:

```env
CIMIDATA_APP_ID=
CIMIDATA_APP_SECRET=
```

- [ ] **Step 2: Create client module**

Create `web/backend/hotrank_client.py` with:

```python
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


CIMIDATA_HOST = "https://api.cimidata.com"
TOKEN_ENDPOINT = "/api/v2/token"
HOTRANK_ENDPOINT = "/api/v3/hotrank"
TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
TOKEN_REFRESH_MARGIN_SECONDS = 12 * 60 * 60
REQUEST_INTERVAL_SECONDS = 1.05


class CimiDataError(RuntimeError):
    pass


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class CimiDataHotrankClient:
    def __init__(
        self,
        host: str = CIMIDATA_HOST,
        token_cache: Path = Path("web_jobs/hotrank/token.json"),
        timeout_seconds: int = 30,
    ) -> None:
        self.host = host.rstrip("/")
        self.token_cache = token_cache
        self.timeout_seconds = timeout_seconds

    def get_token(self) -> str:
        load_env_file()
        app_id = os.environ.get("CIMIDATA_APP_ID", "").strip()
        app_secret = os.environ.get("CIMIDATA_APP_SECRET", "").strip()
        if not app_id or not app_secret:
            raise CimiDataError("CIMIDATA_APP_ID / CIMIDATA_APP_SECRET 未配置")

        now = time.time()
        if self.token_cache.exists():
            try:
                cached = json.loads(self.token_cache.read_text(encoding="utf-8"))
                token = str(cached.get("access_token") or "")
                expires_at = float(cached.get("expires_at") or 0)
                if token and now + TOKEN_REFRESH_MARGIN_SECONDS < expires_at:
                    return token
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        response = self._post_json(TOKEN_ENDPOINT, {"app_id": app_id, "app_secret": app_secret}, query={})
        data = response.get("data") if isinstance(response, dict) else {}
        token = str((data or {}).get("access_token") or (data or {}).get("token") or "").strip()
        if not token:
            raise CimiDataError("CimiData token response did not include access_token")

        self.token_cache.parent.mkdir(parents=True, exist_ok=True)
        self.token_cache.write_text(
            json.dumps(
                {
                    "access_token": token,
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "expires_at": now + TOKEN_TTL_SECONDS,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.token_cache.chmod(0o600)
        return token

    def fetch_hotrank_channel(self, channel_id: int, access_token: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"access_token": access_token, "channel_id": channel_id})
        request = urllib.request.Request(
            f"{self.host}{HOTRANK_ENDPOINT}?{query}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8", "replace")
        payload = json.loads(raw)
        if int(payload.get("code", 0) or 0) != 200:
            raise CimiDataError(f"hotrank channel {channel_id} failed: {payload.get('msg', payload)}")
        return payload

    def fetch_channels(self, channel_ids: list[int]) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any], list[int], list[int], list[str]]:
        token = self.get_token()
        rows_by_channel: dict[int, list[dict[str, Any]]] = {}
        raw_channels: list[dict[str, Any]] = []
        succeeded: list[int] = []
        failed: list[int] = []
        warnings: list[str] = []
        for index, channel_id in enumerate(channel_ids):
            if index:
                time.sleep(REQUEST_INTERVAL_SECONDS)
            try:
                payload = self.fetch_hotrank_channel(channel_id, token)
            except Exception as exc:
                failed.append(channel_id)
                warnings.append(f"channel {channel_id} failed: {exc}")
                continue
            data = payload.get("data", [])
            rows = [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
            rows_by_channel[channel_id] = rows
            raw_channels.append({"channel_id": channel_id, "raw_response": payload})
            succeeded.append(channel_id)
        return rows_by_channel, {"channels": raw_channels}, succeeded, failed, warnings

    def _post_json(self, path: str, payload: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.host}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8", "replace")
        parsed = json.loads(raw)
        if int(parsed.get("code", 0) or 0) != 200:
            raise CimiDataError(f"{path} failed: {parsed.get('msg', parsed)}")
        return parsed
```

- [ ] **Step 3: Run syntax check**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m py_compile web/backend/hotrank_client.py
```

Expected: PASS with no output.

## Task 5: Backend Routes

**Files:**
- Create: `web/backend/hotrank_routes.py`
- Modify: `web/backend/app.py`
- Create: `tests/test_hotrank_routes.py`

- [ ] **Step 1: Add failing route tests**

Create `tests/test_hotrank_routes.py` with:

```python
from pathlib import Path

from fastapi.testclient import TestClient

from web.backend.app import app
from web.backend.hotrank_models import HotrankSnapshot
from web.backend.hotrank_store import HotrankStore


def test_hotrank_latest_does_not_trigger_run(monkeypatch, tmp_path: Path):
    from web.backend import hotrank_routes

    store = HotrankStore(root=tmp_path / "hotrank")
    monkeypatch.setattr(hotrank_routes, "STORE", store)

    def fail_run():
        raise AssertionError("latest endpoint must not fetch CimiData")

    monkeypatch.setattr(hotrank_routes, "_run_hotrank_fetch", fail_run)
    client = TestClient(app)

    response = client.get("/api/hotrank/latest")

    assert response.status_code == 200
    assert response.json() == {"snapshot": None}


def test_hotrank_run_returns_snapshot(monkeypatch, tmp_path: Path):
    from web.backend import hotrank_routes

    store = HotrankStore(root=tmp_path / "hotrank")
    monkeypatch.setattr(hotrank_routes, "STORE", store)

    def fake_run(channel_ids):
        snapshot = HotrankSnapshot(
            run_id="fake",
            generated_at="2026-05-21T10:10:10",
            channels_requested=channel_ids,
            channels_succeeded=channel_ids,
            channels_failed=[],
            raw_row_count=0,
            topic_count=0,
            top_topics=[],
            category_counts={},
            warnings=[],
        )
        store.save_run("fake", {"channels": []}, snapshot)
        return snapshot

    monkeypatch.setattr(hotrank_routes, "_run_hotrank_fetch", fake_run)
    client = TestClient(app)

    response = client.post("/api/hotrank/runs", json={"channel_ids": [1, 3]})

    assert response.status_code == 200
    assert response.json()["snapshot"]["channels_requested"] == [1, 3]
```

- [ ] **Step 2: Run route tests and verify they fail**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_routes.py -q
```

Expected: FAIL because the router is not included.

- [ ] **Step 3: Implement routes**

Create `web/backend/hotrank_routes.py`:

```python
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from web.backend.hotrank_aggregator import aggregate_hotrank_rows
from web.backend.hotrank_client import CimiDataError, CimiDataHotrankClient
from web.backend.hotrank_models import HotrankLatestResponse, HotrankRunRequest, HotrankRunResponse
from web.backend.hotrank_store import HotrankStore


router = APIRouter(prefix="/api/hotrank", tags=["hotrank"])
STORE = HotrankStore()


def _run_hotrank_fetch(channel_ids: list[int]):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_at = datetime.now().isoformat(timespec="seconds")
    client = CimiDataHotrankClient()
    rows_by_channel, raw_payload, succeeded, failed, warnings = client.fetch_channels(channel_ids)
    if not succeeded:
        raise CimiDataError("所有 hotrank 渠道均请求失败")
    snapshot = aggregate_hotrank_rows(
        rows_by_channel=rows_by_channel,
        channels_requested=channel_ids,
        channels_succeeded=succeeded,
        channels_failed=failed,
        warnings=warnings,
        run_id=run_id,
        generated_at=generated_at,
        top_n=10,
    )
    STORE.save_run(run_id=run_id, raw_payload=raw_payload, snapshot=snapshot)
    return snapshot


@router.get("/latest", response_model=HotrankLatestResponse)
def hotrank_latest() -> HotrankLatestResponse:
    return HotrankLatestResponse(snapshot=STORE.load_latest())


@router.post("/runs", response_model=HotrankRunResponse)
def hotrank_run(request: HotrankRunRequest) -> HotrankRunResponse:
    try:
        snapshot = _run_hotrank_fetch(request.channel_ids)
    except CimiDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return HotrankRunResponse(snapshot=snapshot)
```

- [ ] **Step 4: Include router in app**

Modify `web/backend/app.py`:

```python
from web.backend.hotrank_routes import router as hotrank_router
```

Add after existing `app = FastAPI(...)` setup:

```python
app.include_router(hotrank_router)
```

- [ ] **Step 5: Run route tests and verify they pass**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_routes.py -q
```

Expected: PASS.

## Task 6: Frontend API And Types

**Files:**
- Create: `web/frontend/src/hotrankTypes.ts`
- Create: `web/frontend/src/hotrankApi.ts`

- [ ] **Step 1: Add frontend types**

Create `web/frontend/src/hotrankTypes.ts`:

```typescript
export type HotrankEvidence = {
  channel_id: number;
  channel_name: string;
  rank: number;
  title: string;
  url: string;
  hot: string;
  hot_numeric: number;
  hot_tag: string;
  summary?: string;
  created_at: string;
  rank_score: number;
  hot_score: number;
};

export type HotrankTopic = {
  topic_id: string;
  label: string;
  category: string;
  trend_score: number;
  score_breakdown: Record<string, number>;
  platform_count: number;
  evidence_count: number;
  first_seen_at: string;
  latest_seen_at: string;
  evidence: HotrankEvidence[];
};

export type HotrankSnapshot = {
  run_id: string;
  generated_at: string;
  channels_requested: number[];
  channels_succeeded: number[];
  channels_failed: number[];
  raw_row_count: number;
  topic_count: number;
  top_topics: HotrankTopic[];
  category_counts: Record<string, number>;
  warnings: string[];
};

export type HotrankLatestResponse = {
  snapshot: HotrankSnapshot | null;
};

export type HotrankRunResponse = {
  snapshot: HotrankSnapshot;
};
```

- [ ] **Step 2: Add frontend API wrapper**

Create `web/frontend/src/hotrankApi.ts`:

```typescript
import type { HotrankLatestResponse, HotrankRunResponse } from "./hotrankTypes";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchHotrankLatest(): Promise<HotrankLatestResponse> {
  return requestJson<HotrankLatestResponse>("/api/hotrank/latest");
}

export function runHotrankRefresh(channelIds = [1, 2, 3, 4, 5, 7]): Promise<HotrankRunResponse> {
  return requestJson<HotrankRunResponse>("/api/hotrank/runs", {
    method: "POST",
    body: JSON.stringify({ channel_ids: channelIds }),
  });
}
```

- [ ] **Step 3: Run frontend type check or build**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot/web/frontend
npm run build
```

Expected: PASS because the new API and type files are standalone and not yet imported by the app.

## Task 7: Hotrank Page

**Files:**
- Create: `web/frontend/src/pages/HotrankPage.tsx`
- Modify: `web/frontend/src/App.tsx`
- Modify: `web/frontend/src/styles.css`

- [ ] **Step 1: Create `HotrankPage.tsx`**

Create `web/frontend/src/pages/HotrankPage.tsx`:

```tsx
import { useEffect, useMemo, useState } from "react";
import { fetchHotrankLatest, runHotrankRefresh } from "../hotrankApi";
import type { HotrankSnapshot, HotrankTopic } from "../hotrankTypes";

const PLATFORM_TOTAL = 6;

function formatGeneratedAt(value: string) {
  if (!value) return "-";
  return value.replace("T", " ");
}

function topEvidence(topic: HotrankTopic) {
  return [...topic.evidence].sort((a, b) => a.rank - b.rank).slice(0, 4);
}

export function HotrankPage() {
  const [snapshot, setSnapshot] = useState<HotrankSnapshot | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    fetchHotrankLatest()
      .then((data) => {
        if (mounted) setSnapshot(data.snapshot);
      })
      .catch((exc) => {
        if (mounted) setError(String(exc));
      })
      .finally(() => {
        if (mounted) setLoadingLatest(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const categoryRows = useMemo(() => {
    if (!snapshot) return [];
    return Object.entries(snapshot.category_counts)
      .sort((left, right) => right[1] - left[1])
      .slice(0, 8);
  }, [snapshot]);

  async function handleRefresh() {
    setRunning(true);
    setError("");
    try {
      const response = await runHotrankRefresh();
      setSnapshot(response.snapshot);
    } catch (exc) {
      setError(String(exc));
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="hotrank-page">
      <section className="hotrank-header">
        <div>
          <p className="eyebrow">CimiData Hotrank</p>
          <h1>全网热榜</h1>
          <p className="subtitle">打开页面只读取本地快照；点击按钮后才请求外部 API 并生成当前趋势图。</p>
        </div>
        <button className="primary-button" onClick={handleRefresh} disabled={running}>
          {running ? "正在生成..." : "生成当前趋势"}
        </button>
      </section>

      {error && <div className="alert error">{error}</div>}
      {loadingLatest && <div className="empty-state">正在读取本地快照...</div>}

      {!loadingLatest && !snapshot && (
        <section className="empty-state">
          <h2>还没有全网热榜快照</h2>
          <p>点击“生成当前趋势”后，会按 1 QPS 顺序请求微博、知乎、百度、抖音、头条和 B站。</p>
        </section>
      )}

      {snapshot && (
        <>
          <section className="metric-grid">
            <div className="metric-card">
              <span>平台覆盖</span>
              <strong>{snapshot.channels_succeeded.length}/{PLATFORM_TOTAL}</strong>
            </div>
            <div className="metric-card">
              <span>原始热榜</span>
              <strong>{snapshot.raw_row_count}</strong>
            </div>
            <div className="metric-card">
              <span>聚合主题</span>
              <strong>{snapshot.topic_count}</strong>
            </div>
            <div className="metric-card">
              <span>生成时间</span>
              <strong>{formatGeneratedAt(snapshot.generated_at)}</strong>
            </div>
          </section>

          {snapshot.warnings.length > 0 && (
            <section className="alert warning">
              {snapshot.warnings.map((warning) => <div key={warning}>{warning}</div>)}
            </section>
          )}

          <section className="hotrank-layout">
            <div className="trend-panel">
              <h2>当前 Top10 搜索趋势</h2>
              <div className="trend-bars">
                {snapshot.top_topics.map((topic, index) => (
                  <article className="trend-row" key={topic.topic_id}>
                    <div className="trend-rank">#{index + 1}</div>
                    <div className="trend-main">
                      <div className="trend-title-line">
                        <strong>{topic.label}</strong>
                        <span>{topic.category}</span>
                      </div>
                      <div className="trend-bar-track">
                        <div className="trend-bar-fill" style={{ width: `${Math.min(100, topic.trend_score)}%` }} />
                      </div>
                      <div className="trend-meta">
                        <span>趋势分 {topic.trend_score.toFixed(1)}</span>
                        <span>覆盖 {topic.platform_count} 平台</span>
                        <span>证据 {topic.evidence_count} 条</span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <aside className="category-panel">
              <h2>分类分布</h2>
              {categoryRows.map(([category, count]) => (
                <div className="category-row" key={category}>
                  <span>{category}</span>
                  <div className="category-track">
                    <div className="category-fill" style={{ width: `${Math.min(100, count * 12)}%` }} />
                  </div>
                  <strong>{count}</strong>
                </div>
              ))}
            </aside>
          </section>

          <section className="evidence-panel">
            <h2>Top10 证据</h2>
            {snapshot.top_topics.map((topic) => (
              <details className="evidence-card" key={topic.topic_id}>
                <summary>
                  <strong>{topic.label}</strong>
                  <span>{topic.category} · {topic.platform_count} 平台 · {topic.trend_score.toFixed(1)} 分</span>
                </summary>
                <div className="evidence-list">
                  {topEvidence(topic).map((item) => (
                    <a href={item.url} target="_blank" rel="noreferrer" className="evidence-item" key={`${topic.topic_id}-${item.channel_id}-${item.rank}`}>
                      <span>{item.channel_name} #{item.rank}</span>
                      <strong>{item.title}</strong>
                      <em>{item.hot_tag || "无标签"} · {item.hot || "无热度值"}</em>
                    </a>
                  ))}
                </div>
              </details>
            ))}
          </section>
        </>
      )}
    </main>
  );
}
```

- [ ] **Step 2: Add route and nav in `App.tsx`**

Open `web/frontend/src/App.tsx`. Add:

```tsx
import { HotrankPage } from "./pages/HotrankPage";
```

Add a nav item labeled `全网热榜` pointing to `/hotrank`, following the existing navigation pattern. Add a route that renders:

```tsx
<HotrankPage />
```

- [ ] **Step 3: Add CSS**

Append to `web/frontend/src/styles.css`:

```css
.hotrank-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hotrank-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.hotrank-header h1 {
  margin: 0;
  font-size: 32px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
}

.subtitle {
  margin: 6px 0 0;
  color: #64748b;
}

.primary-button {
  border: 0;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-weight: 700;
  min-height: 40px;
  padding: 0 16px;
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.metric-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card,
.trend-panel,
.category-panel,
.evidence-panel,
.empty-state,
.alert {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.metric-card span {
  color: #64748b;
  display: block;
  font-size: 13px;
}

.metric-card strong {
  color: #0f172a;
  display: block;
  font-size: 24px;
  margin-top: 6px;
}

.hotrank-layout {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr);
}

.trend-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-row {
  align-items: center;
  display: grid;
  gap: 12px;
  grid-template-columns: 42px minmax(0, 1fr);
}

.trend-rank {
  color: #2563eb;
  font-weight: 800;
}

.trend-title-line,
.trend-meta,
.category-row,
.evidence-item {
  align-items: center;
  display: flex;
  gap: 10px;
}

.trend-title-line {
  justify-content: space-between;
}

.trend-title-line span,
.trend-meta,
.evidence-item em,
.evidence-card summary span {
  color: #64748b;
  font-size: 13px;
  font-style: normal;
}

.trend-bar-track,
.category-track {
  background: #e2e8f0;
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.trend-bar-fill,
.category-fill {
  background: #2563eb;
  height: 100%;
}

.category-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 32px;
  margin-top: 12px;
}

.evidence-card {
  border-top: 1px solid #e2e8f0;
  padding: 12px 0;
}

.evidence-card summary {
  cursor: pointer;
}

.evidence-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.evidence-item {
  color: inherit;
  justify-content: space-between;
  text-decoration: none;
}

.alert.error {
  border-color: #fecaca;
  color: #991b1b;
}

.alert.warning {
  border-color: #fde68a;
  color: #92400e;
}

@media (max-width: 860px) {
  .hotrank-header {
    flex-direction: column;
  }

  .metric-grid,
  .hotrank-layout {
    grid-template-columns: 1fr;
  }

  .trend-title-line,
  .trend-meta,
  .evidence-item {
    align-items: flex-start;
    flex-direction: column;
  }
}
```

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot/web/frontend
npm run build
```

Expected: PASS.

## Task 8: Full Verification

**Files:**
- Existing files only.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_hotrank_aggregator.py tests/test_hotrank_store.py tests/test_hotrank_routes.py -q
```

Expected: PASS.

- [ ] **Step 2: Run existing backend tests that cover job/config stability**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_job_runner.py tests/test_web_active_job_guard.py -q
```

Expected: PASS. If unrelated dirty worktree changes have failing tests, inspect failures before editing.

- [ ] **Step 3: Start backend locally**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
```

Expected: server starts and serves `http://127.0.0.1:8000`.

- [ ] **Step 4: Verify latest endpoint does not call external API**

Run in another terminal:

```bash
curl -s http://127.0.0.1:8000/api/hotrank/latest | python -m json.tool
```

Expected: returns either `{"snapshot": null}` or a cached snapshot. No CimiData balance changes should happen from this GET.

- [ ] **Step 5: Verify manual run endpoint with real credentials**

Only run after `.env` has valid `CIMIDATA_APP_ID` and `CIMIDATA_APP_SECRET`.

```bash
curl -s -X POST http://127.0.0.1:8000/api/hotrank/runs \
  -H 'Content-Type: application/json' \
  -d '{"channel_ids":[1,2,3,4,5,7]}' | python -m json.tool
```

Expected: response contains `snapshot.top_topics` with up to 10 topics and `channels_succeeded` containing successful channels.

- [ ] **Step 6: Verify snapshot files**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
find web_jobs/hotrank -maxdepth 3 -type f | sort
```

Expected: includes `web_jobs/hotrank/latest.json`, `raw.json`, and `trends.json` under a timestamped run directory.

- [ ] **Step 7: Verify UI manually**

Open:

```text
http://127.0.0.1:8000/hotrank
```

Expected:

- Opening the page shows cached data or empty state.
- It does not trigger a new run.
- Clicking `生成当前趋势` triggers one manual run.
- Top 10 trend bars render.
- Category distribution renders.
- Evidence details expand and show platform title/rank/hot/link.

## Task 9: Documentation Note

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a short Web page note**

In the Web 工作台 section of `README.md`, add:

````markdown
### 全网热榜

`/hotrank` 是 CimiData 热榜聚合页面。打开页面只读取本地最新快照，不会自动请求外部 API。点击“生成当前趋势”后，后端才会按 1 QPS 顺序请求微博、知乎、百度、抖音、头条和 B站热榜，并生成当前 Top10 趋势图。

需要在 `.env` 配置：

```env
CIMIDATA_APP_ID=
CIMIDATA_APP_SECRET=
```

热榜趋势分是基于平台内排名、平台内热度归一、跨平台共振和时效性计算的派生分数，不代表真实全网搜索量。
````

- [ ] **Step 2: Run markdown sanity check**

Run:

```bash
cd /Users/neo/Projects/AITrend-aihot
python - <<'PY'
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
assert "全网热榜" in text
assert "CIMIDATA_APP_ID" in text
assert "不代表真实全网搜索量" in text
PY
```

Expected: PASS with no output.

## Self-Review Checklist

- [x] Spec requirement: `/hotrank` dedicated subpage is covered by Task 7.
- [x] Spec requirement: page load does not call CimiData is covered by Task 5 route test and Task 8 manual check.
- [x] Spec requirement: manual click triggers API is covered by Task 7 and Task 8.
- [x] Spec requirement: one-at-a-time 1 QPS channel calls is covered by Task 4 client.
- [x] Spec requirement: Top 10 chart, coverage, categories, evidence are covered by Task 7.
- [x] Spec requirement: local snapshots are covered by Task 3.
- [x] Spec requirement: secrets stay backend-only is covered by Task 4 and frontend API shape in Task 6.
- [x] Placeholder scan: this plan contains concrete file paths, commands, expected results, and code blocks for new code.
