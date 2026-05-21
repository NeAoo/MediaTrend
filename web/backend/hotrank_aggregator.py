from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Callable

from web.backend.hotrank_models import (
    HotrankChannelItem,
    HotrankFetchResult,
    HotrankSnapshot,
    HotrankThemeSearch,
    HotrankThemeSummary,
    HotrankTrendEvidence,
    HotrankTrendTopic,
)


CHANNEL_NAMES: dict[int, str] = {
    1: "微博",
    2: "知乎",
    3: "百度",
    4: "抖音",
    5: "头条",
    7: "B站",
}
DEFAULT_CHANNEL_IDS = [1, 2, 3, 4, 5, 7]
DEFAULT_TREND_LIMIT = 10
THEME_SUMMARY_LIMIT = 5
THEME_TOP_SEARCH_LIMIT = 3
MAX_EVIDENCE_PER_TOPIC = 8
TOKEN_JOIN_THRESHOLD = 0.32
LONG_COMMON_SUBSTRING_THRESHOLD = 4

_HOT_VALUE_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*([亿万wWkK]?)")
_ASCII_WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_PUNCTUATION_PATTERN = re.compile(r"[#【】\[\]（）()《》<>“”\"'‘’、，。！？!?:：；;|｜/\\\\\-_·•…\s]+")
_EDGE_PUNCTUATION_PATTERN = re.compile(r"^[\s#【】\[\]（）()《》<>“”\"'‘’、，。！？!?:：；;|｜/\\\\\-_·•…]+|[\s#【】\[\]（）()《》<>“”\"'‘’、，。！？!?:：；;|｜/\\\\\-_·•…]+$")


STANDARD_CATEGORIES: tuple[str, ...] = (
    "育儿",
    "科技",
    "体育健身",
    "财经",
    "美食",
    "医疗",
    "娱乐",
    "情感",
    "历史",
    "军事国际",
    "美妆时尚",
    "文化",
    "汽车",
    "游戏",
    "旅游",
    "房产",
    "健康养生",
    "职场",
    "摄影",
    "资讯热点",
    "教育",
    "开发者",
    "影视",
    "美妆",
    "生活",
    "数码",
    "媒体",
    "宠物",
    "三农",
    "星座命理",
    "搞笑",
    "动漫",
    "家居",
    "科学",
    "商业营销",
    "个人成长",
    "壁纸头像",
    "法律",
    "民生",
    "文案",
    "体制",
    "文摘",
    "AI",
    "其它",
)

CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AI", ("人工智能", "openai", "chatgpt", "大模型", "生成式", "aigc", "算力", "智能体", "机器人", "ai芯片", "deepseek", "通义", "豆包", "文心")),
    ("开发者", ("编程", "程序员", "代码", "开源", "github", "python", "java", "javascript", "前端", "后端", "数据库", "服务器", "漏洞", "接口", "框架")),
    ("数码", ("手机", "电脑", "平板", "耳机", "相机", "苹果", "iphone", "ipad", "华为", "小米", "oppo", "vivo", "荣耀", "显卡", "芯片")),
    ("科技", ("科技", "航天", "卫星", "量子", "芯片", "半导体", "新能源", "无人机", "硬核", "算力网", "专利", "实验室", "科研")),
    ("体育健身", ("nba", "cba", "英超", "西甲", "中超", "足球", "篮球", "网球", "乒乓", "羽毛球", "马刺", "雷霆", "湖人", "勇士", "凯尔特人", "冠军", "夺冠", "比分", "健身", "跑步", "马拉松", "奥运", "世界杯", "全运会")),
    ("汽车", ("汽车", "车企", "新车", "电动车", "智驾", "自动驾驶", "fsd", "特斯拉", "比亚迪", "小鹏", "理想", "蔚来", "问界", "小米汽车", "高速", "驾照")),
    ("房产", ("房价", "楼市", "房贷", "买房", "卖房", "二手房", "新房", "地产", "住宅", "公积金", "物业")),
    ("财经", ("a股", "美股", "港股", "股票", "基金", "黄金", "银行", "央行", "利率", "汇率", "财报", "上市", "关税", "贸易", "经济", "消费", "订单", "市场", "投资", "债券")),
    ("军事国际", ("中俄", "俄乌", "美国", "俄罗斯", "普京", "特朗普", "拜登", "韩国", "日本", "印度", "以色列", "伊朗", "联合国", "外交", "总统", "首相", "战争", "停火", "战机", "导弹", "航母", "军演", "边境", "国际")),
    ("法律", ("法院", "判决", "起诉", "律师", "违法", "犯罪", "刑拘", "拘留", "立案", "审判", "检察", "赔偿", "侵权", "法规")),
    ("医疗", ("医院", "医生", "患者", "手术", "急诊", "门诊", "医保", "药品", "疫苗", "感染", "癌症", "病情", "诊断", "治疗")),
    ("健康养生", ("健康", "养生", "睡眠", "减肥", "饮食", "脂肪肝", "血糖", "血压", "运动", "熬夜", "体检", "心理", "焦虑")),
    ("教育", ("高考", "中考", "考研", "学校", "学生", "老师", "教育", "招生", "录取", "试卷", "大学", "校园", "补课", "学费")),
    ("育儿", ("育儿", "孩子", "宝宝", "婴儿", "幼儿", "宝妈", "奶粉", "早教", "亲子", "儿童", "家长")),
    ("影视", ("电影", "电视剧", "短剧", "票房", "导演", "演员", "院线", "上映", "剧集", "纪录片", "奥斯卡")),
    ("动漫", ("动漫", "动画", "漫画", "番剧", "二次元", "cos", "声优")),
    ("游戏", ("游戏", "电竞", "王者荣耀", "原神", "和平精英", "英雄联盟", "lol", "steam", "手游", "主机")),
    ("娱乐", ("明星", "艺人", "综艺", "演唱会", "歌手", "偶像", "直播", "开机", "红毯", "恋情", "塌房", "道歉", "回应")),
    ("美妆", ("美妆", "护肤", "口红", "粉底", "眼影", "化妆", "面膜", "防晒")),
    ("美妆时尚", ("时尚", "穿搭", "妆容", "高定", "秀场", "奢侈品", "香水", "包包", "珠宝")),
    ("美食", ("美食", "餐厅", "外卖", "奶茶", "咖啡", "火锅", "烧烤", "预制菜", "食品", "食物", "做饭", "菜谱")),
    ("旅游", ("旅游", "景区", "游客", "酒店", "高铁", "地铁", "航班", "机场", "出境", "签证", "旅行", "露营")),
    ("三农", ("三农", "农村", "农民", "农业", "粮食", "种植", "养殖", "玉米", "小麦", "水稻", "乡村")),
    ("宠物", ("宠物", "猫", "狗", "萌宠", "猫咪", "狗狗", "铲屎官", "流浪狗", "流浪猫")),
    ("家居", ("家居", "装修", "家具", "家电", "收纳", "房间", "卧室", "客厅")),
    ("职场", ("职场", "工资", "薪资", "裁员", "招聘", "面试", "老板", "员工", "公司上班", "加班", "离职")),
    ("商业营销", ("营销", "品牌", "广告", "带货", "电商", "直播间", "销量", "商家", "促销", "618", "双11")),
    ("个人成长", ("个人成长", "自律", "学习方法", "认知", "成长", "读书", "效率", "复盘", "目标")),
    ("情感", ("情感", "恋爱", "分手", "结婚", "离婚", "婚姻", "情侣", "夫妻", "相亲", "婆媳")),
    ("历史", ("历史", "考古", "文物", "古代", "博物馆", "遗址", "朝代", "汉朝", "唐朝", "宋朝")),
    ("文化", ("文化", "节气", "小满", "非遗", "诗词", "文学", "传统", "民俗", "艺术", "读书", "书法")),
    ("科学", ("科学", "科普", "物理", "化学", "生物", "天文", "地理", "研究发现", "实验", "论文")),
    ("摄影", ("摄影", "拍照", "镜头", "写真", "修图", "相机", "照片")),
    ("媒体", ("媒体", "记者", "报社", "电视台", "新闻发布会", "主持人", "采访")),
    ("搞笑", ("搞笑", "段子", "梗", "离谱", "表情包", "笑死", "名场面")),
    ("星座命理", ("星座", "命理", "运势", "塔罗", "占卜", "风水")),
    ("壁纸头像", ("壁纸", "头像", "表情包", "背景图", "手机壁纸")),
    ("文案", ("文案", "金句", "句子", "朋友圈", "小作文", "标题")),
    ("文摘", ("文摘", "散文", "摘抄", "语录", "书摘")),
    ("体制", ("体制", "公务员", "事业编", "编制", "国企", "考公", "考编")),
    ("生活", ("生活", "日常", "家庭", "邻居", "租房", "家务", "通勤", "续费", "扣款")),
    ("民生", ("民生", "事故", "警方", "女子", "男子", "消防", "村民", "老人", "死亡", "去世", "通报", "失窃", "赔偿", "家委会", "安全")),
    ("资讯热点", ("热点", "热搜", "突发", "最新", "官方", "发布", "消息", "现场", "事件")),
)
DEFAULT_CATEGORY = "其它"
HIDDEN_THEME_CATEGORIES = {"其它", "其他"}
CATEGORY_ALIASES = {
    "其他": "其它",
}
CategoryClassifier = Callable[[list[HotrankTrendTopic]], dict[str, str]]


