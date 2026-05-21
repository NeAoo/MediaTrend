"""
小红书内容采集器
集成 TrendCrawlerRuntime 的 Pipeline 到统一的采集框架。
"""

import json
import os
import re
import signal
import subprocess
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import requests
from loguru import logger

from config.settings import (
    TREND_CRAWLER_RUNTIME_DIR,
    TREND_CRAWLER_RUNTIME_LOGIN_TYPE,
    TREND_CRAWLER_RUNTIME_PYTHON_BIN,
    TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS,
    XIAOHONGSHU_COOKIE,
    XIAOHONGSHU_ACCOUNT_TIME_RANGE_HOURS,
    XIAOHONGSHU_CREATOR_URLS,
    XIAOHONGSHU_KEYWORD_TIME_RANGE_HOURS,
    XIAOHONGSHU_LOGIN_TYPE,
    XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT,
    XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
)
from crawlers.base import BaseCrawler, resolve_query_lookback_hours
from models.hotspot import CollectionResult, EducationHotspot


SHORT_LINK_DOMAINS = ("xhslink.com", "xhsurl.com")
SHARE_URL_PATTERN = re.compile(r"https?://[^\s<>'\"，。；、]+")
TRAILING_URL_PUNCTUATION = ".,，。；;、）)]}>》\"'"
SHORT_LINK_TIMEOUT_SECONDS = 15


