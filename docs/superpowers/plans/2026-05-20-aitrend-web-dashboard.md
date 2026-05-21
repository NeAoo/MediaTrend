# AITrend Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished blue/white/gray AITrend web dashboard for source configuration, optional LLM scoring configuration, job execution, and per-source/keyword/account progress tracking.

**Architecture:** Add a FastAPI backend under `web/backend/` and a Vite React frontend under `web/frontend/`. The backend reads and validates the existing `config.yaml`, writes it with backups, stores job state under `web_jobs/`, streams events through SSE, and orchestrates collection/scoring without breaking the existing CLI.

**Tech Stack:** Python FastAPI, Pydantic, PyYAML, Loguru, React, TypeScript, Vite, Server-Sent Events, pytest.

---

## File Structure

Create or modify these files:

- Modify: `requirements.txt`
  - Add `fastapi` and `uvicorn`.
- Modify: `.gitignore`
  - Keep `.superpowers/` ignored.
  - Add `web_jobs/` and frontend build outputs.
- Modify: `config/app_config.py`
  - Add `ScoringConfig`, `ScoringPromptConfig`, and UI expected minimum fields.
- Modify: `config/settings.py`
  - Export scoring settings from `APP_CONFIG.scoring`.
- Modify: `config.yaml`
  - Add `scoring` section and expected minimum fields.
- Modify: `.env.example`
  - Keep `LLM_API_KEY` documented as secret storage.
- Create: `prompts/scoring_system_prompt.md`
  - System prompt extracted from `scorers/scorer.py`.
- Create: `prompts/scoring_user_prompt.md`
  - User prompt template extracted from `scorers/scorer.py`.
- Modify: `scorers/scorer.py`
  - Load prompt files and render variables instead of hard-coding prompt text.
- Create: `web/backend/__init__.py`
- Create: `web/backend/app.py`
  - FastAPI app and route registration.
- Create: `web/backend/models.py`
  - Web request/response/job/event models.
- Create: `web/backend/config_service.py`
  - Read, validate, backup, and atomically write `config.yaml`; save prompt files.
- Create: `web/backend/env_service.py`
  - Read/mask/write `.env` secrets.
- Create: `web/backend/job_store.py`
  - Manage `web_jobs/<job_id>/status.json`, `events.jsonl`, and `artifacts.json`.
- Create: `web/backend/job_runner.py`
  - Run serial and parallel collection jobs, merge, score, and report.
- Create: `web/backend/progress.py`
  - Progress calculation helpers and low-expected warning logic.
- Create: `web/frontend/package.json`
- Create: `web/frontend/index.html`
- Create: `web/frontend/tsconfig.json`
- Create: `web/frontend/vite.config.ts`
- Create: `web/frontend/src/main.tsx`
- Create: `web/frontend/src/App.tsx`
- Create: `web/frontend/src/api.ts`
- Create: `web/frontend/src/types.ts`
- Create: `web/frontend/src/styles.css`
- Create: `web/frontend/src/pages/DashboardPage.tsx`
- Create: `web/frontend/src/pages/SourcesPage.tsx`
- Create: `web/frontend/src/pages/ScoringPage.tsx`
- Create: `web/frontend/src/pages/HistoryPage.tsx`
- Create: `web/frontend/src/pages/ReportsPage.tsx`
- Create: `web/frontend/src/pages/SystemStatusPage.tsx`
- Create: `web/frontend/src/components/TopNav.tsx`
- Create: `web/frontend/src/components/SourceProgressCard.tsx`
- Create: `web/frontend/src/components/ProgressBar.tsx`
- Create: `web/frontend/src/components/SourceConfigEditor.tsx`
- Create: `web/frontend/src/components/PromptEditor.tsx`
- Create: `tests/test_web_config_service.py`
- Create: `tests/test_scoring_config.py`
- Create: `tests/test_job_store.py`
- Create: `tests/test_job_runner.py`
- Create: `tests/test_progress.py`

---

### Task 1: Add Web and Scoring Dependencies

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Update Python dependencies**

Add these lines to `requirements.txt`:

```txt
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
```

- [ ] **Step 2: Update ignored runtime outputs**

Add these lines to `.gitignore`:

```gitignore
web_jobs/
web/frontend/node_modules/
web/frontend/dist/
```

- [ ] **Step 3: Verify dependency file**

Run:

```bash
python -m pip install -r requirements.txt
```

Expected: command exits 0. If local environment lacks Node, this task still passes because Node dependencies are not installed here.

---

### Task 2: Extend App Config for Scoring and Expected Minimums

**Files:**
- Modify: `config/app_config.py`
- Modify: `config/settings.py`
- Modify: `config.yaml`
- Modify: `.env.example`
- Test: `tests/test_scoring_config.py`

- [ ] **Step 1: Write failing tests for scoring config**

Create `tests/test_scoring_config.py`:

```python
from pathlib import Path

from config.app_config import load_app_config


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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/test_scoring_config.py -q
```

Expected: fails because `scoring` and `expected_min_results` are not defined.

- [ ] **Step 3: Implement config models**

In `config/app_config.py`, add:

```python
class ScoringPromptConfig(BaseModel):
    system_path: str = "./prompts/scoring_system_prompt.md"
    user_path: str = "./prompts/scoring_user_prompt.md"


class ScoringConfig(BaseModel):
    enabled: bool = True
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-5.4"
    timeout_seconds: float = Field(120.0, ge=10)
    max_retries: int = Field(1, ge=0)
    max_completion_tokens: int = Field(0, ge=0)
    reasoning_effort: str = ""
    workers: int = Field(5, ge=1)
    parse_failure_score: float = Field(1.0, ge=1.0, le=10.0)
    random_fallback_on_all_parse_failures: bool = True
    prompt: ScoringPromptConfig = Field(default_factory=ScoringPromptConfig)
```

Add `expected_min_results` to `KeywordSearchConfig`, `WechatAccountCrawlConfig`, and `CreatorAccountCrawlConfig`:

```python
expected_min_results: int = Field(3, ge=0)
```

Add to `AppConfig`:

```python
scoring: ScoringConfig = Field(default_factory=ScoringConfig)
```

- [ ] **Step 4: Export scoring settings**

In `config/settings.py`, replace LLM env defaults with config-backed defaults while keeping `.env` as override for the secret:

```python
SCORING_ENABLED = APP_CONFIG.scoring.enabled
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = APP_CONFIG.scoring.base_url.strip()
LLM_MODEL = APP_CONFIG.scoring.model.strip() or "gpt-5.4"
LLM_TIMEOUT_SECONDS = max(10.0, float(APP_CONFIG.scoring.timeout_seconds))
LLM_MAX_RETRIES = max(0, int(APP_CONFIG.scoring.max_retries))
LLM_MAX_COMPLETION_TOKENS = max(0, int(APP_CONFIG.scoring.max_completion_tokens))
LLM_REASONING_EFFORT = APP_CONFIG.scoring.reasoning_effort.strip()
SCORE_WORKERS = max(1, int(APP_CONFIG.scoring.workers))
SCORING_PARSE_FAILURE_SCORE = max(1.0, min(10.0, float(APP_CONFIG.scoring.parse_failure_score)))
SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES = APP_CONFIG.scoring.random_fallback_on_all_parse_failures
SCORING_SYSTEM_PROMPT_PATH = str(APP_CONFIG.resolve_path(APP_CONFIG.scoring.prompt.system_path))
SCORING_USER_PROMPT_PATH = str(APP_CONFIG.resolve_path(APP_CONFIG.scoring.prompt.user_path))
```

