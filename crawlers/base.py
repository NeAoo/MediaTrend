"""
采集器基类
定义统一的采集器接口规范
"""
from abc import ABC, abstractmethod
from typing import List
from models.hotspot import EducationHotspot, CollectionResult


class BaseCrawler(ABC):
    """采集器抽象基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def collect(self, keywords: List[str], time_range_hours: tuple = (24, 48)) -> CollectionResult:
        """
        采集热点内容

        Args:
            keywords: 搜索关键词列表
            time_range_hours: 时间范围（最小小时数，最大小时数）

        Returns:
            CollectionResult: 采集结果
        """
        pass

    @abstractmethod
    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """
        解析单条数据为标准格式

        Args:
            raw_data: 原始数据

        Returns:
            EducationHotspot: 标准化后的热点数据
        """
        pass

    def validate_time_range(self, publish_time, min_hours: int, max_hours: int) -> bool:
        """
        验证发布时间是否在指定范围内

        Args:
            publish_time: 发布时间
            min_hours: 最小小时数
            max_hours: 最大小时数

        Returns:
            bool: 是否在时间范围内
        """
        from datetime import datetime, timedelta

        now = datetime.now()
        time_diff = now - publish_time
        hours = time_diff.total_seconds() / 3600

        return min_hours <= hours <= max_hours