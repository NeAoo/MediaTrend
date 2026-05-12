"""Google News keyword crawler."""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterator, List
from urllib.parse import quote_plus

import feedparser
import requests
from loguru import logger

from config.settings import (
    GOOGLE_NEWS_COUNTRY,
    GOOGLE_NEWS_KEYWORDS,
    GOOGLE_NEWS_LANGUAGE,
    GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD,
    GOOGLE_NEWS_PERIOD,
    GOOGLE_NEWS_PROXY_URL,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


GOOGLE_NEWS_BATCH_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS = 8


class GoogleNewsCrawler(BaseCrawler):
    """Collect keyword results from Google News."""

    def __init__(self):
        super().__init__("google_news")

    def collect(
        self,
        keywords: List[str] | None = None,
        time_range_hours: tuple = (0, 24),
    ) -> CollectionResult:
        result = CollectionResult()
        selected_keywords = keywords or GOOGLE_NEWS_KEYWORDS
        if not selected_keywords:
            logger.warning("未配置 Google News 搜索关键词，无法采集")
            return result

        with self._proxy_env(GOOGLE_NEWS_PROXY_URL):
            for keyword in selected_keywords:
                try:
                    logger.info(f"正在搜索 Google News 关键词: {keyword}")
                    raw_items = self._get_news_items(keyword)
                    for raw_item in raw_items[:GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD]:
                        raw_item["source_keyword"] = keyword
                        raw_item["resolved_url"] = raw_item.get("url", "")
                        hotspot = self.parse_item(raw_item)
                        if self.validate_time_range(
                            hotspot.publish_time,
                            time_range_hours[0],
                            time_range_hours[1],
                        ):
                            result.items.append(hotspot)
                            result.success_count += 1
                except Exception as exc:
                    logger.error(f"Google News 关键词 {keyword} 采集失败: {exc}")
                    result.error_messages.append(f"{keyword}: {exc}")

        result.items.sort(key=lambda item: item.publish_time, reverse=True)
        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        publish_time = self._parse_publish_time(raw_data.get("published date"))
        publisher = raw_data.get("publisher") or {}
        source_keyword = raw_data.get("source_keyword", "")
        tags = ["教育", "Google News"]
        if source_keyword:
            tags.append(source_keyword)
        return EducationHotspot(
            title=raw_data.get("title", "") or "无标题",
            source="google_news",
            author=publisher.get("title") if isinstance(publisher, dict) else None,
            publish_time=publish_time,
            content=raw_data.get("description", "") or "",
            url=raw_data.get("resolved_url") or raw_data.get("url", ""),
            popularity=None,
            cover_image=None,
            image_list=[],
            tags=tags,
        )

    def _get_news_items(self, keyword: str) -> list[dict]:
        response = requests.get(
            self._build_search_url(keyword),
            timeout=GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        if getattr(feed, "bozo", False):
            logger.debug(f"Google News RSS 解析警告: {getattr(feed, 'bozo_exception', '')}")

        items = []
        for entry in feed.entries[:GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD]:
            source = entry.get("source") or {}
            if not isinstance(source, dict):
                source = {"title": str(source)}
            items.append(
                {
                    "title": entry.get("title", ""),
                    "description": self._clean_description(
                        entry.get("summary", "") or entry.get("description", "")
                    ),
                    "published date": entry.get("published", ""),
                    "url": entry.get("link", ""),
                    "publisher": {"title": source.get("title", "")},
                }
            )
        return items

    def _build_search_url(self, keyword: str) -> str:
        query = keyword
        if GOOGLE_NEWS_PERIOD:
            query = f"{query} when:{GOOGLE_NEWS_PERIOD}"
        return (
            f"{GOOGLE_NEWS_RSS_URL}?q={quote_plus(query)}"
            f"&hl={GOOGLE_NEWS_LANGUAGE}"
            f"&gl={GOOGLE_NEWS_COUNTRY}"
            f"&ceid={GOOGLE_NEWS_COUNTRY}:{GOOGLE_NEWS_LANGUAGE}"
        )

    def _clean_description(self, value: str) -> str:
        if not value:
            return ""
        text = re.sub(r"<[^>]+>", "", value)
        return re.sub(r"\s+", " ", text).strip()

    def _parse_publish_time(self, value: str | None) -> datetime:
        if not value:
            return datetime.now()
        try:
            parsed = parsedate_to_datetime(value)
            return parsed.replace(tzinfo=None)
        except (TypeError, ValueError):
            logger.debug(f"Google News 时间解析失败，使用当前时间: {value}")
            return datetime.now()

    def _resolve_google_news_url(self, url: str) -> str:
        if not url or "news.google.com" not in url:
            return url
        try:
            params = self._get_google_params(url)
            if not params:
                return url
            resolved = self._get_origin_url(
                source=params["source"],
                sign=params["sign"],
                ts=params["ts"],
            )
            return resolved or url
        except Exception as exc:
            logger.debug(f"Google News 原始链接解析失败，保留原链接: {exc}")
            return url

    def _get_google_params(self, url: str) -> dict[str, str]:
        response = requests.get(url, timeout=GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        text = response.text
        sign = re.search(r'data-n-a-sg="([^"]+)"', text)
        ts = re.search(r'data-n-a-ts="([^"]+)"', text)
        source = re.search(r'data-n-a-id="([^"]+)"', text)
        if not sign or not ts or not source:
            return {}
        return {
            "sign": sign.group(1),
            "ts": ts.group(1),
            "source": source.group(1),
        }

    def _get_origin_url(self, source: str, sign: str, ts: str) -> str:
        payload = [
            "Fbv4je",
            (
                '["garturlreq",[[["zh-CN","CN",["FINANCE_TOP_INDICES",'
                '"WEB_TEST_1_0_0"],null,null,1,1,"CN:zh-Hans",null,180,'
                f'null,null,null,null,null,0,null,null,[1608992183,723341000]],'
                f'"zh-CN","CN",1,[2,3,4,8],1,0,"655000234",0,0,null,0],'
                f'"{source}",{ts},"{sign}"]'
            ),
        ]
        data = f"f.req={json.dumps([[payload]])}"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
        response = requests.post(
            GOOGLE_NEWS_BATCH_URL,
            headers=headers,
            data=data,
            timeout=GOOGLE_NEWS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        match = re.search(
            r'\[\\"wrb.fr\\",\\"Fbv4je\\",\\"(.*?)\\",null',
            response.text,
        )
        if not match:
            return ""
        return json.loads(match.group(1))[1]

    @contextmanager
    def _proxy_env(self, proxy_url: str) -> Iterator[None]:
        if not proxy_url:
            yield
            return

        old_http = os.environ.get("http_proxy")
        old_https = os.environ.get("https_proxy")
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        try:
            yield
        finally:
            self._restore_env("http_proxy", old_http)
            self._restore_env("https_proxy", old_https)

    def _restore_env(self, key: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