- [ ] **Step 5: Update config.yaml**

Add this section to `config.yaml`:

```yaml
scoring:
  enabled: true
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
```

Add `expected_min_results: 3` beside every `max_results_per_keyword` and `max_results_per_account` entry.

- [ ] **Step 6: Update .env.example**

Keep only secret and local machine overrides in `.env.example`. Add a comment:

```dotenv
# LLM_API_KEY remains in .env because config.yaml must not store secrets.
LLM_API_KEY=
```

- [ ] **Step 7: Run tests**

Run:

```bash
python -m pytest tests/test_scoring_config.py tests/test_app_config.py tests/test_settings.py -q
```

Expected: all pass.

---

### Task 3: Extract Scoring Prompts from Code

**Files:**
- Create: `prompts/scoring_system_prompt.md`
- Create: `prompts/scoring_user_prompt.md`
- Modify: `scorers/scorer.py`
- Test: `tests/test_scoring_config.py`

- [ ] **Step 1: Add prompt files**

Create `prompts/scoring_system_prompt.md`:

```markdown
你是专业的社会热点选题评估专家，擅长判断内容的点击潜力、公共讨论价值、事实可靠性和传播风险。
```

Create `prompts/scoring_user_prompt.md` with the current user prompt from `scorers/scorer.py`, replacing item fields with variables:

```markdown
你是一位社会热点公众号选题评估专家，请对下面这一篇内容进行独立评分。

评分目标：
- 判断这篇内容是否值得进入“社会热点 / 公众号选题池”，核心目标是提升整体点击量和传播潜力。
- 只评价这一篇文章，不要和其他文章做相对比较。
- 正文最多 5000 字，必须基于标题、来源、作者/公众号、发布时间、URL、热度指标和正文综合判断。
- 如果内容只是资料下载、纯广告、旧闻搬运、无法核查、夸张承诺，应该明显降分。

评估逻辑：
- 当前第一目标是阅读量、打开率和传播性，不再把每篇内容筛成家长教育稿。
- 优先看当前社会热点事件、公共情绪点、争议点、反常识点、强故事性和可转成公众号长文的话题。
- 候选文章会被“选题池”当作“对标母稿”：标题结构、核心热词、冲突设置、叙事顺序、段落节奏和情绪推进越值得模仿，越应该高分。
- 不要因为话题无法自然连接到教育、孩子、家庭或智趣点读而降分；教育/家庭相关只作为弱备注，不进入核心判断。
- 如果内容非常短，不到两百字，没有核心观点，应该明显降分。
- 重点判断普通大众是否会点开、是否看得懂、是否愿意转发或评论。
- 来源可以来自公众号线索，但涉及政策、医疗、教育、公共事件、具体机构和人物时，事实必须可核查。
- 可以有爆款标题节奏和情绪张力，但不能低俗标题党、不能制造恐慌、不能夸大承诺。
- 更偏好：热点明确、冲突/悬念清楚、信息密度高、大众共鸣强、标题有点击点、结构可拆、二次创作空间大的内容。

评分维度（每项 1-10 分）：
1. heat：热点/打开潜力。
2. authority：权威性/可核查性。
3. quality：内容质量。
4. resonance：大众共鸣/传播角度。
5. timeliness：时效性。
6. reference_value：对标价值。
7. risk_control：风险控制。

综合评分公式：
overall = heat×0.35 + timeliness×0.18 + resonance×0.18 + reference_value×0.14 + quality×0.08 + authority×0.04 + risk_control×0.03

请严格按照以下 JSON 格式返回评分结果，只返回 JSON，不要其他文字：
{
  "heat": 8.5,
  "authority": 9.0,
  "quality": 8.0,
  "resonance": 9.5,
  "timeliness": 8.0,
  "reference_value": 8.5,
  "risk_control": 9.0,
  "overall": 8.53,
  "reason": "用1-2句话说明为什么值得或不值得进入候选池",
  "best_angle": "如果值得写，说明最适合对标原文的标题/冲突/叙事角度；不值得则写不建议",
  "risk_notes": ["需要注意的事实、合规或表达风险"]
}

需要评分的内容：
- 标题: {title}
- 来源平台: {source}
- 作者/公众号: {author}
- 发布时间: {publish_time}
- URL: {url}
- 热度指标: {popularity}
- 正文: {content}

请开始评分：
```

- [ ] **Step 2: Add prompt rendering helper test**

Append to `tests/test_scoring_config.py`:

```python
from datetime import datetime

from models.hotspot import EducationHotspot
from scorers.scorer import render_scoring_prompt


def test_render_scoring_prompt_replaces_variables(tmp_path: Path):
    template = tmp_path / "prompt.md"
    template.write_text("标题: {title}\n正文: {content}\n", encoding="utf-8")
    hotspot = EducationHotspot(
        title="测试标题",
        source="aihot",
        publish_time=datetime(2026, 5, 20, 12, 0),
        content="测试正文",
        url="https://example.com",
        author="测试作者",
        popularity=12,
    )

    rendered = render_scoring_prompt(template.read_text(encoding="utf-8"), hotspot)

    assert "测试标题" in rendered
    assert "测试正文" in rendered
    assert "{title}" not in rendered
```

- [ ] **Step 3: Implement prompt rendering**

In `scorers/scorer.py`, add:

```python
from pathlib import Path
```

Add a helper above `ContentScorer`:

```python
def render_scoring_prompt(template: str, hotspot: EducationHotspot) -> str:
    content = hotspot.content or ""
    values = {
        "title": hotspot.title,
        "source": hotspot.source,
        "author": hotspot.author or "未知",
        "publish_time": hotspot.publish_time.strftime("%Y-%m-%d %H:%M"),
        "url": hotspot.url or "无",
        "popularity": hotspot.popularity or "未知",
        "content": content,
    }
    return template.format(**values)
```

In `ContentScorer.__init__`, read prompt files:

```python
from config.settings import SCORING_SYSTEM_PROMPT_PATH, SCORING_USER_PROMPT_PATH

self.system_prompt = Path(SCORING_SYSTEM_PROMPT_PATH).read_text(encoding="utf-8").strip()
self.user_prompt_template = Path(SCORING_USER_PROMPT_PATH).read_text(encoding="utf-8").strip()
```

In `_score_single_item`, replace hard-coded `prompt = f"""..."""` with:

```python
prompt = render_scoring_prompt(self.user_prompt_template, hotspot)
```

Replace system message content with:

```python
"content": self.system_prompt
```

- [ ] **Step 4: Run scoring tests**

Run:

```bash
python -m pytest tests/test_scoring_config.py -q
```

Expected: all pass.

---

### Task 4: Add Config and Secret Services

**Files:**
- Create: `web/backend/__init__.py`
- Create: `web/backend/models.py`
- Create: `web/backend/config_service.py`
- Create: `web/backend/env_service.py`
- Test: `tests/test_web_config_service.py`

- [ ] **Step 1: Write config service tests**

Create `tests/test_web_config_service.py`:

```python
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
```

- [ ] **Step 2: Implement models**

Create `web/backend/models.py`:

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
RunMode = Literal["collect_only", "collect_score_report"]
ExecutionMode = Literal["serial", "parallel"]


