"""Shared entrypoint for single-source search scripts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

from config.settings import get_source_creator_urls, get_source_keywords
from crawlers.manager import AVAILABLE_SOURCES, CrawlerManager
from main import parse_keywords_arg, setup_logger
from merger.data_merger import DataMerger

CREATOR_SOURCE_NAMES = {"xiaohongshu", "zhihu"}
CREATOR_MODE_CHOICES = ("both", "keywords", "accounts")


def run_single_source_search(
    source_name: str,
    argv: list[str] | None = None,
    default_mode: str = "both",
) -> int:
    """Run one configured source and write a merged JSON result."""
    if default_mode not in CREATOR_MODE_CHOICES:
        raise ValueError(f"未知账号采集模式: {default_mode}")

    parser = argparse.ArgumentParser(description=f"{source_name} 单源搜索脚本")
    if source_name == "wechat_mp":
        parser.add_argument(
            "-a",
            "--accounts",
            dest="keywords",
            help="本次运行覆盖要采集的公众号名称，逗号分隔；不填则使用 config.yaml 的 wechat.account_crawl.accounts",
        )
    else:
        parser.add_argument(
            "-k",
            "--keywords",
            help="本次运行覆盖该搜索源的关键词，逗号分隔；不填则使用 config.yaml 配置",
        )
        if source_name in CREATOR_SOURCE_NAMES:
            parser.add_argument(
                "-c",
                "--creator-urls",
                help="本次运行覆盖要采集的账号主页 URL，逗号分隔；不填则使用 config.yaml 的 account_crawl.creator_urls",
            )
            parser.add_argument(
                "--mode",
                choices=CREATOR_MODE_CHOICES,
                default=default_mode,
                help="采集模式：both=关键词+账号，keywords=只搜关键词，accounts=只抓账号",
            )
    args = parser.parse_args(argv)

    if source_name not in AVAILABLE_SOURCES:
        parser.error(f"未知搜索源: {source_name}")

    setup_logger()
    keyword_override = parse_keywords_arg(args.keywords)
    keywords = keyword_override or get_source_keywords(source_name)
    creator_urls = []
    if source_name in CREATOR_SOURCE_NAMES:
        creator_override = parse_keywords_arg(args.creator_urls)
        creator_urls = (
            creator_override
            if creator_override is not None
            else get_source_creator_urls(source_name)
        )
        if args.mode == "keywords":
            creator_urls = []
        elif args.mode == "accounts":
            keywords = []

    logger.info("=" * 60)
    logger.info(f"{source_name} 单源搜索任务启动")
    logger.info("=" * 60)
    logger.info(f"搜索关键词: {', '.join(keywords)}")
    if source_name in CREATOR_SOURCE_NAMES:
        logger.info(f"账号 URL 数量: {len(creator_urls)}")
        logger.info(f"采集模式: {args.mode}")

    manager = CrawlerManager(enabled_sources=[source_name])
    hotspots = manager.collect_all(
        source_keywords={source_name: keywords},
        source_creator_urls={source_name: creator_urls}
        if source_name in CREATOR_SOURCE_NAMES
        else None,
    )
    if not hotspots:
        logger.error(f"{source_name} 未采集到任何内容")
        return 1

    merger = DataMerger()
    merged_file = merger.merge_sources(hotspots, source_names=[source_name])
    if not merged_file:
        logger.error(f"{source_name} 搜索结果保存失败")
        return 1

    logger.info(f"{source_name} 单源搜索完成，共 {len(hotspots)} 条")
    logger.info(f"输出文件: {merged_file}")
    return 0
