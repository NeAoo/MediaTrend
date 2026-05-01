"""Shared entrypoint for single-source search scripts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

from config.settings import get_source_keywords
from crawlers.manager import AVAILABLE_SOURCES, CrawlerManager
from main import parse_keywords_arg, setup_logger
from merger.data_merger import DataMerger


def run_single_source_search(source_name: str, argv: list[str] | None = None) -> int:
    """Run one configured source and write a merged JSON result."""
    parser = argparse.ArgumentParser(description=f"{source_name} 单源搜索脚本")
    if source_name == "wechat_mp":
        parser.add_argument(
            "-a",
            "--accounts",
            dest="keywords",
            help="本次运行覆盖要采集的公众号名称，逗号分隔；不填则使用 WECHAT_MP_ACCOUNTS",
        )
    else:
        parser.add_argument(
            "-k",
            "--keywords",
            help="本次运行覆盖该搜索源的关键词，逗号分隔；不填则使用 .env / settings 配置",
        )
    args = parser.parse_args(argv)

    if source_name not in AVAILABLE_SOURCES:
        parser.error(f"未知搜索源: {source_name}")

    setup_logger()
    keyword_override = parse_keywords_arg(args.keywords)
    keywords = keyword_override or get_source_keywords(source_name)

    logger.info("=" * 60)
    logger.info(f"{source_name} 单源搜索任务启动")
    logger.info("=" * 60)
    logger.info(f"搜索关键词: {', '.join(keywords)}")

    manager = CrawlerManager(enabled_sources=[source_name])
    hotspots = manager.collect_all(source_keywords={source_name: keywords})
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
