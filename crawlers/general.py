"""
通用教育资讯采集器
用于采集其他教育类网站的热点资讯
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
from loguru import logger

from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot, CollectionResult


class GeneralEducationCrawler(BaseCrawler):
    """通用教育资讯采集器"""

    def __init__(self):
        super().__init__("general")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        # 教育资讯网站列表
        self.education_sites = [
            {
                "name": "中国教育在线",
                "url": "https://www.eol.cn/",
                "type": "news"
            },
            {
                "name": "家长帮",
                "url": "https://www.jzb.com/",
                "type": "community"
            },
            # 可以添加更多教育类网站
        ]

    def collect(self, keywords: List[str], time_range_hours: tuple = (24, 48)) -> CollectionResult:
        """
        采集通用教育资讯

        Args:
            keywords: 教育相关关键词
            time_range_hours: 时间范围

        Returns:
            CollectionResult: 采集结果
        """
        result = CollectionResult()

        for site in self.education_sites:
            try:
                logger.info(f"正在采集: {site['name']}")

                items = self._fetch_site_news(site)

                for item in items:
                    try:
                        hotspot = self.parse_item(item)
                        if self.validate_time_range(
                            hotspot.publish_time,
                            time_range_hours[0],
                            time_range_hours[1]
                        ):
                            # 检查是否包含教育相关关键词
                            if self._is_education_related(hotspot, keywords):
                                result.items.append(hotspot)
                                result.success_count += 1
                    except Exception as e:
                        logger.error(f"解析资讯失败: {e}")
                        result.failed_count += 1

                import time
                time.sleep(2)

            except Exception as e:
                logger.error(f"采集 {site['name']} 失败: {e}")
                result.error_messages.append(str(e))

        logger.info(f"通用采集完成: 成功{result.success_count}, 失败{result.failed_count}")
        return result

    def _fetch_site_news(self, site: dict) -> List[dict]:
        """
        从指定网站获取新闻列表

        Returns:
            List[dict]: 原始新闻数据
        """
        # TODO: 根据不同网站结构实现解析逻辑
        # 这里提供基础框架

        try:
            response = self.session.get(site["url"], timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 需要根据具体网站结构调整选择器
            articles = []
            # 示例：提取文章链接和标题
            links = soup.find_all('a', href=True)[:20]  # 限制数量

            for link in links:
                title = link.get_text(strip=True)
                href = link['href']

                if title and len(title) > 5:  # 过滤太短的标题
                    articles.append({
                        "title": title,
                        "url": href if href.startswith('http') else site['url'] + href,
                        "publish_time": datetime.now(),  # 需要实际解析
                        "summary": "",
                        "source": site["name"]
                    })

            return articles

        except Exception as e:
            logger.error(f"抓取网站 {site['name']} 失败: {e}")
            return []

    def _is_education_related(self, hotspot: EducationHotspot, keywords: List[str]) -> bool:
        """判断内容是否与教育相关"""
        text = f"{hotspot.title} {hotspot.content_summary}".lower()

        education_terms = keywords + [
            "教育", "学校", "学生", "老师", "家长",
            "学习", "考试", "课程", "培训", "升学"
        ]

        return any(term in text for term in education_terms)

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """解析通用资讯数据"""
        return EducationHotspot(
            title=raw_data.get("title", ""),
            source=raw_data.get("source", "网络"),
            author=None,
            publish_time=raw_data.get("publish_time", datetime.now()),
            content_summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            tags=["教育", "资讯"]
        )