class ApiError(BaseModel):
    message: str
    details: list[str] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    config: dict[str, Any]
    masked_api_key: str = ""
    has_api_key: bool = False


class SaveConfigRequest(BaseModel):
    config: dict[str, Any]
    api_key: str | None = None


class JobCreateRequest(BaseModel):
    run_mode: RunMode
    execution_mode: ExecutionMode = "serial"


class JobEvent(BaseModel):
    job_id: str
    type: str
    message: str = ""
    source: str | None = None
    unit_type: Literal["source", "keyword", "account", "stage"] | None = None
    unit_name: str | None = None
    status: str | None = None
    current_count: int | None = None
    max_count: int | None = None
    expected_min_count: int | None = None
    progress: float | None = None
    created_at: str


class JobSnapshot(BaseModel):
    job_id: str
    status: JobStatus
    run_mode: RunMode
    execution_mode: ExecutionMode
    created_at: str
    updated_at: str
    events_count: int = 0
    artifacts: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 3: Implement config service**

Create `web/backend/config_service.py`:

```python
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from config.app_config import ConfigValidationError, load_app_config


class ConfigWriteError(ValueError):
    pass


def read_yaml_config(config_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigWriteError("config.yaml root must be a mapping")
    return payload


def write_validated_config(config_path: Path, data: dict[str, Any]) -> None:
    config_path = config_path.resolve()
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")
    backup_path = config_path.with_name(
        f"{config_path.name}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    rendered = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    tmp_path.write_text(rendered, encoding="utf-8")
    try:
        load_app_config(tmp_path)
    except (ConfigValidationError, ValueError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise ConfigWriteError(str(exc)) from exc
    if config_path.exists():
        backup_path.write_text(original, encoding="utf-8")
    tmp_path.replace(config_path)
```

- [ ] **Step 4: Implement env service**

Create `web/backend/env_service.py`:

```python
from __future__ import annotations

from pathlib import Path


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return f"{value[:4]}••••••{value[-4:]}"


def read_env_value(env_path: Path, key: str) -> str:
    if not env_path.exists():
        return ""
    prefix = f"{key}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def write_env_value(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    prefix = f"{key}="
    replaced = False
    new_lines = []
    for line in lines:
        if line.startswith(prefix):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_web_config_service.py -q
```

Expected: all pass.

---

### Task 5: Add Job Store and Progress Helpers

**Files:**
- Create: `web/backend/job_store.py`
- Create: `web/backend/progress.py`
- Test: `tests/test_job_store.py`
- Test: `tests/test_progress.py`

- [ ] **Step 1: Write job store tests**

Create `tests/test_job_store.py`:

```python
import json
from pathlib import Path

from web.backend.job_store import JobStore


def test_job_store_writes_status_and_events(tmp_path: Path):
    store = JobStore(tmp_path)
    snapshot = store.create_job(run_mode="collect_only", execution_mode="serial")

    store.append_event(snapshot.job_id, type="source_started", message="start", source="aihot")
    loaded = store.load_job(snapshot.job_id)

    assert loaded.events_count == 1
    assert (tmp_path / snapshot.job_id / "status.json").exists()
    event_lines = (tmp_path / snapshot.job_id / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(event_lines[0])["source"] == "aihot"
```

- [ ] **Step 2: Write progress tests**

Create `tests/test_progress.py`:

```python
from web.backend.progress import count_progress, expected_count_warning


def test_count_progress_uses_max_count():
    assert count_progress(current_count=5, max_count=10) == 0.5
    assert count_progress(current_count=12, max_count=10) == 1.0


def test_expected_count_warning_is_not_failure():
    warning = expected_count_warning(unit_name="AI education", current_count=2, expected_min_count=3)
    assert warning == "AI education 低于预期：2/3"
    assert expected_count_warning("AI education", 3, 3) == ""
```

- [ ] **Step 3: Implement job store**

Create `web/backend/job_store.py`:

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from web.backend.models import ExecutionMode, JobEvent, JobSnapshot, RunMode


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class JobStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create_job(self, run_mode: RunMode, execution_mode: ExecutionMode) -> JobSnapshot:
        job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
        now = utc_now_iso()
        snapshot = JobSnapshot(
            job_id=job_id,
            status="queued",
            run_mode=run_mode,
            execution_mode=execution_mode,
            created_at=now,
            updated_at=now,
        )
        self.job_dir(job_id).mkdir(parents=True, exist_ok=False)
        self.save_job(snapshot)
        return snapshot

    def job_dir(self, job_id: str) -> Path:
        return self.root / job_id

    def save_job(self, snapshot: JobSnapshot) -> None:
        path = self.job_dir(snapshot.job_id) / "status.json"
        path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    def load_job(self, job_id: str) -> JobSnapshot:
        path = self.job_dir(job_id) / "status.json"
        return JobSnapshot.model_validate_json(path.read_text(encoding="utf-8"))

    def update_job(self, snapshot: JobSnapshot, **changes) -> JobSnapshot:
        updated = snapshot.model_copy(update={**changes, "updated_at": utc_now_iso()})
        self.save_job(updated)
        return updated

    def append_event(self, job_id: str, **event_fields) -> JobEvent:
        event = JobEvent(job_id=job_id, created_at=utc_now_iso(), **event_fields)
        event_path = self.job_dir(job_id) / "events.jsonl"
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
        snapshot = self.load_job(job_id)
        self.save_job(snapshot.model_copy(update={
            "events_count": snapshot.events_count + 1,
            "updated_at": utc_now_iso(),
        }))
        return event
```

- [ ] **Step 4: Implement progress helpers**

Create `web/backend/progress.py`:

```python
from __future__ import annotations


def count_progress(current_count: int, max_count: int) -> float:
    if max_count <= 0:
        return 0.0
    return min(1.0, max(0.0, current_count / max_count))


def expected_count_warning(
    unit_name: str,
    current_count: int,
    expected_min_count: int,
) -> str:
    if expected_min_count <= 0 or current_count >= expected_min_count:
        return ""
    return f"{unit_name} 低于预期：{current_count}/{expected_min_count}"
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_job_store.py tests/test_progress.py -q
```

Expected: all pass.

---

### Task 6: Implement Job Runner with Scoring Toggle

**Files:**
- Create: `web/backend/job_runner.py`
- Modify: `main.py`
- Test: `tests/test_job_runner.py`

- [ ] **Step 1: Write runner tests**

Create `tests/test_job_runner.py`:

```python
from pathlib import Path

from models.hotspot import EducationHotspot
from web.backend.job_runner import JobArtifacts, run_merge_score_report


def test_run_merge_score_report_skips_scoring_when_disabled(tmp_path: Path, monkeypatch):
    item = EducationHotspot(
        title="测试",
        source="aihot",
        publish_time=__import__("datetime").datetime.now(),
        content="正文",
        url="https://example.com",
    )

    artifacts = run_merge_score_report(
        hotspots=[item],
        selected_sources=["aihot"],
        scoring_enabled=False,
        output_root=tmp_path,
    )

    assert isinstance(artifacts, JobArtifacts)
    assert artifacts.merged_file
    assert artifacts.scored_file == ""
    assert artifacts.report_file == ""
```

- [ ] **Step 2: Refactor main task functions lightly**

In `main.py`, add optional `scoring_enabled` parameter to `run_collection_task` and check it after merge:

```python
def run_collection_task(
    sources: list[str] | None = None,
    keyword_override: list[str] | None = None,
    scoring_enabled: bool | None = None,
) -> bool:
```

After `merged_file` is generated:

```python
enabled_scoring = SCORING_ENABLED if scoring_enabled is None else scoring_enabled
if not enabled_scoring:
    logger.info("打分已关闭，本次只输出 merged JSON")
    return True
