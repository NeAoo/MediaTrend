"""
采集管理器
统一调度和管理多个数据源采集器
"""
from typing import List
from loguru import logger

from config.settings import INITIAL_COLLECT_COUNT, ENABLED_SOURCES, TIME_RANGE_MIN, TIME_RANGE_MAX
from models.hotspot import EducationHotspot, CollectionResult
from crawlers.wechat import WechatCrawler
from crawlers.xiaohongshu import XiaohongshuCrawler
from crawlers.zhihu import ZhihuCrawler
from crawlers.general import GeneralEducationCrawler
from crawlers.demo import DemoEducationCrawler


class CrawlerManager:
    """采集管理器"""
    
    def __init__(self):
        self.crawlers = {}
        self._init_crawlers()
    
    def _init_crawlers(self):
        """初始化启用的采集器"""
        crawler_map = {
            "wechat": WechatCrawler,
            "xiaohongshu": XiaohongshuCrawler,
            "zhihu": ZhihuCrawler,
            "general": GeneralEducationCrawler,
            "demo": DemoEducationCrawler,
        }
        
        for source_name in ENABLED_SOURCES:
            if source_name in crawler_map:
                self.crawlers[source_name] = crawler_map[source_name]()
                logger.info(f"已加载采集器: {source_name}")
    
    def collect_all(self, keywords: List[str] = None) -> List[EducationHotspot]:
        """
        从所有启用的数据源采集热点
        
        Args:
            keywords: 搜索关键词列表
            
        Returns:
            List[EducationHotspot]: 采集到的所有热点（去重后）
        """
        if keywords is None:
            from config.settings import KEYWORDS
            keywords = KEYWORDS
        
        all_items = []
        
        # 使用配置文件中的时间范围
        time_range = (TIME_RANGE_MIN, TIME_RANGE_MAX)
        logger.info(f"采集时间范围: {time_range[0]}-{time_range[1]} 小时")
        logger.info(f"搜索关键词: {', '.join(keywords)}")
        
        # 并行或串行调用各个采集器
        for source_name, crawler in self.crawlers.items():
            try:
                logger.info(f"开始从 {source_name} 采集...")
                result = crawler.collect(keywords, time_range_hours=time_range)
                
                all_items.extend(result.items)
                logger.info(f"{source_name} 采集到 {len(result.items)} 条内容")
                
            except Exception as e:
                logger.error(f"采集器 {source_name} 执行失败: {e}")
        
        # 去重处理（基于URL）
        unique_items = self._deduplicate(all_items)
        
        # 如果采集数量不足，记录警告
        if len(unique_items) < INITIAL_COLLECT_COUNT:
            logger.warning(
                f"采集数量不足: 当前{len(unique_items)}条，目标{INITIAL_COLLECT_COUNT}条"
            )
        else:
            # 如果超过目标数量，只取前N条
            unique_items = unique_items[:INITIAL_COLLECT_COUNT]
        
        logger.info(f"总计采集到 {len(unique_items)} 条唯一内容")
        return unique_items
    
    def _deduplicate(self, items: List[EducationHotspot]) -> List[EducationHotspot]:
        """
        基于URL去重
        
        Args:
            items: 热点列表
            
        Returns:
            List[EducationHotspot]: 去重后的列表
        """
        seen_urls = set()
        unique_items = []
        
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        
        return unique_items