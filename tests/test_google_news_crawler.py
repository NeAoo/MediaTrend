from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

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


def test_collect_uses_rss_items(monkeypatch):
    crawler = GoogleNewsCrawler()
    calls = []
    published_at = format_datetime(
        datetime.now(timezone.utc) - timedelta(hours=1),
        usegmt=True,
    )

    def fake_get_news_items(keyword):
        calls.append(keyword)
        return [
            {
                "title": f"{keyword} 标题",
                "description": "摘要",
                "published date": published_at,
                "url": "https://news.google.com/read/example",
                "publisher": {"title": "媒体"},
            }
        ]

    monkeypatch.setattr(crawler, "_get_news_items", fake_get_news_items)
    result = crawler.collect(["教育改革"], time_range_hours=(0, 48))

    assert calls == ["教育改革"]
    assert result.success_count == 1
    assert result.items[0].url == "https://news.google.com/read/example"
    assert isinstance(result.items[0].publish_time, datetime)


def test_build_search_url_contains_period_and_locale():
    crawler = GoogleNewsCrawler()

    url = crawler._build_search_url("教育改革")

    assert "q=%E6%95%99%E8%82%B2%E6%94%B9%E9%9D%A9+when%3A7d" in url
    assert "hl=zh-CN" in url
    assert "gl=CN" in url
    assert "ceid=CN:zh-CN" in url