```

Import `SCORING_ENABLED` from `config.settings`.

- [ ] **Step 3: Implement merge/score/report helper**

Create `web/backend/job_runner.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.settings import TOP_N_SELECT_COUNT
from formatters.markdown import MarkdownGenerator
from merger.data_merger import DataMerger
from models.hotspot import EducationHotspot
from scorers.scorer import ContentScorer


@dataclass
class JobArtifacts:
    merged_file: str = ""
    scored_file: str = ""
    report_file: str = ""


def run_merge_score_report(
    hotspots: list[EducationHotspot],
    selected_sources: list[str],
    scoring_enabled: bool,
    output_root: Path | None = None,
) -> JobArtifacts:
    if output_root:
        output_root.mkdir(parents=True, exist_ok=True)
    merged_dir = output_root / "merged_data" if output_root else Path("./merged_data")
    scored_dir = output_root / "scored_data" if output_root else Path("./scored_data")
    report_dir = output_root / "output" if output_root else None

    merged_file = DataMerger(output_dir=str(merged_dir)).merge_sources(
        hotspots,
        source_names=selected_sources,
    )
    if not scoring_enabled:
        return JobArtifacts(merged_file=merged_file)

    scorer = ContentScorer()
    scored_hotspots = scorer.score_batch(hotspots)
    scored_file = DataMerger(output_dir=str(scored_dir)).merge_sources(
        scored_hotspots,
        source_names=selected_sources,
    )
    top_hotspots = scorer.select_top_n(scored_hotspots, TOP_N_SELECT_COUNT)
    generator = MarkdownGenerator()
    if report_dir:
        generator.output_dir = report_dir
        generator.output_dir.mkdir(parents=True, exist_ok=True)
    report_file = generator.generate_daily_report(top_hotspots)
    return JobArtifacts(
        merged_file=merged_file,
        scored_file=scored_file,
        report_file=report_file,
    )
```

- [ ] **Step 4: Run runner tests**

Run:

```bash
python -m pytest tests/test_job_runner.py -q
```

Expected: pass.

---

### Task 7: Implement FastAPI App and Routes

**Files:**
- Create: `web/backend/app.py`
- Modify: `web/backend/config_service.py`
- Modify: `web/backend/env_service.py`

- [ ] **Step 1: Implement app skeleton**

Create `web/backend/app.py`:

```python
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from web.backend.config_service import ConfigWriteError, read_yaml_config, write_validated_config
from web.backend.env_service import mask_secret, read_env_value, write_env_value
from web.backend.job_store import JobStore
from web.backend.models import ConfigResponse, JobCreateRequest, SaveConfigRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"
JOBS_ROOT = PROJECT_ROOT / "web_jobs"

app = FastAPI(title="AITrend Web Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_store = JobStore(JOBS_ROOT)


@app.get("/api/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    api_key = read_env_value(ENV_PATH, "LLM_API_KEY")
    return ConfigResponse(
        config=read_yaml_config(CONFIG_PATH),
        masked_api_key=mask_secret(api_key),
        has_api_key=bool(api_key),
    )


@app.put("/api/config")
def save_config(request: SaveConfigRequest):
    if request.api_key is not None and request.api_key.strip():
        write_env_value(ENV_PATH, "LLM_API_KEY", request.api_key.strip())
    try:
        write_validated_config(CONFIG_PATH, request.config)
    except ConfigWriteError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "ok"}


@app.post("/api/jobs")
def create_job(request: JobCreateRequest):
    snapshot = job_store.create_job(
        run_mode=request.run_mode,
        execution_mode=request.execution_mode,
    )
    job_store.append_event(snapshot.job_id, type="job_created", message="任务已创建")
    return snapshot


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    return job_store.load_job(job_id)


@app.get("/api/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    event_path = job_store.job_dir(job_id) / "events.jsonl"

    async def event_stream():
        offset = 0
        while True:
            if event_path.exists():
                content = event_path.read_text(encoding="utf-8")
                if len(content) > offset:
                    chunk = content[offset:]
                    offset = len(content)
                    for line in chunk.splitlines():
                        yield f"data: {line}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 2: Smoke test app import**

Run:

```bash
python - <<'PY'
from web.backend.app import app
print(app.title)
PY
```

Expected output contains:

```text
AITrend Web Dashboard
```

---

### Task 8: Build React Frontend Shell

**Files:**
- Create all `web/frontend/*` files listed in File Structure.

- [ ] **Step 1: Create package.json**

Create `web/frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "tsc && vite build",
    "preview": "vite preview --host 127.0.0.1 --port 4173"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0",
    "typescript": "^5.5.4",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {}
}
```

- [ ] **Step 2: Create TypeScript and Vite config**

Create `web/frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

Create `web/frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8787"
    }
  }
});
```

- [ ] **Step 3: Create React entry**

Create `web/frontend/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

Create `web/frontend/src/main.tsx`:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 4: Create shared types and API client**

Create `web/frontend/src/types.ts`:

```ts
export type PageKey = "dashboard" | "sources" | "scoring" | "history" | "reports" | "system";
export type RunMode = "collect_only" | "collect_score_report";
export type ExecutionMode = "serial" | "parallel";

export interface ConfigResponse {
  config: Record<string, unknown>;
  masked_api_key: string;
  has_api_key: boolean;
}

export interface JobSnapshot {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  run_mode: RunMode;
  execution_mode: ExecutionMode;
  created_at: string;
  updated_at: string;
  events_count: number;
  artifacts: Record<string, unknown>;
  errors: string[];
  warnings: string[];
}
```

Create `web/frontend/src/api.ts`:

```ts
import type { ConfigResponse, ExecutionMode, JobSnapshot, RunMode } from "./types";

export async function fetchConfig(): Promise<ConfigResponse> {
  const response = await fetch("/api/config");
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function saveConfig(config: Record<string, unknown>, apiKey?: string): Promise<void> {
  const response = await fetch("/api/config", {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({config, api_key: apiKey || null})
  });
  if (!response.ok) throw new Error(await response.text());
}

export async function createJob(runMode: RunMode, executionMode: ExecutionMode): Promise<JobSnapshot> {
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({run_mode: runMode, execution_mode: executionMode})
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
```

- [ ] **Step 5: Create app shell and navigation**

Create `web/frontend/src/App.tsx`:

```tsx
import { useState } from "react";
import { TopNav } from "./components/TopNav";
import { DashboardPage } from "./pages/DashboardPage";
import { SourcesPage } from "./pages/SourcesPage";
import { ScoringPage } from "./pages/ScoringPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SystemStatusPage } from "./pages/SystemStatusPage";
import type { PageKey } from "./types";

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  return (
    <div className="app-shell">
      <TopNav activePage={page} onNavigate={setPage} />
      {page === "dashboard" && <DashboardPage onNavigate={setPage} />}
      {page === "sources" && <SourcesPage />}
      {page === "scoring" && <ScoringPage />}
      {page === "history" && <HistoryPage />}
      {page === "reports" && <ReportsPage />}
      {page === "system" && <SystemStatusPage />}
    </div>
  );
}
```

Create `web/frontend/src/components/TopNav.tsx`:

```tsx
import type { PageKey } from "../types";

const navItems: Array<{key: PageKey; label: string}> = [
  {key: "dashboard", label: "主工作台"},
  {key: "sources", label: "来源配置"},
  {key: "scoring", label: "打分模型"},
  {key: "history", label: "任务历史"},
  {key: "reports", label: "结果报告"},
  {key: "system", label: "系统状态"}
];

export function TopNav({activePage, onNavigate}: {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}) {
  return (
    <header className="top-nav">
      <div className="brand"><span className="brand-mark" />AITrend</div>
      <nav className="nav-links">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={item.key === activePage ? "nav-link active" : "nav-link"}
            onClick={() => onNavigate(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <button className="ghost-button">设置</button>
    </header>
  );
}
```

- [ ] **Step 6: Create styling**

Create `web/frontend/src/styles.css` with blue/white/gray grid styling:

```css
* { box-sizing: border-box; }
body {
  margin: 0;
  color: #111827;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f8fafc;
  background-image:
    linear-gradient(#e8edf5 1px, transparent 1px),
    linear-gradient(90deg, #e8edf5 1px, transparent 1px);
  background-size: 42px 42px;
}
button, input, textarea, select { font: inherit; }
.top-nav {
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  border-bottom: 1px solid #d8dee8;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(10px);
}
.brand { display: flex; align-items: center; gap: 12px; font-size: 22px; font-weight: 800; }
.brand-mark { width: 18px; height: 18px; background: #1261ff; display: inline-block; }
.nav-links { display: flex; align-items: center; gap: 22px; }
.nav-link {
  border: 0;
  background: transparent;
  color: #4b5563;
  padding: 10px 16px;
  cursor: pointer;
}
.nav-link.active {
  color: #1261ff;
  border: 1px solid #c8d3e3;
  background: #f8fbff;
}
.ghost-button {
  border: 1px solid #cfd8e3;
  background: white;
  color: #374151;
  padding: 9px 14px;
  border-radius: 4px;
}
.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 44px 22px;
}
.hero { text-align: center; margin-bottom: 32px; }
.hero h1 { font-size: 44px; line-height: 1.08; margin: 18px 0 10px; letter-spacing: 0; }
.subtitle { color: #6b7280; font-size: 16px; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #cfd8e3;
  background: white;
  padding: 7px 14px;
  font-size: 13px;
}
.badge-dot { width: 8px; height: 8px; border-radius: 999px; background: #22c55e; }
.card {
  background: rgba(255,255,255,.94);
  border: 1px solid #d3dbe7;
  box-shadow: 0 12px 22px rgba(15,23,42,.07);
  border-radius: 4px;
  padding: 18px;
}
.primary-button {
  border: 0;
  background: #1261ff;
  color: white;
  padding: 11px 18px;
  border-radius: 4px;
  cursor: pointer;
}
.danger-text { color: #b91c1c; }
.success-text { color: #15803d; }
.warning-text { color: #92400e; }
```

- [ ] **Step 7: Run frontend install and build**

Run:

```bash
cd web/frontend
npm install
npm run build
```

Expected: build succeeds.

---

### Task 9: Build Dashboard, Source Config, and Scoring Pages

**Files:**
- Create: page and component files listed in File Structure.

- [ ] **Step 1: Implement ProgressBar**

Create `web/frontend/src/components/ProgressBar.tsx`:

```tsx
export function ProgressBar({value, tone = "blue"}: {value: number; tone?: "blue" | "green" | "amber" | "red" | "gray"}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-track">
      <div className={`progress-fill ${tone}`} style={{width: `${clamped}%`}} />
    </div>
  );
}
```

Append CSS:

```css
.progress-track { height: 8px; background: #e5e7eb; overflow: hidden; }
.progress-fill { height: 8px; transition: width 600ms ease; }
.progress-fill.blue { background: #1261ff; box-shadow: 0 0 14px rgba(18,97,255,.28); }
.progress-fill.green { background: #22c55e; }
.progress-fill.amber { background: #f59e0b; }
.progress-fill.red { background: #ef4444; }
.progress-fill.gray { background: #9ca3af; }
```

- [ ] **Step 2: Implement SourceProgressCard**

Create `web/frontend/src/components/SourceProgressCard.tsx`:

```tsx
import { ProgressBar } from "./ProgressBar";

export interface ProgressUnit {
  name: string;
  current: number;
  max: number;
  min: number;
  status: "pending" | "running" | "done" | "warning" | "failed";
}

export function SourceProgressCard({sourceName, progress, units}: {
  sourceName: string;
  progress: number;
  units: ProgressUnit[];
}) {
  const tone = units.some((unit) => unit.status === "failed")
    ? "red"
    : units.some((unit) => unit.status === "warning")
      ? "amber"
      : progress >= 100
        ? "green"
        : "blue";

  return (
    <section className="card source-card">
      <div className="source-card-header">
        <strong>{sourceName}</strong>
        <span>{Math.round(progress)}%</span>
      </div>
      <ProgressBar value={progress} tone={tone} />
      <div className="unit-list">
        {units.map((unit) => (
          <div className="unit-row" key={unit.name}>
            <div className="unit-line">
              <span>{unit.name}</span>
              <span>{unit.current} / {unit.max}</span>
            </div>
            <ProgressBar value={(unit.current / Math.max(1, unit.max)) * 100} tone={unit.status === "warning" ? "amber" : tone} />
            {unit.status === "warning" && (
              <div className="warning-text">低于预期：{unit.current}/{unit.min}</div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
```

Append CSS:

```css
.source-card-header, .unit-line { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.unit-list { display: grid; gap: 12px; margin-top: 14px; }
.unit-row { border-top: 1px solid #edf1f7; padding-top: 10px; font-size: 13px; }
```

- [ ] **Step 3: Implement DashboardPage**

Create `web/frontend/src/pages/DashboardPage.tsx`:

```tsx
import { useState } from "react";
import { createJob } from "../api";
import { SourceProgressCard } from "../components/SourceProgressCard";
import type { ExecutionMode, PageKey, RunMode } from "../types";

export function DashboardPage({onNavigate}: {onNavigate: (page: PageKey) => void}) {
  const [runMode, setRunMode] = useState<RunMode>("collect_only");
  const [executionMode, setExecutionMode] = useState<ExecutionMode>("parallel");
  const [message, setMessage] = useState("");

  async function startJob() {
    const job = await createJob(runMode, executionMode);
    setMessage(`任务已创建：${job.job_id}`);
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="badge"><span className="badge-dot" />5 个来源启用 · 默认 7 天 · 预期 3-10 篇</div>
        <h1>热点采集主工作台</h1>
        <p className="subtitle">配置从来源页读取，本页负责启动、观察进度、查看产物。</p>
      </section>
      <section className="dashboard-actions">
        <select value={runMode} onChange={(event) => setRunMode(event.target.value as RunMode)}>
          <option value="collect_only">只采集</option>
          <option value="collect_score_report">采集 + 打分 + 报告</option>
        </select>
        <select value={executionMode} onChange={(event) => setExecutionMode(event.target.value as ExecutionMode)}>
          <option value="parallel">并行</option>
          <option value="serial">串行</option>
        </select>
        <button className="primary-button" onClick={startJob}>开始采集</button>
        <button className="ghost-button" onClick={() => onNavigate("sources")}>来源配置</button>
      </section>
      {message && <p className="success-text">{message}</p>}
      <section className="source-grid">
        <SourceProgressCard sourceName="小红书" progress={62} units={[
          {name: "关键词：英语启蒙", current: 8, max: 10, min: 3, status: "running"},
          {name: "账号：闽教英语智趣点读", current: 3, max: 10, min: 3, status: "running"}
        ]} />
        <SourceProgressCard sourceName="微信公众号账号" progress={100} units={[
          {name: "账号：中国教育报", current: 7, max: 10, min: 3, status: "done"}
        ]} />
        <SourceProgressCard sourceName="Google News" progress={100} units={[
          {name: "关键词：education policy", current: 0, max: 10, min: 3, status: "warning"}
        ]} />
      </section>
    </main>
  );
}
```

