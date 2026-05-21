"""
采集器基类
定义统一的采集器接口规范
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
from models.hotspot import EducationHotspot, CollectionResult


def resolve_time_window(
    now: datetime,
    min_hours: int,
    max_hours: int,
) -> tuple[datetime, datetime]:
    """
    将配置里的小时窗口转换为实际过滤窗口。

    前端用“几天内”表达时间范围，并保存为 max=天数*24、min=0。
    运行时不做自然日换算，直接按最近 N 小时滚动窗口过滤：
    1 天内 = 最近 24 小时；2 天内 = 最近 48 小时。
    """
    safe_min_hours = max(0, int(min_hours))
    safe_max_hours = max(safe_min_hours, int(max_hours))

    window_start = now - timedelta(hours=safe_max_hours)
    window_end = now - timedelta(hours=safe_min_hours)
    return window_start, window_end


def resolve_query_lookback_hours(
    now: datetime,
    min_hours: int,
    max_hours: int,
) -> int:
    """
    给上游采集工具使用的回看小时数。

    与 UI 的“几天内”保持直觉一致：1 天就是 24 小时，2 天就是 48 小时。
    """
    return max(1, int(max_hours))


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
        now = datetime.now()
        window_start, window_end = resolve_time_window(now, min_hours, max_hours)

        return window_start <= publish_time <= window_end
