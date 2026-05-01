"""
知乎内容采集器
集成 MediaCrawler 的知乎平台数据采集。
"""

import json
import os
import subprocess
from datetime import datetime
from typing import List

from loguru import logger

from config.settings import (
    MEDIA_CRAWLER_DIR,
    MEDIA_CRAWLER_LOGIN_TYPE,
    MEDIA_CRAWLER_PYTHON_BIN,
    MEDIA_CRAWLER_TIMEOUT_SECONDS,
    ZHIHU_COOKIE,
    ZHIHU_LOGIN_TYPE,
    ZHIHU_MAX_RESULTS_PER_KEYWORD,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


class ZhihuCrawler(BaseCrawler):
    """知乎采集器。"""

    def __init__(self):
        super().__init__("zhihu")
        self.mediacrawler_dir = MEDIA_CRAWLER_DIR
        self.python_bin = MEDIA_CRAWLER_PYTHON_BIN

    def collect(self, keywords: List[str] | None = None, time_range_hours: tuple = (0, 48)) -> CollectionResult:
        if not keywords:
            logger.warning("未配置知乎搜索关键词，无法采集")
            return CollectionResult()

        max_hours = time_range_hours[1] if isinstance(time_range_hours, tuple) else time_range_hours
        result = CollectionResult()

        logger.info("开始从知乎采集教育热点...")
        logger.info(f"  关键词: {', '.join(keywords)}")
        logger.info(f"  时间范围: 最近 {max_hours} 小时")

        try:
            success = self._run_crawler(
                keywords,
                max_hours,
                timeout=MEDIA_CRAWLER_TIMEOUT_SECONDS,
            )
            if not success:
                logger.error("知乎爬虫执行失败或超时")
                result.error_messages.append("爬虫执行失败或超时")
                return result

            hotspots = self._load_and_convert_data()
            result.items = hotspots
            result.success_count = len(hotspots)
            logger.info(f"知乎采集完成，共 {len(hotspots)} 条内容")
        except Exception as exc:
            logger.error(f"知乎采集异常: {exc}", exc_info=True)
            result.error_messages.append(str(exc))

        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        try:
            time_value = raw_data.get("created_time", 0) or raw_data.get("updated_time", 0)
            if time_value:
                if time_value > 1000000000000:
                    time_value = time_value / 1000
                publish_time = datetime.fromtimestamp(time_value)
            else:
                publish_time = datetime.now()

            voteup_count = int(raw_data.get("voteup_count", 0) or 0)
            comment_count = int(raw_data.get("comment_count", 0) or 0)
            popularity = float(voteup_count + comment_count * 2)

            return EducationHotspot(
                title=raw_data.get("title", "无标题")[:100],
                source="zhihu",
                author=raw_data.get("user_nickname", "未知作者"),
                publish_time=publish_time,
                content=raw_data.get("content_text", "") or raw_data.get("desc", ""),
                url=raw_data.get("content_url", ""),
                popularity=popularity,
                cover_image=None,
                image_list=[],
                tags=["教育", "知乎"],
            )
        except Exception as exc:
            logger.warning(f"知乎数据解析失败: {exc}")
            return EducationHotspot(
                title="解析失败",
                source="zhihu",
                author="未知",
                publish_time=datetime.now(),
                content="",
                url="",
                popularity=0.0,
                cover_image=None,
                image_list=[],
                tags=[],
            )

    def _run_crawler(self, keywords: List[str], time_range_hours: int, timeout: int = 900) -> bool:
        main_file = self.mediacrawler_dir / "main.py"
        if not main_file.exists():
            logger.error(f"MediaCrawler 未找到: {main_file}")
            logger.error("请确认 `.env` 中的 MEDIA_CRAWLER_DIR 指向本项目里的 MediaCrawler 目录")
            return False

        login_type = ZHIHU_LOGIN_TYPE or MEDIA_CRAWLER_LOGIN_TYPE
        if login_type == "cookie" and not ZHIHU_COOKIE:
            logger.error("ZHIHU_LOGIN_TYPE=cookie 但未配置 ZHIHU_COOKIE")
            return False

        try:
            env = os.environ.copy()
            keywords_str = ",".join(keywords)
            env["MEDIA_CRAWLER_KEYWORDS"] = keywords_str
            env["MEDIA_CRAWLER_TIME_RANGE_MAX"] = str(time_range_hours)
            env["MEDIA_CRAWLER_MAX_NOTES_COUNT"] = str(ZHIHU_MAX_RESULTS_PER_KEYWORD)

            cmd = [
                self.python_bin,
                "main.py",
                "--platform",
                "zhihu",
                "--lt",
                login_type,
                "--type",
                "search",
            ]
            if login_type == "cookie" and ZHIHU_COOKIE:
                cmd.extend(["--cookies", ZHIHU_COOKIE])

            logger.info(f"传递给 MediaCrawler 的关键词: {keywords_str}")
            logger.info(f"时间范围: {time_range_hours} 小时")
            logger.info(f"每个关键词爬取数量: {ZHIHU_MAX_RESULTS_PER_KEYWORD}")
            logger.info(f"执行 MediaCrawler 知乎: {' '.join(cmd)}")

            completed = subprocess.run(
                cmd,
                cwd=self.mediacrawler_dir,
                env=env,
                capture_output=False,
                text=True,
                timeout=timeout,
            )
            if completed.returncode != 0:
                logger.error(f"MediaCrawler 返回非 0 退出码: {completed.returncode}")
            return completed.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"知乎爬虫执行超时（{timeout / 60:.1f} 分钟）")
            return False
        except Exception as exc:
            logger.error(f"知乎爬虫执行异常: {exc}")
            return False

    def _load_and_convert_data(self) -> List[EducationHotspot]:
        jsonl_dir = self.mediacrawler_dir / "data" / "zhihu" / "jsonl"
        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []

        jsonl_files = list(jsonl_dir.glob("search_contents_*.jsonl"))
        if not jsonl_files:
            logger.error("未找到知乎 JSONL 文件")
            return []

        latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"使用知乎数据文件: {latest_file.name}")

        hotspots = []
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_data = json.loads(line)
                        hotspots.append(self.parse_item(raw_data))
                    except json.JSONDecodeError as exc:
                        logger.warning(f"JSON 解析失败: {exc}")
            logger.info(f"成功转换 {len(hotspots)} 条知乎数据")
        except Exception as exc:
            logger.error(f"知乎数据转换失败: {exc}", exc_info=True)

        return hotspots