Append CSS:

```css
.dashboard-actions { display: flex; justify-content: center; gap: 12px; margin-bottom: 24px; }
.dashboard-actions select { border: 1px solid #cfd8e3; background: white; padding: 10px 12px; border-radius: 4px; }
.source-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
@media (max-width: 960px) { .source-grid { grid-template-columns: 1fr; } .top-nav { padding: 0 18px; } .nav-links { gap: 8px; } }
```

- [ ] **Step 4: Build secondary page shells**

Create `SourcesPage.tsx`, `ScoringPage.tsx`, `HistoryPage.tsx`, `ReportsPage.tsx`, and `SystemStatusPage.tsx` with real page shells:

```tsx
export function SourcesPage() {
  return <main className="page"><h1>来源配置</h1><p className="subtitle">保存后写回 config.yaml，并自动备份。</p></main>;
}
```

Use equivalent content:

- `ScoringPage`: title `打分模型与提示词`
- `HistoryPage`: title `任务历史`
- `ReportsPage`: title `结果报告`
- `SystemStatusPage`: title `系统状态`

- [ ] **Step 5: Build frontend**

Run:

```bash
cd web/frontend
npm run build
```

Expected: build succeeds.

---

### Task 10: Wire Config and Scoring Pages to Backend

**Files:**
- Modify: `web/frontend/src/pages/SourcesPage.tsx`
- Modify: `web/frontend/src/pages/ScoringPage.tsx`
- Modify: `web/frontend/src/components/SourceConfigEditor.tsx`
- Modify: `web/frontend/src/components/PromptEditor.tsx`
- Modify: `web/backend/app.py`
- Modify: `web/backend/config_service.py`

- [ ] **Step 1: Add prompt read/write service functions**

In `web/backend/config_service.py`, add:

```python
REQUIRED_SCORE_FIELDS = [
    "heat", "authority", "quality", "resonance", "timeliness",
    "reference_value", "risk_control", "overall", "reason",
    "best_angle", "risk_notes",
]


def validate_scoring_prompt(user_prompt: str) -> list[str]:
    warnings = []
    if "JSON" not in user_prompt and "json" not in user_prompt:
        warnings.append("评分提示词未明确要求返回 JSON")
    missing = [field for field in REQUIRED_SCORE_FIELDS if field not in user_prompt]
    if missing:
        warnings.append("评分提示词缺少字段：" + ", ".join(missing))
    return warnings


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text_file_with_backup(path: Path, content: str) -> None:
    if path.exists():
        backup_path = path.with_name(path.name + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S"))
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

- [ ] **Step 2: Add prompt endpoints**

In `web/backend/app.py`, add:

```python
from pydantic import BaseModel
from web.backend.config_service import read_text_file, validate_scoring_prompt, write_text_file_with_backup


class PromptPayload(BaseModel):
    system_prompt: str
    user_prompt: str


@app.get("/api/scoring/prompt")
def get_scoring_prompt():
    config = read_yaml_config(CONFIG_PATH)
    prompt_config = config.get("scoring", {}).get("prompt", {})
    system_path = PROJECT_ROOT / prompt_config.get("system_path", "./prompts/scoring_system_prompt.md")
    user_path = PROJECT_ROOT / prompt_config.get("user_path", "./prompts/scoring_user_prompt.md")
    return {
        "system_prompt": read_text_file(system_path),
        "user_prompt": read_text_file(user_path),
        "warnings": validate_scoring_prompt(read_text_file(user_path)),
    }


@app.put("/api/scoring/prompt")
def save_scoring_prompt(payload: PromptPayload):
    config = read_yaml_config(CONFIG_PATH)
    prompt_config = config.get("scoring", {}).get("prompt", {})
    system_path = PROJECT_ROOT / prompt_config.get("system_path", "./prompts/scoring_system_prompt.md")
    user_path = PROJECT_ROOT / prompt_config.get("user_path", "./prompts/scoring_user_prompt.md")
    warnings = validate_scoring_prompt(payload.user_prompt)
    write_text_file_with_backup(system_path, payload.system_prompt)
    write_text_file_with_backup(user_path, payload.user_prompt)
    return {"status": "ok", "warnings": warnings}
```

- [ ] **Step 3: Implement SourceConfigEditor and SourcesPage**

Create `web/frontend/src/components/SourceConfigEditor.tsx`:

```tsx
interface SourceConfigEditorProps {
  title: string;
  enabled: boolean;
  keywords: string[];
  accounts: string[];
  days: number;
  expectedMin: number;
  maxResults: number;
  accountLabel: string;
  onChange: (next: {
    enabled: boolean;
    keywords: string[];
    accounts: string[];
    days: number;
    expectedMin: number;
    maxResults: number;
  }) => void;
}

function splitLines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

export function SourceConfigEditor(props: SourceConfigEditorProps) {
  return (
    <section className="card source-config-card">
      <div className="source-card-header">
        <strong>{props.title}</strong>
        <label className="field-row compact">
          <span>{props.enabled ? "启用" : "关闭"}</span>
          <input
            type="checkbox"
            checked={props.enabled}
            onChange={(event) => props.onChange({...props, enabled: event.target.checked})}
          />
        </label>
      </div>
      <div className="source-config-grid">
        <label className="field-label">关键词
          <textarea
            value={props.keywords.join("\n")}
            onChange={(event) => props.onChange({...props, keywords: splitLines(event.target.value)})}
          />
        </label>
        <label className="field-label">{props.accountLabel}
          <textarea
            value={props.accounts.join("\n")}
            onChange={(event) => props.onChange({...props, accounts: splitLines(event.target.value)})}
          />
        </label>
      </div>
      <div className="source-number-grid">
        <label className="field-label">天数
          <input type="number" value={props.days} onChange={(event) => props.onChange({...props, days: Number(event.target.value)})} />
        </label>
        <label className="field-label">最少篇数
          <input type="number" value={props.expectedMin} onChange={(event) => props.onChange({...props, expectedMin: Number(event.target.value)})} />
        </label>
        <label className="field-label">最多篇数
          <input type="number" value={props.maxResults} onChange={(event) => props.onChange({...props, maxResults: Number(event.target.value)})} />
        </label>
      </div>
    </section>
  );
}
```

Create `web/frontend/src/pages/SourcesPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchConfig, saveConfig } from "../api";
import { SourceConfigEditor } from "../components/SourceConfigEditor";

function hoursToDays(maxHours: number | undefined): number {
  return Math.max(1, Math.round((maxHours || 168) / 24));
}

function daysToTimeRange(days: number) {
  return {min: 0, max: Math.max(1, days) * 24};
}