@dataclass(frozen=True)
class _ScoredEvidence:
    item: HotrankChannelItem
    rank_score: float
    hot_score: float
    single_score: float


@dataclass
class _TopicCluster:
    normalized_title: str
    evidence: list[_ScoredEvidence]


def normalize_title(title: str) -> str:
    cleaned = _EDGE_PUNCTUATION_PATTERN.sub("", title.strip())
    cleaned = _PUNCTUATION_PATTERN.sub("", cleaned)
    return cleaned.lower()


def parse_hot_value(raw_hot: str | int | float | None) -> float | None:
    if raw_hot is None:
        return None
    text = str(raw_hot).replace(",", "").strip()
    if not text:
        return None
    match = _HOT_VALUE_PATTERN.search(text)
    if match is None:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit in {"万", "w"}:
        value *= 10_000
    elif unit == "亿":
        value *= 100_000_000
    elif unit == "k":
        value *= 1_000
    if not math.isfinite(value):
        return None
    return value


def aggregate_hotrank_results(
    fetch_results: list[HotrankFetchResult],
    run_id: str,
    requested_channel_ids: list[int],
    limit: int = DEFAULT_TREND_LIMIT,
    now: datetime | None = None,
    category_classifier: CategoryClassifier | None = None,
) -> HotrankSnapshot:
    assert run_id.strip(), "run_id must not be empty"
    now = now or datetime.now(timezone.utc)
    trend_limit = max(1, min(limit, 50))
    scored_items = _score_items(fetch_results)
    clusters = _cluster_items(scored_items)
    topics = [_topic_from_cluster(index, cluster, now) for index, cluster in enumerate(clusters, start=1)]
    topics.sort(key=lambda topic: (-topic.trend_score, -topic.platform_count, -topic.evidence_count, topic.title))
    warnings = []
    if category_classifier is not None and topics:
        try:
            category_overrides = category_classifier(topics)
        except Exception as exc:
            category_overrides = {}
            warnings.append(f"AI 主题分类失败，已使用关键词分类：{exc}")
        applied_count, invalid_count = _apply_category_overrides(topics, category_overrides)
        if applied_count:
            warnings.append(f"AI 主题分类已应用：{applied_count}/{len(topics)} 个趋势")
            if applied_count < len(topics):
                warnings.append(f"AI 主题分类有 {len(topics) - applied_count} 个趋势未返回有效分类，已保留关键词分类")
        elif category_overrides:
            warnings.append("AI 主题分类返回结果全部非法，已使用关键词分类")
        else:
            warnings.append("AI 主题分类未返回有效分类，已使用关键词分类")
        if invalid_count:
            warnings.append(f"AI 主题分类返回了 {invalid_count} 个非法分类，已保留关键词分类")
    top_trends = topics[:trend_limit]
    theme_summaries = _theme_summaries(topics)
    category_counts = dict(Counter(topic.category for topic in topics))
    channels_succeeded = [result.channel_id for result in fetch_results if result.ok]
    channels_failed = [result.channel_id for result in fetch_results if not result.ok]
    errors = [
        f"{result.channel_name}: {result.error}"
        for result in fetch_results
        if not result.ok and result.error
    ]
    if not top_trends:
        warnings.append("没有可聚合的热榜条目")

    return HotrankSnapshot(
        run_id=run_id,
        created_at=now.isoformat(timespec="seconds"),
        channels_requested=requested_channel_ids,
        channels_succeeded=channels_succeeded,
        channels_failed=channels_failed,
        raw_item_count=sum(len(result.items) for result in fetch_results),
        top_trends=top_trends,
        theme_summaries=theme_summaries,
        category_counts=category_counts,
        warnings=warnings,
        errors=errors,
    )


