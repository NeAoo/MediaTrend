from datetime import datetime, timedelta, timezone

from crawlers.aihot import AihotCrawler


def test_parse_item_maps_aihot_fields():
    crawler = AihotCrawler()
    raw = {
        "id": "cmp2o6m6d00asslta6s0jtj3t",
        "title": "材料科学AI多任务模型突破",
        "title_en": "MatterSim expands AI for materials science",
        "url": "https://example.com/source",
        "source": "AI HOT Source",
        "publishedAt": "2026-05-12T13:24:36.000Z",
        "summary": "这是一段 AI HOT 摘要。",
        "category": "ai-models",
    }

    item = crawler.parse_item(raw)

    assert item.title == "材料科学AI多任务模型突破"
    assert item.source == "aihot"
    assert item.author == "AI HOT Source"
    assert item.url == "https://example.com/source"
    assert item.content == "这是一段 AI HOT 摘要。"
    expected_publish_time = (
        datetime(2026, 5, 12, 13, 24, 36, tzinfo=timezone.utc)
        .astimezone()
        .replace(tzinfo=None)
    )
    assert item.publish_time == expected_publish_time
    assert item.tags == ["AI HOT", "AI 行业", "ai-models", "模型发布/更新"]


def test_build_queries_defaults_to_selected_pool():
    crawler = AihotCrawler()

    assert crawler._build_queries([], []) == [{"keyword": None, "category": None}]


def test_build_queries_combines_keywords_and_categories():
    crawler = AihotCrawler()

    queries = crawler._build_queries(["OpenAI", "Agent"], ["ai-models", "tip"])

    assert queries == [
        {"keyword": "OpenAI", "category": "ai-models"},
        {"keyword": "OpenAI", "category": "tip"},
        {"keyword": "Agent", "category": "ai-models"},
        {"keyword": "Agent", "category": "tip"},
    ]


def test_collect_fetches_default_pool_when_keywords_empty(monkeypatch):
    crawler = AihotCrawler()
    calls = []
    published_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat().replace("+00:00", "Z")

    def fake_fetch_items(keyword, category, since):
        calls.append((keyword, category, since))
        return [
            {
                "id": "cmp-default",
                "title": "默认精选",
                "url": "https://example.com/default",
                "source": "AI HOT",
                "publishedAt": published_at,
                "summary": "摘要",
                "category": "tip",
            }
        ]

    monkeypatch.setattr(crawler, "_fetch_items", fake_fetch_items)

    result = crawler.collect([], time_range_hours=(0, 24))

    assert result.success_count == 1
    assert result.items[0].title == "默认精选"
    assert calls[0][0] is None
    assert calls[0][1] is None
    assert calls[0][2].endswith("Z")