export function SourcesPage() {
  const [config, setConfig] = useState<Record<string, any> | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchConfig().then((response) => setConfig(response.config));
  }, []);

  async function save() {
    if (!config) return;
    await saveConfig(config);
    setMessage("来源配置已保存到 config.yaml");
  }

  if (!config) return <main className="page"><p>正在读取来源配置...</p></main>;
  const enabledSources = new Set<string>(config.enabled_sources || []);
  const xhs = config.xiaohongshu || {};
  const keywordSearch = xhs.keyword_search || {};
  const accountCrawl = xhs.account_crawl || {};

  return (
    <main className="page">
      <section className="hero">
        <div className="badge"><span className="badge-dot" />默认 7 天 · 最少 3 · 最多 10</div>
        <h1>来源配置</h1>
        <p className="subtitle">保存后写回 config.yaml，并自动备份。</p>
      </section>
      <SourceConfigEditor
        title="小红书"
        enabled={enabledSources.has("xiaohongshu")}
        keywords={keywordSearch.keywords || []}
        accounts={accountCrawl.creator_urls || []}
        accountLabel="账号主页 URL"
        days={hoursToDays(keywordSearch.time_range_hours?.max)}
        expectedMin={keywordSearch.expected_min_results ?? 3}
        maxResults={keywordSearch.max_results_per_keyword ?? 10}
        onChange={(next) => {
          const nextEnabled = new Set(enabledSources);
          if (next.enabled) nextEnabled.add("xiaohongshu"); else nextEnabled.delete("xiaohongshu");
          setConfig({
            ...config,
            enabled_sources: Array.from(nextEnabled),
            xiaohongshu: {
              ...xhs,
              keyword_search: {
                ...keywordSearch,
                keywords: next.keywords,
                expected_min_results: next.expectedMin,
                max_results_per_keyword: next.maxResults,
                time_range_hours: daysToTimeRange(next.days)
              },
              account_crawl: {
                ...accountCrawl,
                creator_urls: next.accounts,
                expected_min_results: next.expectedMin,
                max_results_per_account: next.maxResults,
                time_range_hours: daysToTimeRange(next.days)
              }
            }
          });
        }}
      />
      <button className="primary-button save-row" onClick={save}>保存为默认配置</button>
      {message && <p className="success-text">{message}</p>}
    </main>
  );
}
```

Append CSS:

```css
.source-config-card { margin-bottom: 18px; }
.source-config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.source-number-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
.field-label { display: grid; gap: 8px; color: #374151; font-size: 13px; }
.field-label input, .field-label textarea {
  border: 1px solid #cfd8e3;
  border-radius: 4px;
  padding: 10px 12px;
  background: white;
  color: #111827;
}
.field-label textarea { min-height: 110px; resize: vertical; }
.field-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.field-row.compact { justify-content: flex-end; font-size: 13px; }
.save-row { margin-top: 8px; }
.scoring-layout { display: grid; grid-template-columns: 360px 1fr; gap: 18px; }
.scoring-panel { display: grid; gap: 12px; align-content: start; }
@media (max-width: 960px) {
  .source-config-grid, .source-number-grid, .scoring-layout { grid-template-columns: 1fr; }
}
```

- [ ] **Step 4: Implement PromptEditor**

Create `PromptEditor.tsx`:

```tsx
export function PromptEditor({label, value, onChange}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="prompt-editor">
      <span>{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}
```

Append CSS:

```css
.prompt-editor { display: grid; gap: 8px; }
.prompt-editor textarea {
  min-height: 220px;
  width: 100%;
  border: 1px solid #cfd8e3;
  border-radius: 4px;
  padding: 12px;
  resize: vertical;
  background: #fff;
}
```

- [ ] **Step 5: Implement ScoringPage**

Create `web/frontend/src/pages/ScoringPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchConfig, saveConfig } from "../api";
import { PromptEditor } from "../components/PromptEditor";

interface PromptResponse {
  system_prompt: string;
  user_prompt: string;
  warnings: string[];
}

export function ScoringPage() {
  const [config, setConfig] = useState<Record<string, any> | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [maskedKey, setMaskedKey] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userPrompt, setUserPrompt] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchConfig().then((response) => {
      setConfig(response.config);
      setMaskedKey(response.masked_api_key);
    });
    fetch("/api/scoring/prompt")
      .then((response) => response.json())
      .then((payload: PromptResponse) => {
        setSystemPrompt(payload.system_prompt);
        setUserPrompt(payload.user_prompt);
        setWarnings(payload.warnings || []);
      });
  }, []);

  async function saveAll() {
    if (!config) return;
    await saveConfig(config, apiKey || undefined);
    const response = await fetch("/api/scoring/prompt", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({system_prompt: systemPrompt, user_prompt: userPrompt})
    });
    if (!response.ok) throw new Error(await response.text());
    const payload = await response.json();
    setWarnings(payload.warnings || []);
    setMessage("打分配置已保存");
  }

  if (!config) return <main className="page"><p>正在读取打分配置...</p></main>;
  const scoring = (config.scoring || {}) as Record<string, any>;

  function updateScoring(key: string, value: unknown) {
    setConfig({...config, scoring: {...scoring, [key]: value}});
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="badge"><span className="badge-dot" />打分模型</div>
        <h1>打分模型与提示词</h1>
        <p className="subtitle">关闭打分时只输出 merged JSON；开启后生成 scored JSON 和报告。</p>
      </section>
      <section className="scoring-layout">
        <div className="card scoring-panel">
          <label className="field-row">
            <span>启用打分</span>
            <input
              type="checkbox"
              checked={Boolean(scoring.enabled)}
              onChange={(event) => updateScoring("enabled", event.target.checked)}
            />
          </label>
          <label className="field-label">Base URL
            <input value={scoring.base_url || ""} onChange={(event) => updateScoring("base_url", event.target.value)} />
          </label>
          <label className="field-label">Model
            <input value={scoring.model || ""} onChange={(event) => updateScoring("model", event.target.value)} />
          </label>
          <label className="field-label">API Key
            <input placeholder={maskedKey || "未配置"} value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
          </label>
          <label className="field-label">并发数
            <input type="number" value={scoring.workers || 5} onChange={(event) => updateScoring("workers", Number(event.target.value))} />
          </label>
          <button className="primary-button" onClick={saveAll}>保存并验证</button>
          {message && <p className="success-text">{message}</p>}
          {warnings.map((warning) => <p className="warning-text" key={warning}>{warning}</p>)}
        </div>
        <div className="card">
          <PromptEditor label="System Prompt" value={systemPrompt} onChange={setSystemPrompt} />
          <PromptEditor label="User Prompt Template" value={userPrompt} onChange={setUserPrompt} />
        </div>
      </section>
    </main>
  );
}
```

The implementation must mask existing key and only send `api_key` if the user enters a new value.

- [ ] **Step 6: Manual verification**

Start backend:

```bash
uvicorn web.backend.app:app --host 127.0.0.1 --port 8787
```

Start frontend:

```bash
cd web/frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Expected:

- `来源配置` loads config.
- `打分模型` loads model config and prompt text.
- Save config creates `config.yaml.bak.*`.

---

### Task 11: Add Real Job Execution and SSE Updates

**Files:**
- Modify: `web/backend/job_runner.py`
- Modify: `web/backend/app.py`
- Modify: `web/frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Implement background job launch**

In `web/backend/app.py`, replace `create_job` route with a background thread runner:

```python
from threading import Thread
from web.backend.job_runner import run_web_job


