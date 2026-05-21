from datetime import datetime
from pathlib import Path

from models.hotspot import EducationHotspot
from config.app_config import AppConfig
from web.backend.job_runner import (
    CrawlUnit,
    JobArtifacts,
    UnitCollectionResult,
    _collect_source_units,
    _source_units,
    run_merge_score_report,
)


def test_run_merge_score_report_skips_scoring_when_disabled(tmp_path: Path):
    item = EducationHotspot(
        title="测试",
        source="aihot",
        publish_time=datetime.now(),
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


def test_collect_source_units_continues_after_unit_failure(monkeypatch):
    units = [
        CrawlUnit(
            unit_type="keyword",
            unit_name="慢关键词",
            keywords=["慢关键词"],
            creator_urls=[],
            keyword_time_range=(0, 24),
            account_time_range=None,
            max_count=3,
            expected_min=1,
            runtime_timeout_seconds=30,
        ),
        CrawlUnit(
            unit_type="keyword",
            unit_name="正常关键词",
            keywords=["正常关键词"],
            creator_urls=[],
            keyword_time_range=(0, 24),
            account_time_range=None,
            max_count=3,
            expected_min=1,
            runtime_timeout_seconds=30,
        ),
    ]
    item = EducationHotspot(
        title="正常结果",
        source="xiaohongshu",
        publish_time=datetime.now(),
        content="正文",
        url="https://example.com/item",
    )
    events = []

    monkeypatch.setattr("web.backend.job_runner._source_units", lambda config, source: units)

    def fake_collect_one_unit(source_name: str, unit: CrawlUnit) -> UnitCollectionResult:
        if unit.unit_name == "慢关键词":
            raise TimeoutError("单元超时")
        return UnitCollectionResult(items=[item], errors=[])

    monkeypatch.setattr("web.backend.job_runner.collect_one_unit", fake_collect_one_unit)

    items, warnings = _collect_source_units(
        "xiaohongshu",
        config=object(),
        emit_event=lambda **event: events.append(event),
        should_cancel=lambda: False,
    )

    assert items == [item]
    assert any("慢关键词" in warning for warning in warnings)
    assert [event["type"] for event in events] == [
        "unit_started",
        "unit_failed",
        "unit_started",
        "unit_completed",
    ]


def test_zhihu_source_units_batch_auth_sensitive_keywords_and_accounts():
    config = AppConfig.model_validate(
        {
            "enabled_sources": ["zhihu"],
            "zhihu": {
                "keyword_search": {
                    "enabled": True,
                    "keywords": ["教育改革", "中考"],
                    "max_results_per_keyword": 3,
                    "expected_min_results": 1,
                    "time_range_hours": {"min": 0, "max": 72},
                },
                "account_crawl": {
                    "enabled": True,
                    "creator_urls": [
                        "https://www.zhihu.com/people/a",
                        "https://www.zhihu.com/people/b",
                    ],
                    "max_results_per_account": 5,
                    "expected_min_results": 1,
                    "time_range_hours": {"min": 0, "max": 168},
                },
            },
            "web": {"unit_timeout_seconds": 180},
        }
    )

    units = _source_units(config, "zhihu")

    assert len(units) == 2
    assert units[0].unit_name == "关键词批量：教育改革、中考"
    assert units[0].keywords == ["教育改革", "中考"]
    assert units[0].max_count == 6
    assert units[0].expected_min == 2
    assert units[1].unit_name == "账号批量：2 个账号"
    assert units[1].creator_urls == [
        "https://www.zhihu.com/people/a",
        "https://www.zhihu.com/people/b",
    ]
    assert units[1].max_count == 10
    assert units[1].expected_min == 2
