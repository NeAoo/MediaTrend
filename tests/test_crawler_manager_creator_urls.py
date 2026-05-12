from datetime import datetime

from crawlers.manager import CrawlerManager
from models.hotspot import CollectionResult, EducationHotspot


class FakeCreatorCrawler:
    def __init__(self):
        self.calls = []

    def collect(
        self,
        keywords,
        time_range_hours=(0, 24),
        creator_urls=None,
        creator_time_range_hours=None,
    ):
        self.calls.append(
            {
                "keywords": keywords,
                "time_range_hours": time_range_hours,
                "creator_urls": creator_urls,
                "creator_time_range_hours": creator_time_range_hours,
            }
        )
        return CollectionResult(
            success_count=1,
            items=[
                EducationHotspot(
                    title="账号内容",
                    source="xiaohongshu",
                    publish_time=datetime.now(),
                    content="",
                    url="https://example.com/item",
                )
            ],
        )


def test_manager_passes_creator_urls_to_creator_sources():
    crawler = FakeCreatorCrawler()
    manager = object.__new__(CrawlerManager)
    manager.enabled_sources = ["xiaohongshu"]
    manager.crawlers = {"xiaohongshu": crawler}

    items = manager.collect_all(
        source_keywords={"xiaohongshu": []},
        source_creator_urls={"xiaohongshu": ["https://example.com/creator"]},
        source_keyword_time_ranges={"xiaohongshu": (0, 12)},
        source_account_time_ranges={"xiaohongshu": (0, 96)},
    )

    assert len(items) == 1
    assert crawler.calls == [
        {
            "keywords": [],
            "time_range_hours": (0, 12),
            "creator_urls": ["https://example.com/creator"],
            "creator_time_range_hours": (0, 96),
        }
    ]
