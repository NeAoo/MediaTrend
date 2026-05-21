from datetime import datetime, timezone

from web.backend.hotrank_aggregator import (
    CATEGORY_RULES,
    STANDARD_CATEGORIES,
    aggregate_hotrank_results,
    parse_hot_value,
)
from web.backend.hotrank_models import HotrankChannelItem, HotrankFetchResult


def _result(channel_id: int, channel_name: str, titles: list[str]) -> HotrankFetchResult:
    return HotrankFetchResult(
        channel_id=channel_id,
        channel_name=channel_name,
        ok=True,
        items=[
            HotrankChannelItem(
                channel_id=channel_id,
                channel_name=channel_name,
                rank=index,
                title=title,
                hot=str(1_000_000 - index * 10_000),
                created_at="2026-05-21T10:00:00+00:00",
            )
            for index, title in enumerate(titles, start=1)
        ],
    )


def test_parse_hot_value_handles_common_units():
    assert parse_hot_value(" 7904689 ") == 7_904_689
    assert parse_hot_value("2208 万热度") == 22_080_000
    assert parse_hot_value("1.2亿") == 120_000_000
    assert parse_hot_value("") is None


def test_aggregate_clusters_cross_platform_topics():
    snapshot = aggregate_hotrank_results(
        [
            _result(1, "微博", ["普京结束访华", "某明星新剧开机"]),
            _result(3, "百度", ["普京结束对中国的国事访问", "四大一线城市房价全涨"]),
        ],
        run_id="test-run",
        requested_channel_ids=[1, 3],
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
    )

    assert snapshot.raw_item_count == 4
    top_topic = snapshot.top_trends[0]
    assert top_topic.platform_count == 2
    assert top_topic.evidence_count == 2
    assert top_topic.trend_score > 70
    assert {item.channel_name for item in top_topic.evidence} == {"微博", "百度"}


def test_aggregate_assigns_basic_category():
    snapshot = aggregate_hotrank_results(
        [_result(3, "百度", ["四大一线城市房价全涨"])],
        run_id="category-run",
        requested_channel_ids=[3],
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
    )

    assert snapshot.top_trends[0].category == "房产"


def test_category_rules_use_standard_chinese_categories():
    rule_categories = {category for category, _ in CATEGORY_RULES}

    assert rule_categories <= set(STANDARD_CATEGORIES)
    assert "其它" in STANDARD_CATEGORIES
    assert all(category == "AI" or not category.isascii() for category in rule_categories)


def test_aggregate_assigns_more_specific_hotrank_categories():
    cases = [
        ("雷霆力克马刺大比分扳平", "体育健身"),
        ("一组数据看懂我国硬核算力网", "AI"),
        ("何为“小满”", "文化"),
        ("特斯拉监督版FSD入华", "汽车"),
        ("普京上飞机前依依不舍久久交谈", "军事国际"),
        ("中国拿下90%超大型油轮新订单", "财经"),
    ]
    for title, expected_category in cases:
        snapshot = aggregate_hotrank_results(
            [_result(3, "百度", [title])],
            run_id=f"category-{expected_category}",
            requested_channel_ids=[3],
            now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
        )

        assert snapshot.top_trends[0].category == expected_category


def test_aggregate_can_apply_ai_category_classifier_before_theme_summary():
    def fake_classifier(topics):
        return {
            topic.id: "军事国际"
            for topic in topics
            if "歼10" in topic.title or "歼10" in "".join(item.title for item in topic.evidence)
        }

    snapshot = aggregate_hotrank_results(
        [_result(3, "百度", ["歼10CE凭什么吊打欧洲双雄"])],
        run_id="ai-category-run",
        requested_channel_ids=[3],
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
        category_classifier=fake_classifier,
    )

    assert snapshot.top_trends[0].category == "军事国际"
    assert snapshot.theme_summaries[0].category == "军事国际"
    assert "AI 主题分类已应用：1/1 个趋势" in snapshot.warnings


def test_unknown_topics_fall_back_to_other_and_hide_from_theme_summary():
    snapshot = aggregate_hotrank_results(
        [
            _result(
                3,
                "百度",
                [
                    "完全无法稳定判断分类的随机短句",
                    "四大一线城市房价全涨",
                ],
            )
        ],
        run_id="other-category-run",
        requested_channel_ids=[3],
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
    )

    categories = {topic.title: topic.category for topic in snapshot.top_trends}
    assert categories["完全无法稳定判断分类的随机短句"] == "其它"
    assert "其它" not in {summary.category for summary in snapshot.theme_summaries}


def test_ai_category_alias_other_is_normalized_and_hidden_from_theme_summary():
    def fake_classifier(topics):
        return {
            topic.id: "其他"
            for topic in topics
            if "随机短句" in topic.title
        }

    snapshot = aggregate_hotrank_results(
        [
            _result(
                3,
                "百度",
                [
                    "完全无法稳定判断分类的随机短句",
                    "特斯拉监督版FSD入华",
                ],
            )
        ],
        run_id="other-alias-run",
        requested_channel_ids=[3],
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
        category_classifier=fake_classifier,
    )

    categories = {topic.title: topic.category for topic in snapshot.top_trends}
    assert categories["完全无法稳定判断分类的随机短句"] == "其它"
    assert "其它" not in {summary.category for summary in snapshot.theme_summaries}


def test_theme_summaries_use_full_topic_pool_not_only_top_trends():
    snapshot = aggregate_hotrank_results(
        [
            _result(
                3,
                "百度",
                [
                    "普京上飞机前依依不舍久久交谈",
                    "雷霆力克马刺大比分扳平",
                    "四大一线城市房价全涨",
                    "高考志愿填报指南发布",
                    "特斯拉监督版FSD入华",
                    "苹果手机突然降价",
                ],
            )
        ],
        run_id="theme-run",
        requested_channel_ids=[3],
        limit=3,
        now=datetime(2026, 5, 21, 10, 30, tzinfo=timezone.utc),
    )

    assert len(snapshot.top_trends) == 3
    assert len(snapshot.theme_summaries) == 5
    assert {summary.category for summary in snapshot.theme_summaries} >= {
        "军事国际",
        "体育健身",
        "房产",
        "教育",
        "汽车",
    }
    assert all(len(summary.top_searches) <= 3 for summary in snapshot.theme_summaries)