def _theme_summaries(topics: list[HotrankTrendTopic]) -> list[HotrankThemeSummary]:
    grouped: dict[str, list[HotrankTrendTopic]] = {}
    for topic in topics:
        category = _normalize_category(topic.category or DEFAULT_CATEGORY)
        if category in HIDDEN_THEME_CATEGORIES:
            continue
        grouped.setdefault(category, []).append(topic)

    summaries: list[HotrankThemeSummary] = []
    for category, category_topics in grouped.items():
        sorted_topics = sorted(
            category_topics,
            key=lambda topic: (-topic.trend_score, -topic.platform_count, -topic.evidence_count, topic.title),
        )
        total_score = round(sum(topic.trend_score for topic in sorted_topics), 2)
        summaries.append(
            HotrankThemeSummary(
                category=category,
                total_score=total_score,
                topic_count=len(sorted_topics),
                evidence_count=sum(topic.evidence_count for topic in sorted_topics),
                top_searches=[
                    HotrankThemeSearch(
                        id=topic.id,
                        title=topic.title,
                        trend_score=topic.trend_score,
                        platform_count=topic.platform_count,
                        evidence_count=topic.evidence_count,
                        total_hot_value=topic.total_hot_value,
                    )
                    for topic in sorted_topics[:THEME_TOP_SEARCH_LIMIT]
                ],
            )
        )
    summaries.sort(
        key=lambda summary: (
            -summary.total_score,
            -summary.topic_count,
            -summary.evidence_count,
            summary.category,
        )
    )
    return summaries[:THEME_SUMMARY_LIMIT]


def _apply_category_overrides(
    topics: list[HotrankTrendTopic],
    category_overrides: dict[str, str],
) -> tuple[int, int]:
    if not category_overrides:
        return (0, 0)

    valid_categories = set(STANDARD_CATEGORIES)
    applied_count = 0
    invalid_count = 0
    for topic in topics:
        category = _normalize_category(category_overrides.get(topic.id, ""))
        if not category:
            continue
        if category not in valid_categories:
            invalid_count += 1
            continue
        topic.category = category
        applied_count += 1
    return applied_count, invalid_count


def _normalize_category(category: str | None) -> str:
    normalized = str(category or "").strip()
    return CATEGORY_ALIASES.get(normalized, normalized)


