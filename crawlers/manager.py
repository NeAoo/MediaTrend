"""
采集管理器
统一调度和管理多个数据源采集器。
"""

from typing import List

from loguru import logger

from config.settings import (
    ENABLED_SOURCES,
    get_source_account_time_range,
    get_source_creator_urls,
    get_source_keyword_time_range,
    get_source_keywords,
)
from models.hotspot import EducationHotspot


CRAWLER_MAP = {
    "wechat": ("crawlers.wechat", "WechatCrawler"),
    "wechat_mp": ("crawlers.wechat_mp", "WechatMpCrawler"),
    "xiaohongshu": ("crawlers.xiaohongshu", "XiaohongshuCrawler"),
    "zhihu": ("crawlers.zhihu", "ZhihuCrawler"),
    "google_news": ("crawlers.google_news", "GoogleNewsCrawler"),
    "aihot": ("crawlers.aihot", "AihotCrawler"),
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
        source_creator_urls: dict[str, List[str]] | None = None,
        source_keyword_time_ranges: dict[str, tuple[int, int]] | None = None,
        source_account_time_ranges: dict[str, tuple[int, int]] | None = None,
    ) -> List[EducationHotspot]:
        """从所有启用的数据源采集热点。"""
        all_items: list[EducationHotspot] = []

        for source_name, crawler in self.crawlers.items():
            try:
                current_keywords = self._keywords_for_source(
                    source_name,
                    keywords=keywords,
                    source_keywords=source_keywords,
                )
                current_creator_urls = self._creator_urls_for_source(
                    source_name,
                    source_creator_urls=source_creator_urls,
                )
                keyword_time_range = self._keyword_time_range_for_source(
                    source_name,
                    source_keyword_time_ranges=source_keyword_time_ranges,
                )
                account_time_range = self._account_time_range_for_source(
                    source_name,
                    source_account_time_ranges=source_account_time_ranges,
                )
                logger.info(f"开始从 {source_name} 采集...")
                if source_name == "wechat_mp":
                    logger.info(
                        f"{source_name} 公众号账号: {', '.join(current_keywords)}"
                    )
                else:
                    logger.info(
                        f"{source_name} 搜索关键词: {', '.join(current_keywords)}"
                    )
                if current_creator_urls:
                    logger.info(f"{source_name} 账号 URL 数量: {len(current_creator_urls)}")
                if source_name != "wechat_mp":
                    logger.info(
                        f"{source_name} 关键词时间范围: "
                        f"{keyword_time_range[0]}-{keyword_time_range[1]} 小时"
                    )
                if source_name == "wechat_mp" or current_creator_urls:
                    logger.info(
                        f"{source_name} 账号时间范围: "
                        f"{account_time_range[0]}-{account_time_range[1]} 小时"
                    )
                if source_name in {"xiaohongshu", "zhihu"}:
                    result = crawler.collect(
                        current_keywords,
                        time_range_hours=keyword_time_range,
                        creator_urls=current_creator_urls,
                        creator_time_range_hours=account_time_range,
                    )
                elif source_name == "wechat_mp":
                    result = crawler.collect(
                        current_keywords,
                        time_range_hours=account_time_range,
                    )
                else:
                    result = crawler.collect(
                        current_keywords,
                        time_range_hours=keyword_time_range,
                    )
                all_items.extend(result.items)
                logger.info(f"{source_name} 采集到 {len(result.items)} 条内容")
            except Exception as exc:
                logger.error(f"采集器 {source_name} 执行失败: {exc}")

        unique_items = self._deduplicate(all_items)

        logger.info(f"总计采集到 {len(unique_items)} 条唯一内容，将全部进入打分")
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

    def _creator_urls_for_source(
        self,
        source_name: str,
        source_creator_urls: dict[str, List[str]] | None,
    ) -> List[str]:
        if source_creator_urls and source_name in source_creator_urls:
            return source_creator_urls[source_name]
        return get_source_creator_urls(source_name)

    def _keyword_time_range_for_source(
        self,
        source_name: str,
        source_keyword_time_ranges: dict[str, tuple[int, int]] | None,
    ) -> tuple[int, int]:
        if source_keyword_time_ranges and source_name in source_keyword_time_ranges:
            return source_keyword_time_ranges[source_name]
        return get_source_keyword_time_range(source_name)

    def _account_time_range_for_source(
        self,
        source_name: str,
        source_account_time_ranges: dict[str, tuple[int, int]] | None,
    ) -> tuple[int, int]:
        if source_account_time_ranges and source_name in source_account_time_ranges:
            return source_account_time_ranges[source_name]
        return get_source_account_time_range(source_name)

    def _deduplicate(self, items: List[EducationHotspot]) -> List[EducationHotspot]:
        """基于 URL 去重。"""
        seen_urls = set()
        unique_items = []

        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        return unique_items
