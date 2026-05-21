"""AI HOT public API crawler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, List

import requests
from loguru import logger

from config.settings import (
    AIHOT_BASE_URL,
    AIHOT_CATEGORIES,
    AIHOT_KEYWORDS,
    AIHOT_MAX_RESULTS_PER_QUERY,
    AIHOT_MODE,
    AIHOT_REQUEST_TIMEOUT_SECONDS,
    AIHOT_USER_AGENT,
)
from crawlers.base import BaseCrawler, resolve_query_lookback_hours
from models.hotspot import CollectionResult, EducationHotspot


AIHOT_ITEMS_PATH = "/api/public/items"
AIHOT_CATEGORY_LABELS = {
    "ai-models": "模型发布/更新",
    "ai-products": "产品发布/更新",
    "industry": "行业动态",
    "paper": "论文研究",
    "tip": "技巧与观点",
}


class AihotCrawler(BaseCrawler):
    """Collect AI industry reference items from AI HOT."""

    def __init__(self):
        super().__init__("aihot")

    def collect(
        self,
        keywords: List[str] | None = None,
        time_range_hours: tuple = (0, 24),
    ) -> CollectionResult:
        result = CollectionResult()
        selected_keywords = AIHOT_KEYWORDS if keywords is None else keywords
        queries = self._build_queries(selected_keywords, AIHOT_CATEGORIES)
        since = self._since_iso(time_range_hours)
        seen_ids: set[str] = set()

        logger.info("开始从 AI HOT 采集 AI 行业参考内容...")
        logger.info(f"AI HOT mode: {AIHOT_MODE}")
        logger.info(f"AI HOT 查询数量: {len(queries)}")
        if since:
            logger.info(f"AI HOT since: {since}")

        for query in queries:
            try:
                raw_items = self._fetch_items(
                    keyword=query.get("keyword"),
                    category=query.get("category"),
                    since=since,
                )
                for raw_item in raw_items:
                    item_id = str(raw_item.get("id") or raw_item.get("url") or "")
                    if item_id and item_id in seen_ids:
                        continue
                    if item_id:
                        seen_ids.add(item_id)
                    hotspot = self.parse_item(raw_item)
                    if self.validate_time_range(
                        hotspot.publish_time,
                        time_range_hours[0],
                        time_range_hours[1],
                    ):
                        result.items.append(hotspot)
                        result.success_count += 1
            except Exception as exc:
                label = self._query_label(query)
                logger.error(f"AI HOT 查询失败 ({label}): {exc}")
                result.error_messages.append(f"{label}: {exc}")

        result.items.sort(key=lambda item: item.publish_time, reverse=True)
        logger.info(f"AI HOT 采集完成，共 {len(result.items)} 条内容")
        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        category = raw_data.get("category")
        title = raw_data.get("title") or raw_data.get("title_en") or "无标题"
        summary = raw_data.get("summary") or raw_data.get("title_en") or ""
        tags = ["AI HOT", "AI 行业"]
        if category:
            tags.append(str(category))
            label = AIHOT_CATEGORY_LABELS.get(str(category))
            if label:
                tags.append(label)

        return EducationHotspot(
            title=title,
            source="aihot",
            author=raw_data.get("source") or "AI HOT",
            publish_time=self._parse_publish_time(raw_data.get("publishedAt")),
            content=summary,
            url=raw_data.get("url", ""),
            popularity=None,
            cover_image=None,
            image_list=[],
            tags=tags,
        )

    def _build_queries(
        self,
        keywords: list[str],
        categories: list[str],
    ) -> list[dict[str, str | None]]:
        normalized_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
        normalized_categories = [
            category.strip() for category in categories if category.strip()
        ]

        if normalized_keywords and normalized_categories:
            return [
                {"keyword": keyword, "category": category}
                for keyword in normalized_keywords
                for category in normalized_categories
            ]
        if normalized_keywords:
            return [
                {"keyword": keyword, "category": None}
                for keyword in normalized_keywords
            ]
        if normalized_categories:
            return [
                {"keyword": None, "category": category}
                for category in normalized_categories
            ]
        return [{"keyword": None, "category": None}]

    def _fetch_items(
        self,
        keyword: str | None,
        category: str | None,
        since: str | None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {
            "mode": AIHOT_MODE,
            "take": AIHOT_MAX_RESULTS_PER_QUERY,
        }
        if keyword:
            params["q"] = keyword
        if category:
            params["category"] = category
        if since:
            params["since"] = since

        response = requests.get(
            f"{AIHOT_BASE_URL}{AIHOT_ITEMS_PATH}",
            params=params,
            headers={"User-Agent": AIHOT_USER_AGENT},
            timeout=AIHOT_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 304:
            return []
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", [])
        if not isinstance(items, list):
            raise ValueError("AI HOT response.items must be a list")
        return [item for item in items if isinstance(item, dict)]

    def _parse_publish_time(self, value: str | None) -> datetime:
        if not value:
            return datetime.now()
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                return parsed.astimezone().replace(tzinfo=None)
            return parsed
        except ValueError:
            logger.debug(f"AI HOT 时间解析失败，使用当前时间: {value}")
            return datetime.now()

    def _since_iso(self, time_range_hours: tuple[int, int] | None) -> str | None:
        if not time_range_hours:
            return None
        now = datetime.now(timezone.utc)
        lookback_hours = resolve_query_lookback_hours(
            now.replace(tzinfo=None),
            time_range_hours[0],
            time_range_hours[1],
        )
        if lookback_hours <= 0:
            return None
        since = now - timedelta(hours=lookback_hours)
        return since.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _query_label(self, query: dict[str, str | None]) -> str:
        keyword = query.get("keyword") or "*"
        category = query.get("category") or "*"
        return f"keyword={keyword}, category={category}"