class XiaohongshuCrawler(BaseCrawler):
    """小红书采集器。"""

    def __init__(self):
        super().__init__("xiaohongshu")
        self.trendcrawler_dir = TREND_CRAWLER_RUNTIME_DIR
        self.python_bin = TREND_CRAWLER_RUNTIME_PYTHON_BIN

    def collect(
        self,
        keywords: List[str] | None = None,
        time_range_hours: tuple | None = None,
        creator_urls: List[str] | None = None,
        creator_time_range_hours: tuple | None = None,
        runtime_timeout_seconds: int | None = None,
    ) -> CollectionResult:
        selected_keywords = keywords or []
        selected_creator_urls = (
            XIAOHONGSHU_CREATOR_URLS if creator_urls is None else creator_urls
        )
        selected_creator_urls = self._normalize_creator_urls(selected_creator_urls)
        if not selected_keywords and not selected_creator_urls:
            logger.warning("未配置小红书关键词或账号 URL，无法采集")
            return CollectionResult()

        result = CollectionResult()
        keyword_time_range = self._normalize_time_range(
            time_range_hours or XIAOHONGSHU_KEYWORD_TIME_RANGE_HOURS
        )
        account_time_range = self._normalize_time_range(
            creator_time_range_hours
            or time_range_hours
            or XIAOHONGSHU_ACCOUNT_TIME_RANGE_HOURS
        )
        keyword_max_hours = self._max_hours(keyword_time_range)
        account_max_hours = self._max_hours(account_time_range)
        runtime_timeout = runtime_timeout_seconds or TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS
        hotspots: list[EducationHotspot] = []

        logger.info("开始从小红书采集教育热点...")
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
                    max_count=XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
                    time_range_hours=keyword_max_hours,
                    timeout=runtime_timeout,
                )
                if success:
                    hotspots.extend(
                        self._load_and_convert_data(
                            ["search_contents_*.jsonl"],
                            time_range_hours=keyword_time_range,
                            limit=XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD
                            * len(selected_keywords),
                        )
                    )
                else:
                    result.error_messages.append("小红书关键词搜索执行失败或超时")

            if selected_creator_urls:
                success = self._run_trendcrawler(
                    mode="creator",
                    items=selected_creator_urls,
                    max_count=XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT,
                    time_range_hours=account_max_hours,
                    timeout=runtime_timeout,
                )
                if success:
                    hotspots.extend(
                        self._load_and_convert_data(
                            ["creator_contents_*.jsonl"],
                            time_range_hours=account_time_range,
                            limit=XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT
                            * len(selected_creator_urls),
                        )
                    )
                else:
                    result.error_messages.append("小红书账号采集执行失败或超时")

            result.items = hotspots
            result.success_count = len(hotspots)
            logger.info(f"小红书采集完成，共 {len(hotspots)} 条内容")
        except Exception as exc:
            logger.error(f"小红书采集异常: {exc}", exc_info=True)
            result.error_messages.append(str(exc))

        return result

    def _normalize_creator_urls(self, creator_urls: List[str]) -> List[str]:
        """Accept raw share text, short links, profile URLs, or pure user IDs."""
        normalized_urls: list[str] = []
        seen_urls: set[str] = set()
        for raw_value in creator_urls:
            candidates = self._extract_creator_url_candidates(raw_value)
            for candidate_url in candidates:
                final_url = self._expand_short_creator_url(candidate_url)
                if final_url not in seen_urls:
                    normalized_urls.append(final_url)
                    seen_urls.add(final_url)
        return normalized_urls

    def _extract_creator_url_candidates(self, raw_value: str) -> list[str]:
        stripped_value = raw_value.strip()
        if not stripped_value:
            return []
        matched_urls = [
            match.group(0).rstrip(TRAILING_URL_PUNCTUATION)
            for match in SHARE_URL_PATTERN.finditer(stripped_value)
        ]
        if matched_urls:
            return matched_urls
        is_pure_user_id = len(stripped_value) == 24 and all(
            char in "0123456789abcdef" for char in stripped_value
        )
        if is_pure_user_id:
            return [stripped_value]
        logger.warning(f"无法从小红书账号输入中提取 URL 或 user_id: {raw_value}")
        return []

    def _expand_short_creator_url(self, candidate_url: str) -> str:
        parsed_url = urlparse(candidate_url)
        host = parsed_url.netloc.lower()
        if not any(host == domain or host.endswith(f".{domain}") for domain in SHORT_LINK_DOMAINS):
            return candidate_url

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            )
        }
        try:
            response = requests.get(
                candidate_url,
                allow_redirects=True,
                timeout=SHORT_LINK_TIMEOUT_SECONDS,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"小红书短链已展开: {candidate_url} -> {response.url}")
            return response.url
        except requests.RequestException as exc:
            logger.warning(
                f"小红书短链展开失败，保留原始 URL: {candidate_url}, error={exc}"
            )
            return candidate_url

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

        login_type = XIAOHONGSHU_LOGIN_TYPE or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
        if login_type == "cookie" and not XIAOHONGSHU_COOKIE:
            logger.error("xiaohongshu.login_type=cookie 但未配置 XIAOHONGSHU_COOKIE")
            return False

        try:
            env = os.environ.copy()
            env["TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX"] = str(time_range_hours)
            env["TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT"] = str(max_count)

            cmd = [
                self.python_bin,
                "main.py",
                "--platform",
                "xhs",
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
                logger.error(f"未知小红书采集模式: {mode}")
                return False

            if login_type == "cookie" and XIAOHONGSHU_COOKIE:
                cmd.extend(["--cookies", XIAOHONGSHU_COOKIE])

            logger.info(f"小红书 {mode} 输入数量: {len(items)}")
            logger.info(f"时间范围: {time_range_hours} 小时")
            logger.info(f"采集数量上限: {max_count}")
            logger.info(f"执行 TrendCrawlerRuntime 小红书 {mode}: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                cwd=self.trendcrawler_dir,
                env=env,
                start_new_session=(os.name != "nt"),
                text=True,
            )
            return_code = process.wait(timeout=timeout)
            if return_code != 0:
                logger.error(f"TrendCrawlerRuntime 返回非 0 退出码: {return_code}")
            return return_code == 0
        except subprocess.TimeoutExpired:
            self._terminate_process_tree(process)
            logger.error(f"小红书 {mode} 执行超时（{timeout / 60:.1f} 分钟）")
            return False
        except Exception as exc:
            logger.error(f"小红书 {mode} 执行异常: {exc}")
            return False

    def _terminate_process_tree(self, process: subprocess.Popen) -> None:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        except ProcessLookupError:
            return

    def _load_and_convert_data(
        self,
        patterns: List[str] | None = None,
        time_range_hours: tuple[int, int] | None = None,
        limit: int | None = None,
    ) -> List[EducationHotspot]:
        jsonl_dir = self.trendcrawler_dir / "data" / "xhs" / "jsonl"
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
            logger.error(f"未找到小红书 JSONL 文件: {', '.join(selected_patterns)}")
            return []

        hotspots = []
        try:
            for latest_file in latest_files:
                logger.info(f"使用小红书数据文件: {latest_file.name}")
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
            logger.info(f"成功转换 {len(hotspots)} 条小红书数据")
        except Exception as exc:
            logger.error(f"小红书数据转换失败: {exc}", exc_info=True)

        return hotspots

    def _max_hours(self, time_range_hours: tuple[int, int] | int) -> int:
        if isinstance(time_range_hours, tuple):
            return resolve_query_lookback_hours(
                datetime.now(),
                time_range_hours[0],
                time_range_hours[1],
            )
        return int(time_range_hours)

    def _normalize_time_range(
        self,
        time_range_hours: tuple[int, int] | int,
    ) -> tuple[int, int]:
        if isinstance(time_range_hours, tuple):
            return time_range_hours
        return (0, int(time_range_hours))
