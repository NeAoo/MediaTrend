"""
知乎内容采集器
集成 TrendCrawlerRuntime 的知乎平台数据采集。
"""

import json
import os
import subprocess
from datetime import datetime
from typing import List

from loguru import logger

from config.settings import (
    TREND_CRAWLER_RUNTIME_DIR,
    TREND_CRAWLER_RUNTIME_LOGIN_TYPE,
    TREND_CRAWLER_RUNTIME_PYTHON_BIN,
    TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
    ZHIHU_ACCOUNT_TIME_RANGE_HOURS,
    ZHIHU_COOKIE,
    ZHIHU_CREATOR_URLS,
    ZHIHU_KEYWORD_TIME_RANGE_HOURS,
    ZHIHU_LOGIN_TYPE,
    ZHIHU_MAX_RESULTS_PER_ACCOUNT,
    ZHIHU_MAX_RESULTS_PER_KEYWORD,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


class ZhihuCrawler(BaseCrawler):
    """知乎采集器。"""

    def __init__(self):
        super().__init__("zhihu")
        self.trendcrawler_dir = TREND_CRAWLER_RUNTIME_DIR
        self.python_bin = TREND_CRAWLER_RUNTIME_PYTHON_BIN

    def collect(
        self,
        keywords: List[str] | None = None,
        time_range_hours: tuple | None = None,
        creator_urls: List[str] | None = None,
        creator_time_range_hours: tuple | None = None,
    ) -> CollectionResult:
        selected_keywords = keywords or []
        selected_creator_urls = (
            ZHIHU_CREATOR_URLS if creator_urls is None else creator_urls
        )
        if not selected_keywords and not selected_creator_urls:
            logger.warning("未配置知乎关键词或账号 URL，无法采集")
            return CollectionResult()

        result = CollectionResult()
        keyword_time_range = self._normalize_time_range(
            time_range_hours or ZHIHU_KEYWORD_TIME_RANGE_HOURS
        )
        account_time_range = self._normalize_time_range(
            creator_time_range_hours
            or time_range_hours
            or ZHIHU_ACCOUNT_TIME_RANGE_HOURS
        )
        keyword_max_hours = self._max_hours(keyword_time_range)
        account_max_hours = self._max_hours(account_time_range)
        hotspots: list[EducationHotspot] = []

        logger.info("开始从知乎采集教育热点...")
        if selected_keywords:
            logger.info(f"  关键词: {', '.join(selected_keywords)}")
            logger.info(
                f"  关键词时间范围: {keyword_time_range[0]}-{keyword_time_range[1]} 小时"
            )
        if selected_creator_urls:
            logger.info(f"  账号 URL 数量: {len(selected_creator_urls)}")
            logger.info(
                f"  账号时间范围: {account_time_range[0]}-{account_time_range[1]} 小时"
            )

        try:
            if selected_keywords:
                success = self._run_trendcrawler(
                    mode="search",
                    items=selected_keywords,
                    max_count=ZHIHU_MAX_RESULTS_PER_KEYWORD,
                    time_range_hours=keyword_max_hours,
                    timeout=TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
                )
                if success:
                    hotspots.extend(
                        self._load_and_convert_data(
                            ["search_contents_*.jsonl"],
                            time_range_hours=keyword_time_range,
                            limit=ZHIHU_MAX_RESULTS_PER_KEYWORD
                            * len(selected_keywords),
                        )
                    )
                else:
                    result.error_messages.append("知乎关键词搜索执行失败或超时")

            if selected_creator_urls:
                success = self._run_trendcrawler(
                    mode="creator",
                    items=selected_creator_urls,
                    max_count=ZHIHU_MAX_RESULTS_PER_ACCOUNT,
                    time_range_hours=account_max_hours,
                    timeout=TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
                )
                if success:
                    hotspots.extend(
                        self._load_and_convert_data(
                            ["creator_contents_*.jsonl"],
                            time_range_hours=account_time_range,
                            limit=ZHIHU_MAX_RESULTS_PER_ACCOUNT
                            * len(selected_creator_urls),
                        )
                    )
                else:
                    result.error_messages.append("知乎账号采集执行失败或超时")

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

    def _run_trendcrawler(
        self,
        mode: str,
        items: List[str],
        max_count: int,
        time_range_hours: int,
        timeout: int = 900,
    ) -> bool:
        main_file = self.trendcrawler_dir / "main.py"
        if not main_file.exists():
            logger.error(f"TrendCrawlerRuntime 未找到: {main_file}")
            logger.error("请确认 config.yaml 中 trend_crawler_runtime.dir 指向有效的 TrendCrawlerRuntime 目录")
            return False

        login_type = ZHIHU_LOGIN_TYPE or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
        if login_type == "cookie" and not ZHIHU_COOKIE:
            logger.error("zhihu.login_type=cookie 但未配置 ZHIHU_COOKIE")
            return False

        try:
            env = os.environ.copy()
            env["TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX"] = str(time_range_hours)
            env["TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT"] = str(max_count)

            cmd = [
                self.python_bin,
                "main.py",
                "--platform",
                "zhihu",
                "--lt",
                login_type,
                "--type",
                mode,
            ]
            if mode == "search":
                keywords_str = ",".join(items)
                env["TREND_CRAWLER_RUNTIME_KEYWORDS"] = keywords_str
                cmd.extend(["--keywords", keywords_str])
            elif mode == "creator":
                cmd.extend(["--creator_id", ",".join(items)])
            else:
                logger.error(f"未知知乎采集模式: {mode}")
                return False

            if login_type == "cookie" and ZHIHU_COOKIE:
                cmd.extend(["--cookies", ZHIHU_COOKIE])

            logger.info(f"知乎 {mode} 输入数量: {len(items)}")
            logger.info(f"时间范围: {time_range_hours} 小时")
            logger.info(f"采集数量上限: {max_count}")
            logger.info(f"执行 TrendCrawlerRuntime 知乎 {mode}: {' '.join(cmd)}")

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
            logger.error(f"知乎 {mode} 执行超时（{timeout / 60:.1f} 分钟）")
            return False
        except Exception as exc:
            logger.error(f"知乎 {mode} 执行异常: {exc}")
            return False

    def _load_and_convert_data(
        self,
        patterns: List[str] | None = None,
        time_range_hours: tuple[int, int] | None = None,
        limit: int | None = None,
    ) -> List[EducationHotspot]:
        jsonl_dir = self.trendcrawler_dir / "data" / "zhihu" / "jsonl"
        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []

        selected_patterns = patterns or ["search_contents_*.jsonl"]
        latest_files = []
        for pattern in selected_patterns:
            pattern_files = list(jsonl_dir.glob(pattern))
            if pattern_files:
                latest_files.append(max(pattern_files, key=lambda p: p.stat().st_mtime))

        if not latest_files:
            logger.error(f"未找到知乎 JSONL 文件: {', '.join(selected_patterns)}")
            return []

        hotspots = []
        try:
            for latest_file in latest_files:
                logger.info(f"使用知乎数据文件: {latest_file.name}")
                with open(latest_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            raw_data = json.loads(line)
                            hotspot = self.parse_item(raw_data)
                            if time_range_hours and not self.validate_time_range(
                                hotspot.publish_time,
                                time_range_hours[0],
                                time_range_hours[1],
                            ):
                                continue
                            hotspots.append(hotspot)
                            if limit and len(hotspots) >= limit:
                                break
                        except json.JSONDecodeError as exc:
                            logger.warning(f"{latest_file.name} 第{line_num}行 JSON 解析失败: {exc}")
                    if limit and len(hotspots) >= limit:
                        break
            logger.info(f"成功转换 {len(hotspots)} 条知乎数据")
        except Exception as exc:
            logger.error(f"知乎数据转换失败: {exc}", exc_info=True)

        return hotspots

    def _max_hours(self, time_range_hours: tuple[int, int] | int) -> int:
        if isinstance(time_range_hours, tuple):
            return time_range_hours[1]
        return int(time_range_hours)

    def _normalize_time_range(
        self,
        time_range_hours: tuple[int, int] | int,
    ) -> tuple[int, int]:
        if isinstance(time_range_hours, tuple):
            return time_range_hours
        return (0, int(time_range_hours))