def _score_items(fetch_results: list[HotrankFetchResult]) -> list[_ScoredEvidence]:
    channel_max_rank = {
        result.channel_id: max(len(result.items), 1)
        for result in fetch_results
    }
    channel_hot_ranges: dict[int, tuple[float, float] | None] = {}
    for result in fetch_results:
        values = [
            item.hot_value if item.hot_value is not None else parse_hot_value(item.hot)
            for item in result.items
        ]
        finite_values = [value for value in values if value is not None and math.isfinite(value)]
        channel_hot_ranges[result.channel_id] = (
            (min(finite_values), max(finite_values)) if finite_values else None
        )

    scored_items: list[_ScoredEvidence] = []
    for result in fetch_results:
        max_rank = channel_max_rank[result.channel_id]
        hot_range = channel_hot_ranges[result.channel_id]
        for item in result.items:
            title = normalize_title(item.title)
            if not title:
                continue
            rank_score = 100 * (max_rank - item.rank + 1) / max_rank
            hot_value = item.hot_value if item.hot_value is not None else parse_hot_value(item.hot)
            item.hot_value = hot_value
            hot_score = _normalized_hot_score(hot_value, hot_range, rank_score)
            single_score = (rank_score * 0.62) + (hot_score * 0.38)
            scored_items.append(
                _ScoredEvidence(
                    item=item,
                    rank_score=round(rank_score, 4),
                    hot_score=round(hot_score, 4),
                    single_score=round(single_score, 4),
                )
            )
    scored_items.sort(key=lambda scored: (scored.item.channel_id, scored.item.rank))
    return scored_items


def _normalized_hot_score(
    hot_value: float | None,
    hot_range: tuple[float, float] | None,
    rank_score: float,
) -> float:
    if hot_value is None or hot_range is None:
        return rank_score
    low, high = hot_range
    if high <= low:
        return rank_score
    return max(0.0, min(100.0, 100 * (hot_value - low) / (high - low)))


def _cluster_items(scored_items: list[_ScoredEvidence]) -> list[_TopicCluster]:
    clusters: list[_TopicCluster] = []
    for scored in scored_items:
        normalized = normalize_title(scored.item.title)
        match = _find_cluster(clusters, normalized)
        if match is None:
            clusters.append(_TopicCluster(normalized_title=normalized, evidence=[scored]))
        else:
            match.evidence.append(scored)
            match.normalized_title = _choose_cluster_normalized_title(match)
    return clusters


def _find_cluster(clusters: list[_TopicCluster], normalized_title: str) -> _TopicCluster | None:
    for cluster in clusters:
        if _should_join_topic(normalized_title, cluster.normalized_title):
            return cluster
        if any(_should_join_topic(normalized_title, normalize_title(item.item.title)) for item in cluster.evidence):
            return cluster
    return None


def _choose_cluster_normalized_title(cluster: _TopicCluster) -> str:
    best = max(
        cluster.evidence,
        key=lambda scored: (scored.single_score, -scored.item.rank, -len(scored.item.title)),
    )
    return normalize_title(best.item.title)