@app.post("/api/jobs")
def create_job(request: JobCreateRequest):
    snapshot = job_store.create_job(
        run_mode=request.run_mode,
        execution_mode=request.execution_mode,
    )
    job_store.append_event(snapshot.job_id, type="job_created", message="任务已创建")
    thread = Thread(target=run_web_job, args=(snapshot.job_id, job_store, CONFIG_PATH), daemon=True)
    thread.start()
    return snapshot
```

- [ ] **Step 2: Implement single-source collection helpers**

In `web/backend/job_runner.py`, add:

```python
from config.app_config import load_app_config
from crawlers.manager import CrawlerManager


def collect_one_source(source_name: str, manager: CrawlerManager):
    crawler = manager.crawlers[source_name]
    keyword_time_range = manager._keyword_time_range_for_source(source_name, None)
    account_time_range = manager._account_time_range_for_source(source_name, None)
    keywords = manager._keywords_for_source(source_name, None, None)
    creator_urls = manager._creator_urls_for_source(source_name, None)
    if source_name in {"xiaohongshu", "zhihu"}:
        return crawler.collect(
            keywords,
            time_range_hours=keyword_time_range,
            creator_urls=creator_urls,
            creator_time_range_hours=account_time_range,
        )
    if source_name == "wechat_mp":
        return crawler.collect(keywords, time_range_hours=account_time_range)
    return crawler.collect(keywords, time_range_hours=keyword_time_range)


def collect_sources_serial(job_id: str, job_store, manager: CrawlerManager) -> list[EducationHotspot]:
    all_items: list[EducationHotspot] = []
    for source_name in manager.crawlers:
        job_store.append_event(job_id, type="source_started", source=source_name, message=f"{source_name} 开始")
        result = collect_one_source(source_name, manager)
        all_items.extend(result.items)
        job_store.append_event(
            job_id,
            type="source_completed",
            source=source_name,
            message=f"{source_name} 完成",
            current_count=len(result.items),
        )
    return all_items
```

- [ ] **Step 3: Implement run_web_job serial path**

In `web/backend/job_runner.py`, add:

```python
def run_web_job(job_id: str, job_store, config_path: Path) -> None:
    snapshot = job_store.load_job(job_id)
    snapshot = job_store.update_job(snapshot, status="running")
    config = load_app_config(config_path)
    selected_sources = config.enabled_sources
    job_store.append_event(job_id, type="job_started", message="任务开始")
    try:
        manager = CrawlerManager(enabled_sources=selected_sources)
        hotspots = collect_sources_serial(job_id, job_store, manager)
        artifacts = run_merge_score_report(
            hotspots=hotspots,
            selected_sources=selected_sources,
            scoring_enabled=snapshot.run_mode == "collect_score_report" and config.scoring.enabled,
            output_root=job_store.job_dir(job_id),
        )
        snapshot = job_store.load_job(job_id)
        job_store.save_job(snapshot.model_copy(update={
            "status": "succeeded",
            "artifacts": artifacts.__dict__,
        }))
        job_store.append_event(job_id, type="job_completed", message="任务完成")
    except Exception as exc:
        snapshot = job_store.load_job(job_id)
        job_store.save_job(snapshot.model_copy(update={
            "status": "failed",
            "errors": snapshot.errors + [str(exc)],
        }))
        job_store.append_event(job_id, type="job_failed", message=str(exc))
```

- [ ] **Step 4: Add frontend SSE connection**

In `DashboardPage.tsx`, after `createJob`, open:

```tsx
const events = new EventSource(`/api/jobs/${job.job_id}/events`);
events.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  setMessage(payload.message || payload.type);
};
events.onerror = () => events.close();
```

- [ ] **Step 5: Verify with a lightweight source**

Set `enabled_sources` temporarily to `aihot` in the UI or config, then run:

```bash
uvicorn web.backend.app:app --host 127.0.0.1 --port 8787
```

Start a frontend job in `只采集` mode.

Expected:

- `web_jobs/<job_id>/status.json` exists.
- `events.jsonl` receives events.
- `merged_data` under job directory contains one merged file.

---

### Task 12: Add Source-Level Parallel Collection

**Files:**
- Modify: `web/backend/job_runner.py`
- Test: `tests/test_job_runner.py`

- [ ] **Step 1: Add test for parallel merge once**

Append to `tests/test_job_runner.py`:

```python
def test_parallel_mode_is_declared_as_source_level_only():
    from web.backend.job_runner import MAX_SOURCE_WORKERS

    assert MAX_SOURCE_WORKERS == 3
```

- [ ] **Step 2: Implement bounded parallel collection**

In `web/backend/job_runner.py`, add:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_SOURCE_WORKERS = 3


def collect_sources_parallel(job_id: str, job_store, manager: CrawlerManager) -> list[EducationHotspot]:
    all_items: list[EducationHotspot] = []
    with ThreadPoolExecutor(max_workers=min(MAX_SOURCE_WORKERS, len(manager.crawlers))) as executor:
        future_to_source = {
            executor.submit(collect_one_source, source_name, manager): source_name
            for source_name in manager.crawlers
        }
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                result = future.result()
                all_items.extend(result.items)
                job_store.append_event(
                    job_id,
                    type="source_completed",
                    source=source_name,
                    message=f"{source_name} 完成",
                    current_count=len(result.items),
                )
            except Exception as exc:
                job_store.append_event(
                    job_id,
                    type="source_failed",
                    source=source_name,
                    message=str(exc),
                    status="failed",
                )
    return all_items
```

In `run_web_job`, branch on snapshot execution mode:

```python
if snapshot.execution_mode == "parallel":
    hotspots = collect_sources_parallel(job_id, job_store, manager)
else:
    hotspots = collect_sources_serial(job_id, job_store, manager)
```

- [ ] **Step 3: Run tests**

Run:

```bash
python -m pytest tests/test_job_runner.py -q
```

Expected: pass.

---

### Task 13: Final Verification

**Files:**
- All files touched above.

- [ ] **Step 1: Run backend tests**

Run:

```bash
python -m pytest tests/test_scoring_config.py tests/test_web_config_service.py tests/test_job_store.py tests/test_progress.py tests/test_job_runner.py -q
```

Expected: all pass.

- [ ] **Step 2: Run existing tests most likely affected**

Run:

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_xiaohongshu_crawler_modes.py tests/test_zhihu_crawler_modes.py tests/test_aihot_crawler.py -q
```

Expected: all pass.

- [ ] **Step 3: Build frontend**

Run:

```bash
cd web/frontend
npm run build
```

Expected: `dist/` build succeeds.

- [ ] **Step 4: Start local dev servers**

Run backend:

```bash
uvicorn web.backend.app:app --host 127.0.0.1 --port 8787
```

Run frontend:

```bash
cd web/frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Expected:

- Blue/white/gray dashboard loads.
- Navigation switches pages.
- Config page can load `config.yaml`.
- Scoring page can show masked API key and prompt text.
- A lightweight `aihot` collect-only job can start and write `web_jobs/<job_id>/`.

- [ ] **Step 5: Post-change risk review**

Check:

```bash
git status --short
git diff --stat
```

Review whether changes introduced these risks:

- API key leaked into `config.yaml` or logs.
- Prompt extraction changed scoring semantics.
- Parallel mode caused shared output path contention.
- Config save can overwrite invalid YAML.
- Frontend progress can display 100% before backend completion.

If any risk is present, document it before expanding implementation scope.
