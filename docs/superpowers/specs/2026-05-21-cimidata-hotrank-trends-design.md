# CimiData Hotrank Trends Design

Date: 2026-05-21

## Goal

Build a dedicated Web subpage in `AITrend-aihot` that lets the operator manually fetch CimiData hotrank data, aggregate mainstream platform hot lists into current cross-platform trend topics, and show a Top 10 trend chart plus evidence.

The page must not call CimiData just because the user opens it. Opening the page reads only the latest local snapshot if one exists. A new CimiData request happens only after the operator clicks a refresh/generate button.

## Current Code Facts

- `AITrend-aihot` already has a FastAPI backend and React frontend under `web/`.
- `web/backend/job_runner.py` is built around full collection jobs, but CimiData hotrank is not a normal keyword or account source. It is a snapshot-style hot list aggregator.
- `config/app_config.py` currently supports these normal sources: `wechat`, `wechat_mp`, `xiaohongshu`, `zhihu`, `google_news`, and `aihot`.
- `models/hotspot.py` is useful for normal collected items, but hotrank trends need an additional topic model because one topic can have multiple source evidences.
- Existing Markdown report categorization is a display-layer keyword rule focused on education/social content. It should not be reused as the full product taxonomy for general web trends.

## API Fact

CimiData hotrank endpoint:

```text
GET https://api.cimidata.com/api/v3/hotrank?access_token=<token>&channel_id=<id>
```

Current verified channels:

| channel_id | Channel |
| ---: | --- |
| 1 | 微博 |
| 2 | 知乎 |
| 3 | 百度 |
| 4 | 抖音 |
| 5 | 头条 |
| 7 | B站 |

Each successful channel currently returns 50 rows shaped like:

```json
{
  "created_at": "2026-05-21T10:10:16",
  "hot": "7904600",
  "hot_tag": "热",
  "id": 1964254,
  "summary": "Only Baidu commonly has summary text.",
  "title": "中俄迈向更高质量的全面战略协作",
  "url": "https://www.baidu.com/s?wd=..."
}
```

The API returns platform hot-list snapshots. It does not return true global search volume, article bodies, or long-term trend curves by itself.

## Non-Goals

- Do not add automatic polling on page load.
- Do not run this as part of the existing full collection job.
- Do not expose `access_token`, `CIMIDATA_APP_ID`, or `CIMIDATA_APP_SECRET` to the frontend.
- Do not claim the score is real all-network search volume. It is a derived trend score from hot-list evidence.
- Do not add database infrastructure in the first version. Local JSON snapshots are enough.
- Do not add an LLM clustering dependency in the first version. Deterministic clustering is easier to debug and cheaper to run.

## Approaches Considered

### Approach A: Add `cimidata_hotrank` As A Normal Crawler Source

This would plug hotrank rows into `CrawlerManager -> EducationHotspot -> scorer/report`.

Pros:

- Reuses existing merged JSON and report pipeline.
- Small backend surface if only command-line reports are needed.

Cons:

- Hotrank is not keyword/account collection.
- A trend topic needs many evidence rows, but `EducationHotspot` models one item.
- Page-level manual refresh and snapshot display would still need custom APIs.

### Approach B: Build A Dedicated Hotrank Subpage And Service

Create a separate backend service for CimiData hotrank snapshots, aggregation, scoring, and frontend display.

Pros:

- Matches the product shape: manual click, current snapshot, Top 10 chart.
- Keeps token handling and API cost control isolated.
- Allows topic-level models with evidence lists and score breakdowns.
- Does not disturb the existing source matrix.

Cons:

- Adds a parallel service path beside normal collection jobs.
- Needs new tests for aggregation and frontend page behavior.

### Approach C: Put It In OpenClaw As An Ops Query Tool

Add a script/reference under longxia OpenClaw for ad-hoc operator questions.

Pros:

- Fastest to use in chat.
- Good for one-off operational analysis.

Cons:

- Poor fit for a browsable trend chart.
- Harder to preserve snapshots, inspect evidence, and tune scoring.
- Keeps the feature as an agent trick instead of a product capability.

Recommended: Approach B. It is the cleanest boundary for a manual, page-level trend product.

## Product Behavior

### Navigation

Add a new Web navigation item:

```text
全网热榜
```

The route should be:

```text
/hotrank
```

### Page Load

When the operator opens `/hotrank`:

- The frontend calls a local backend endpoint such as `GET /api/hotrank/latest`.
- The backend reads the latest local snapshot.
- No CimiData request is made.
- If no snapshot exists, the page shows an empty state and a primary button.

### Manual Refresh

When the operator clicks `生成当前趋势` or `刷新热榜`:

- The frontend calls `POST /api/hotrank/runs`.
- The backend obtains or refreshes a CimiData token server-side.
- The backend requests the configured channels one by one.
- The backend waits at least 1.05 seconds between channel requests to respect the 1 QPS limit.
- The backend writes a raw snapshot and a processed trend snapshot.
- The frontend receives or polls the run result and renders the latest Top 10.

### Display

The page shows:

- Last generated time.
- Channel coverage, for example `6/6 platforms`.
- Raw row count, for example `300 hotrank rows`.
- Topic count after clustering.
- Top 10 current trend topics.
- A horizontal bar chart of Top 10 `trend_score`.
- A platform evidence matrix for Top 10.
- A category distribution chart.
- A detail panel per topic with evidence rows, original titles, hot tags, rank, hot value, created time, and links.

## Trend Topic Model

Each processed topic is not a single hotrank row. It is a cluster:

```json
{
  "topic_id": "sha1-normalized-topic",
  "label": "普京访华 / 中俄联合声明",
  "category": "时政国际",
  "trend_score": 87.4,
  "score_breakdown": {
    "platform_rank_score": 91.2,
    "normalized_hot_score": 84.0,
    "cross_platform_score": 95.0,
    "freshness_score": 76.0
  },
  "platform_count": 4,
  "evidence_count": 8,
  "first_seen_at": "2026-05-21T08:15:25",
  "latest_seen_at": "2026-05-21T10:10:16",
  "evidence": [
    {
      "channel_id": 3,
      "channel_name": "百度",
      "rank": 1,
      "title": "中俄迈向更高质量的全面战略协作",
      "hot": "7904600",
      "hot_numeric": 7904600.0,
      "hot_tag": "",
      "created_at": "2026-05-21T10:10:16",
      "url": "https://www.baidu.com/s?wd=..."
    }
  ]
}
```

## Topic Clustering

The first version should use deterministic clustering:

1. Normalize titles:
   - convert full-width punctuation to common separators where useful
   - lowercase ASCII
   - strip spaces and obvious hotrank suffix words
   - remove punctuation
2. Extract topic tokens:
   - preserve ASCII words and numbers
   - extract Chinese 2-gram and 3-gram tokens
   - drop generic stop tokens such as `回应`, `现场`, `官方`, `为何`, `怎么`, `最新`, `热搜`
3. Compare a new row against existing topics:
   - exact normalized title match joins
   - substring match joins when the shorter normalized title has at least 6 CJK chars
   - token Jaccard similarity joins when similarity is at least `0.34`
   - require at least one shared non-generic token of length 2 or more
4. Pick topic label:
   - choose the evidence title with the best platform rank
   - if multiple platforms exist, append a short secondary phrase only when it adds a distinct anchor token

This is conservative. It avoids dangerous false merges. Broad event families may remain as two nearby topics in the first version; that is acceptable because it preserves evidence integrity.

## Trend Scoring

Do not score by simple `+1` per title occurrence. That loses platform rank, freshness, and per-platform heat. Use a transparent weighted score:

```text
trend_score =
  platform_rank_score * 0.40
+ normalized_hot_score * 0.25
+ cross_platform_score * 0.25
+ freshness_score * 0.10
```

### platform_rank_score

For each evidence row:

```text
rank_score = 100 * (channel_item_count - rank + 1) / channel_item_count
```

Topic value:

```text
platform_rank_score = max(rank_score across evidence)
```

Reason: platform rank is more comparable than raw `hot` across different platforms.

### normalized_hot_score

For each channel, normalize `hot_numeric` against the channel's own min/max:

```text
hot_score = 100 * (hot_numeric - channel_min_hot) / (channel_max_hot - channel_min_hot)
```

If all hot values are equal or unavailable:

```text
hot_score = rank_score
```

Topic value:

```text
normalized_hot_score = average(top 3 evidence hot_score values)
```

Reason: Weibo, Zhihu, Baidu, Douyin, Toutiao, and Bilibili use incompatible heat units.

### cross_platform_score

```text
cross_platform_score = min(100, 35 + platform_count * 15 + min(evidence_count, 5) * 3)
```

Examples:

- 1 platform / 1 evidence -> 53
- 2 platforms / 3 evidence -> 74
- 4 platforms / 5 evidence -> 100

Reason: a topic on multiple platforms is more likely to be a true all-network trend.

### freshness_score

Use the latest evidence time:

| Age | Score |
| --- | ---: |
| <= 1 hour | 100 |
| <= 3 hours | 85 |
| <= 6 hours | 70 |
| <= 12 hours | 55 |
| <= 24 hours | 35 |
| older | 15 |

Reason: hot lists often contain stale but still high-ranking items.

## Taxonomy

Use a 10-category general web trend taxonomy:

| Key | Label | Purpose |
| --- | --- | --- |
| politics_world | 时政国际 | 国家政策、外交、国际冲突、公共治理 |
| society | 社会民生 | 民生事件、公共安全、消费维权、突发社会事件 |
| finance_business | 财经商业 | 股市、公司、消费、商业模式、产业变化 |
| tech_digital | 科技数码 | AI、手机、互联网产品、机器人、芯片、软件 |
| entertainment | 文娱影视 | 明星、影视、综艺、音乐、游戏泛娱乐 |
| sports | 体育赛事 | 比赛、运动员、体育组织 |
| education | 教育升学 | 学校、考试、招生、教育政策、学习 |
| health_life | 健康生活 | 医疗、食品、睡眠、心理、生活方式 |
| auto_travel | 汽车出行 | 车企、交通、旅行、城市出行 |
| platform_opinion | 平台争议/舆情 | 平台规则、网红争议、舆论反转、热搜争议 |

Classification first version:

- Deterministic keyword rules.
- Use title + summary + top evidence titles.
- If multiple categories match, use priority:
  `politics_world > health_life > education > finance_business > tech_digital > auto_travel > sports > entertainment > platform_opinion > society`.
- Unknown or weak matches default to `society`.

## Backend Design

Create focused backend modules:

- `web/backend/hotrank_models.py`: Pydantic response/request models.
- `web/backend/hotrank_client.py`: CimiData token and hotrank HTTP calls.
- `web/backend/hotrank_aggregator.py`: normalization, clustering, scoring, classification.
- `web/backend/hotrank_store.py`: local snapshot persistence and latest lookup.
- `web/backend/hotrank_routes.py`: FastAPI routes for latest snapshot and manual run.

Routes:

```text
GET  /api/hotrank/latest
POST /api/hotrank/runs
```

The `POST` request should accept optional channel ids, but default to `[1, 2, 3, 4, 5, 7]`.

## Storage Design

Store snapshots under:

```text
web_jobs/hotrank/
  latest.json
  runs/
    YYYYMMDD_HHMMSS/
      raw.json
      trends.json
```

`latest.json` points to or duplicates the latest processed snapshot. For simplicity and robustness, duplicate the processed snapshot in `latest.json`.

The raw snapshot must not include `access_token`.

## Frontend Design

Create:

- `web/frontend/src/pages/HotrankPage.tsx`
- `web/frontend/src/hotrankApi.ts`
- `web/frontend/src/hotrankTypes.ts`

Modify:

- `web/frontend/src/App.tsx` to add route/nav.
- `web/frontend/src/styles.css` for page layout and charts.

Charts should use simple HTML/CSS first:

- horizontal bars for Top 10 scores
- category pills and distribution bars
- platform evidence grid

No new chart library is needed in the first version.

## Error Handling

- Missing CimiData credentials returns a 400-style API error with message `CIMIDATA_APP_ID / CIMIDATA_APP_SECRET 未配置`.
- Token refresh failure returns a backend error and does not modify `latest.json`.
- Per-channel failure records the channel error and continues with remaining channels.
- If all channels fail, the run fails and the previous latest snapshot remains unchanged.
- If only some channels succeed, the page displays partial coverage and warnings.
- Hot value parsing failures fall back to rank score.
- Invalid timestamps get a low freshness score and a warning in backend logs.

## Testing

Backend tests:

- hot value parser handles `7904600`, `2208 万热度`, `1.2亿`, blank values.
- clusterer merges exact/near titles and avoids obvious unrelated titles.
- score formula ranks multi-platform high-rank topics above single-platform low-rank topics.
- category classifier maps representative titles to the 10 categories.
- store writes `raw.json`, `trends.json`, and `latest.json`.
- routes do not call CimiData on `GET /api/hotrank/latest`.
- route `POST /api/hotrank/runs` uses mocked CimiData responses and returns Top 10.

Frontend tests or manual verification:

- Opening `/hotrank` with no snapshot shows empty state and does not call run endpoint.
- Clicking refresh starts a run and renders Top 10.
- Partial channel errors are visible.
- Top 10 chart fits desktop and mobile widths.

## Acceptance Criteria

- `/hotrank` exists as a dedicated subpage.
- Page load never calls CimiData.
- Clicking the refresh button fetches hotrank data for the configured channels.
- The backend respects one-at-a-time channel requests with at least 1.05 seconds between calls.
- The page shows platform coverage, raw row count, topic count, Top 10 trend chart, category distribution, and evidence details.
- Secrets never leave the backend.
- Snapshot files are written locally and can be inspected.
- Existing normal collection jobs still work.

## Open Decisions Resolved

- Product surface: dedicated Web subpage.
- API trigger: manual click only.
- First chart: current snapshot trend chart, not a historical time-series chart.
- First scoring model: deterministic weighted score.
- First classification model: deterministic keyword taxonomy.