def _should_join_topic(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right or left in right or right in left:
        return True
    left_tokens = _title_tokens(left)
    right_tokens = _title_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    overlap = left_tokens & right_tokens
    union = left_tokens | right_tokens
    jaccard = len(overlap) / len(union)
    if jaccard >= TOKEN_JOIN_THRESHOLD:
        return True
    if _longest_common_substring_length(left, right) >= LONG_COMMON_SUBSTRING_THRESHOLD:
        return True
    return len(overlap) >= 3 and jaccard >= 0.24


def _title_tokens(normalized_title: str) -> set[str]:
    tokens = set(_ASCII_WORD_PATTERN.findall(normalized_title))
    chinese_chars = "".join(_CHINESE_CHAR_PATTERN.findall(normalized_title))
    for width in (2, 3):
        for index in range(0, max(0, len(chinese_chars) - width + 1)):
            tokens.add(chinese_chars[index:index + width])
    return tokens


def _longest_common_substring_length(left: str, right: str) -> int:
    if len(left) > len(right):
        left, right = right, left
    previous = [0] * (len(right) + 1)
    best = 0
    for left_index, left_char in enumerate(left, start=1):
        current = [0] * (len(right) + 1)
        for right_index, right_char in enumerate(right, start=1):
            if left_char == right_char:
                current[right_index] = previous[right_index - 1] + 1
                best = max(best, current[right_index])
        previous = current
    return best


def _topic_from_cluster(index: int, cluster: _TopicCluster, now: datetime) -> HotrankTrendTopic:
    sorted_evidence = sorted(
        cluster.evidence,
        key=lambda scored: (-scored.single_score, scored.item.rank, scored.item.channel_id),
    )
    representative = sorted_evidence[0].item
    channels = sorted({scored.item.channel_name for scored in cluster.evidence})
    platform_count = len({scored.item.channel_id for scored in cluster.evidence})
    evidence_count = len(cluster.evidence)
    rank_score = mean(scored.rank_score for scored in cluster.evidence)
    hot_score = mean(scored.hot_score for scored in cluster.evidence)
    cross_platform_score = min(100.0, 35 + platform_count * 15 + min(evidence_count, 5) * 3)
    freshness_score = max(_freshness_score(scored.item.created_at, now) for scored in cluster.evidence)
    trend_score = (
        rank_score * 0.40
        + hot_score * 0.25
        + cross_platform_score * 0.25
        + freshness_score * 0.10
    )
    latest_created_at = _latest_created_at(scored.item.created_at for scored in cluster.evidence)
    evidence_models = [
        HotrankTrendEvidence(
            channel_id=scored.item.channel_id,
            channel_name=scored.item.channel_name,
            rank=scored.item.rank,
            title=scored.item.title,
            url=scored.item.url,
            hot=scored.item.hot,
            hot_value=scored.item.hot_value,
            hot_tag=scored.item.hot_tag,
            summary=scored.item.summary,
            created_at=scored.item.created_at,
        )
        for scored in sorted_evidence[:MAX_EVIDENCE_PER_TOPIC]
    ]
    topic_id = hashlib.sha1(normalize_title(representative.title).encode("utf-8")).hexdigest()[:12]
    if not topic_id:
        topic_id = f"topic-{index}"

    return HotrankTrendTopic(
        id=topic_id,
        title=representative.title.strip(),
        category=_categorize_topic(cluster),
        trend_score=round(trend_score, 2),
        platform_count=platform_count,
        evidence_count=evidence_count,
        total_hot_value=round(
            sum(scored.item.hot_value or 0 for scored in cluster.evidence),
            2,
        ),
        latest_created_at=latest_created_at,
        channels=channels,
        score_parts={
            "rank": round(rank_score, 2),
            "hot": round(hot_score, 2),
            "cross_platform": round(cross_platform_score, 2),
            "freshness": round(freshness_score, 2),
        },
        evidence=evidence_models,
    )


def _categorize_topic(cluster: _TopicCluster) -> str:
    corpus = " ".join(
        f"{scored.item.title} {scored.item.summary}"
        for scored in cluster.evidence
    ).lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword.lower() in corpus for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def _freshness_score(created_at: str | None, now: datetime) -> float:
    parsed = _parse_datetime(created_at)
    if parsed is None:
        return 35.0
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    age_seconds = (now - parsed).total_seconds()
    if age_seconds <= 60 * 60:
        return 100.0
    if age_seconds <= 3 * 60 * 60:
        return 85.0
    if age_seconds <= 6 * 60 * 60:
        return 70.0
    if age_seconds <= 12 * 60 * 60:
        return 55.0
    if age_seconds <= 24 * 60 * 60:
        return 35.0
    return 15.0


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _latest_created_at(values) -> str | None:
    parsed_values = [
        (parsed, value)
        for value in values
        if (parsed := _parse_datetime(value)) is not None
    ]
    if not parsed_values:
        return None
    return max(parsed_values, key=lambda item: item[0])[1]
