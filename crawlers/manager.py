"""
采集管理器
统一调度和管理多个数据源采集器。
"""

from typing import List

from loguru import logger

from config.settings import ENABLED_SOURCES, INITIAL_COLLECT_COUNT, TIME_RANGE_MAX, TIME_RANGE_MIN
from models.hotspot import EducationHotspot


class CrawlerManager:
    """采集管理器。"""

    def __init__(self):
        self.crawlers = {}
        self._init_crawlers()

    def _init_crawlers(self) -> None:
        """初始化启用的采集器。"""
        crawler_map = {
            "wechat": ("crawlers.wechat", "WechatCrawler"),
            "xiaohongshu": ("crawlers.xiaohongshu", "XiaohongshuCrawler"),
            "zhihu": ("crawlers.zhihu", "ZhihuCrawler"),
            "general": ("crawlers.general", "GeneralEducationCrawler"),
            "demo": ("crawlers.demo", "DemoEducationCrawler"),
        }

        for source_name in ENABLED_SOURCES:
            if source_name not in crawler_map:
                logger.warning(f"未知采集器配置，已跳过: {source_name}")
                continue

            module_name, class_name = crawler_map[source_name]
            try:
                module = __import__(module_name, fromlist=[class_name])
                crawler_class = getattr(module, class_name)
                self.crawlers[source_name] = crawler_class()
                logger.info(f"已加载采集器: {source_name}")
            except Exception as exc:
                logger.error(f"加载采集器 {source_name} 失败: {exc}")

    def collect_all(self, keywords: List[str] | None = None) -> List[EducationHotspot]:
        """从所有启用的数据源采集热点。"""
        if keywords is None:
            from config.settings import KEYWORDS

            keywords = KEYWORDS

        all_items: list[EducationHotspot] = []
        time_range = (TIME_RANGE_MIN, TIME_RANGE_MAX)
        logger.info(f"采集时间范围: {time_range[0]}-{time_range[1]} 小时")
        logger.info(f"搜索关键词: {', '.join(keywords)}")

        for source_name, crawler in self.crawlers.items():
            try:
                logger.info(f"开始从 {source_name} 采集...")
                result = crawler.collect(keywords, time_range_hours=time_range)
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

    def _deduplicate(self, items: List[EducationHotspot]) -> List[EducationHotspot]:
        """基于 URL 去重。"""
        seen_urls = set()
        unique_items = []

        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        return unique_items
