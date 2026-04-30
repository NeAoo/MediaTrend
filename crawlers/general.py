"""
通用教育资讯采集器
用于采集教育类网站的热点资讯。
"""

import re
from datetime import datetime
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger

from config.settings import GENERAL_MAX_LINKS_PER_SITE, GENERAL_NEWS_SITES
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


class GeneralEducationCrawler(BaseCrawler):
    """通用教育资讯采集器。"""

    def __init__(self):
        super().__init__("general")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
        )
        self.education_sites = GENERAL_NEWS_SITES

    def collect(self, keywords: List[str], time_range_hours: tuple = (0, 24)) -> CollectionResult:
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
                            time_range_hours[1],
                        ) and self._is_education_related(hotspot, keywords):
                            result.items.append(hotspot)
                            result.success_count += 1
                    except Exception as exc:
                        logger.error(f"解析资讯失败: {exc}")
                        result.failed_count += 1

            except Exception as exc:
                logger.error(f"采集 {site['name']} 失败: {exc}")
                result.error_messages.append(str(exc))

        logger.info(f"通用采集完成: 成功{result.success_count}, 失败{result.failed_count}")
        return result

    def _fetch_site_news(self, site: dict) -> List[dict]:
        try:
            response = self.session.get(site["url"], timeout=10)
            response.encoding = response.apparent_encoding or response.encoding or "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            articles = []
            links = soup.find_all("a", href=True)[:GENERAL_MAX_LINKS_PER_SITE]
            for link in links:
                title = link.get_text(strip=True)
                href = link["href"]
                publish_time = self._extract_publish_time(link, href)

                if title and len(title) > 5 and publish_time:
                    articles.append(
                        {
                            "title": title,
                            "url": urljoin(site["url"], href),
                            "publish_time": publish_time,
                            "summary": "",
                            "source": site["name"],
                        }
                    )

            return articles
        except Exception as exc:
            logger.error(f"抓取网站 {site['name']} 失败: {exc}")
            return []

    def _extract_publish_time(self, link, href: str) -> datetime | None:
        """从链接文本、周边 HTML 或 URL 中提取发布日期。"""
        text_parts = [href or "", link.get_text(" ", strip=True)]
        parent = link.parent
        if parent:
            text_parts.append(parent.get_text(" ", strip=True))
        raw = " ".join(text_parts)

        patterns = [
            r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})",
            r"(20\d{2})(\d{2})(\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw)
            if not match:
                continue
            year, month, day = [int(part) for part in match.groups()]
            try:
                return datetime(year, month, day)
            except ValueError:
                continue
        return None

    def _is_education_related(self, hotspot: EducationHotspot, keywords: List[str]) -> bool:
        text = f"{hotspot.title} {hotspot.content_summary}".lower()
        education_terms = keywords + ["教育", "学校", "学生", "老师", "家长", "学习", "考试", "课程", "培训", "升学"]
        return any(term in text for term in education_terms)

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        return EducationHotspot(
            title=raw_data.get("title", ""),
            source=raw_data.get("source", "网络"),
            author=None,
            publish_time=raw_data.get("publish_time", datetime.now()),
            content_summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            tags=["教育", "资讯"],
        )
