"""
小红书内容采集器
集成 TrendCrawlerRuntime 的 Pipeline 到统一的采集框架。
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from config.settings import (
    TREND_CRAWLER_RUNTIME_DIR,
    TREND_CRAWLER_RUNTIME_LOGIN_TYPE,
    TREND_CRAWLER_RUNTIME_PYTHON_BIN,
    TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
    XIAOHONGSHU_COOKIE,
    XIAOHONGSHU_LOGIN_TYPE,
    XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


class XiaohongshuCrawler(BaseCrawler):
    """小红书采集器。"""

    def __init__(self):
        super().__init__("xiaohongshu")
        self.trendcrawler_dir = TREND_CRAWLER_RUNTIME_DIR
        self.python_bin = TREND_CRAWLER_RUNTIME_PYTHON_BIN

    def collect(self, keywords: List[str] | None = None, time_range_hours: tuple = (0, 48)) -> CollectionResult:
        if not keywords:
            logger.warning("未配置小红书搜索关键词，无法采集")
            return CollectionResult()

        max_hours = time_range_hours[1] if isinstance(time_range_hours, tuple) else time_range_hours
        result = CollectionResult()

        logger.info("开始从小红书采集教育热点...")
        logger.info(f"  关键词: {', '.join(keywords)}")
        logger.info(f"  时间范围: 最近 {max_hours} 小时")

        try:
            success = self._run_crawler(
                keywords,
                max_hours,
                timeout=TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
            )
            if not success:
                logger.error("小红书爬虫执行失败或超时")
                result.error_messages.append("爬虫执行失败或超时")
                return result

            hotspots = self._load_and_convert_data()
            result.items = hotspots
            result.success_count = len(hotspots)
            logger.info(f"小红书采集完成，共 {len(hotspots)} 条内容")
        except Exception as exc:
            logger.error(f"小红书采集异常: {exc}", exc_info=True)
            result.error_messages.append(str(exc))

        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        try:
            time_value = raw_data.get("time", 0)
            if time_value:
                if time_value > 1000000000000:
                    time_value = time_value / 1000
                publish_time = datetime.fromtimestamp(time_value)
            else:
                publish_time = datetime.now()

            image_list = self._parse_image_list(raw_data.get("image_list", ""))
            return EducationHotspot(
                title=raw_data.get("title", "无标题"),
                source="xiaohongshu",
                author=raw_data.get("nickname", "未知作者"),
                publish_time=publish_time,
                content=raw_data.get("desc", ""),
                url=raw_data.get("note_url", ""),
                popularity=float(raw_data.get("liked_count", 0) or 0),
                cover_image=self._extract_first_image(raw_data.get("image_list", "")),
                image_list=image_list,
                tags=self._parse_tags(raw_data.get("tag_list", "")),
            )
        except Exception as exc:
            logger.warning(f"小红书数据解析失败: {exc}, 数据ID: {raw_data.get('note_id', 'unknown')}")
            return EducationHotspot(
                title=raw_data.get("title", "未知标题"),
                source="xiaohongshu",
                author=raw_data.get("nickname", "未知作者"),
                publish_time=datetime.now(),
                content=raw_data.get("desc", ""),
                url=raw_data.get("note_url", ""),
                popularity=float(raw_data.get("liked_count", 0) or 0),
                tags=[],
            )

    def _extract_first_image(self, image_list_str: str) -> Optional[str]:
        if not image_list_str:
            return None
        try:
            urls = image_list_str.split(",")
            return urls[0].strip() if urls else None
        except Exception:
            return None

    def _parse_image_list(self, image_list_str: str) -> List[str]:
        if not image_list_str:
            return []
        try:
            return [url.strip() for url in image_list_str.split(",") if url.strip()]
        except Exception:
            return []

    def _parse_tags(self, tag_list_str: str) -> List[str]:
        if not tag_list_str:
            return []
        try:
            return [tag.strip() for tag in tag_list_str.split(",") if tag.strip()]
        except Exception:
            return []

    def _run_crawler(self, keywords: List[str], time_range_hours: int, timeout: int = 900) -> bool:
        main_file = self.trendcrawler_dir / "main.py"
        if not main_file.exists():
            logger.error(f"TrendCrawlerRuntime 未找到: {main_file}")
            logger.error("请确认 `.env` 中的 TREND_CRAWLER_RUNTIME_DIR 指向本项目里的 TrendCrawlerRuntime 目录")
            return False

        login_type = XIAOHONGSHU_LOGIN_TYPE or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
        if login_type == "cookie" and not XIAOHONGSHU_COOKIE:
            logger.error("XIAOHONGSHU_LOGIN_TYPE=cookie 但未配置 XIAOHONGSHU_COOKIE")
            return False

        try:
            env = os.environ.copy()
            keywords_str = ",".join(keywords)
            env["TREND_CRAWLER_RUNTIME_KEYWORDS"] = keywords_str
            env["TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX"] = str(time_range_hours)
            env["TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT"] = str(XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD)

            cmd = [
                self.python_bin,
                "main.py",
                "--platform",
                "xhs",
                "--lt",
                login_type,
                "--type",
                "search",
            ]
            if login_type == "cookie" and XIAOHONGSHU_COOKIE:
                cmd.extend(["--cookies", XIAOHONGSHU_COOKIE])

            logger.info(f"传递给 TrendCrawlerRuntime 的关键词: {keywords_str}")
            logger.info(f"时间范围: {time_range_hours} 小时")
            logger.info(f"每个关键词爬取数量: {XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD}")
            logger.info(f"执行 TrendCrawlerRuntime: {' '.join(cmd)}")

            completed = subprocess.run(
                cmd,
                cwd=self.trendcrawler_dir,
                env=env,
                capture_output=False,
                text=True,
                timeout=timeout,
            )
            if completed.returncode != 0:
                logger.error(f"TrendCrawlerRuntime 返回非 0 退出码: {completed.returncode}")
            return completed.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"爬虫执行超时（{timeout / 60:.1f} 分钟）")
            return False
        except Exception as exc:
            logger.error(f"爬虫执行异常: {exc}")
            return False

    def _load_and_convert_data(self) -> List[EducationHotspot]:
        jsonl_dir = self.trendcrawler_dir / "data" / "xhs" / "jsonl"
        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []

        jsonl_files = list(jsonl_dir.glob("search_contents_*.jsonl"))
        if not jsonl_files:
            logger.error("未找到 JSONL 文件")
            return []

        latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"使用数据文件: {latest_file.name}")

        hotspots = []
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_data = json.loads(line)
                        hotspots.append(self.parse_item(raw_data))
                    except json.JSONDecodeError as exc:
                        logger.warning(f"第{line_num}行 JSON 解析失败: {exc}")
            logger.info(f"成功转换 {len(hotspots)} 条小红书数据")
        except Exception as exc:
            logger.error(f"小红书数据转换失败: {exc}", exc_info=True)

        return hotspots
