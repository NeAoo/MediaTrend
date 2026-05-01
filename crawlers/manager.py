"""
采集管理器
统一调度和管理多个数据源采集器。
"""

from typing import List

from loguru import logger

from config.settings import (
    ENABLED_SOURCES,
    INITIAL_COLLECT_COUNT,
    TIME_RANGE_MAX,
    TIME_RANGE_MIN,
    get_source_keywords,
)
from models.hotspot import EducationHotspot


CRAWLER_MAP = {
    "wechat": ("crawlers.wechat", "WechatCrawler"),
    "wechat_mp": ("crawlers.wechat_mp", "WechatMpCrawler"),
    "xiaohongshu": ("crawlers.xiaohongshu", "XiaohongshuCrawler"),
    "zhihu": ("crawlers.zhihu", "ZhihuCrawler"),
    "general": ("crawlers.general", "GeneralEducationCrawler"),
    "demo": ("crawlers.demo", "DemoEducationCrawler"),
}

AVAILABLE_SOURCES = list(CRAWLER_MAP.keys())


class CrawlerManager:
    """采集管理器。"""

    def __init__(self, enabled_sources: List[str] | None = None):
        self.enabled_sources = enabled_sources or ENABLED_SOURCES
        self.crawlers = {}
        self._init_crawlers()

    def _init_crawlers(self) -> None:
        """初始化启用的采集器。"""
        for source_name in self.enabled_sources:
            if source_name not in CRAWLER_MAP:
                logger.warning(f"未知采集器配置，已跳过: {source_name}")
                continue

            module_name, class_name = CRAWLER_MAP[source_name]
            try:
                module = __import__(module_name, fromlist=[class_name])
                crawler_class = getattr(module, class_name)
                self.crawlers[source_name] = crawler_class()
                logger.info(f"已加载采集器: {source_name}")
            except Exception as exc:
                logger.error(f"加载采集器 {source_name} 失败: {exc}")

    def collect_all(
        self,
        keywords: List[str] | None = None,
        source_keywords: dict[str, List[str]] | None = None,
    ) -> List[EducationHotspot]:
        """从所有启用的数据源采集热点。"""
        all_items: list[EducationHotspot] = []
        time_range = (TIME_RANGE_MIN, TIME_RANGE_MAX)
        logger.info(f"采集时间范围: {time_range[0]}-{time_range[1]} 小时")

        for source_name, crawler in self.crawlers.items():
            try:
                current_keywords = self._keywords_for_source(
                    source_name,
                    keywords=keywords,
                    source_keywords=source_keywords,
                )
                logger.info(f"开始从 {source_name} 采集...")
                logger.info(f"{source_name} 搜索关键词: {', '.join(current_keywords)}")
                result = crawler.collect(current_keywords, time_range_hours=time_range)
                all_items.extend(result.items)
                logger.info(f"{source_name} 采集到 {len(result.items)} 条内容")
            except Exception as exc:
                logger.error(f"采集器 {source_name} 执行失败: {exc}")

        unique_items = self._deduplicate(all_items)

        if len(unique_items) < INITIAL_COLLECT_COUNT:
            logger.warning(f"采集数量不足: 当前{len(unique_items)}条，目标{INITIAL_COLLECT_COUNT}条")
        else:
            unique_items = unique_items[:INITIAL_COLLECT_COUNT]

        logger.info(f"总计采集到 {len(unique_items)} 条唯一内容")
        return unique_items

    def _keywords_for_source(
        self,
        source_name: str,
        keywords: List[str] | None,
        source_keywords: dict[str, List[str]] | None,
    ) -> List[str]:
        if keywords is not None:
            return keywords
        if source_keywords and source_name in source_keywords:
            return source_keywords[source_name]
        return get_source_keywords(source_name)

    def _deduplicate(self, items: List[EducationHotspot]) -> List[EducationHotspot]:
        """基于 URL 去重。"""
        seen_urls = set()
        unique_items = []

        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        return unique_items
