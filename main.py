"""
教育热点搜集 Agent - 主入口
支持单次执行、只搜索和定时调度三种模式。
"""

import argparse
import random

from loguru import logger

from config.settings import (
    ENABLED_SOURCES,
    LLM_API_KEY,
    LOG_COMPRESSION,
    LOG_FILE,
    LOG_LEVEL,
    LOG_RETENTION,
    LOG_ROTATION,
    MATERIAL_EXPORT_ENABLED,
    SCORING_ENABLED,
    SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES,
    SCHEDULE_TIME,
    TOP_N_SELECT_COUNT,
)
from crawlers.manager import AVAILABLE_SOURCES, CrawlerManager
from formatters.material_exporter import MaterialExporter
from formatters.markdown import MarkdownGenerator
from merger.data_merger import DataMerger
from scorers.scorer import ContentScorer


def setup_logger() -> None:
    """配置日志输出。"""
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | <level>{message}</level>"
        ),
        colorize=True,
    )
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression=LOG_COMPRESSION,
        encoding="utf-8",
    )


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_sources_arg(raw_sources: str | None) -> list[str]:
    """Parse CLI source list while preserving execution order."""
    if not raw_sources:
        return ENABLED_SOURCES

    sources = _split_csv(raw_sources)
    if len(sources) == 1 and sources[0].lower() == "all":
        return [source for source in AVAILABLE_SOURCES if source != "demo"]

    invalid_sources = [source for source in sources if source not in AVAILABLE_SOURCES]
    if invalid_sources:
        raise ValueError(
            "未知搜索源: "
            f"{', '.join(invalid_sources)}；可选值: {', '.join(AVAILABLE_SOURCES)}"
        )
    return sources


def parse_keywords_arg(raw_keywords: str | None) -> list[str] | None:
    keywords = _split_csv(raw_keywords)
    return keywords or None


def _source_keywords_override(
    sources: list[str],
    keyword_override: list[str] | None,
) -> dict[str, list[str]] | None:
    if keyword_override is None:
        return None
    return {source: keyword_override for source in sources}


def _is_scoring_failed(hotspot) -> bool:
    details = getattr(hotspot, "score_details", None)
    return isinstance(details, dict) and details.get("scoring_failed") is True


def _select_random_fallback(hotspots: list, n: int) -> list:
    if n <= 0:
        return []
    items = list(hotspots)
    random.shuffle(items)
    selected = items[: min(n, len(items))]
    logger.warning(f"AI 打分整体不可用，随机选取 {len(selected)} 条候选继续上传")
    return selected


def run_collection_task(
    sources: list[str] | None = None,
    keyword_override: list[str] | None = None,
    scoring_enabled: bool | None = None,
) -> bool:
    """执行一次完整的采集、打分和报告生成。"""
    logger.info("=" * 60)
    logger.info("教育热点搜集 Agent 启动")
    logger.info("=" * 60)

    should_score = SCORING_ENABLED if scoring_enabled is None else scoring_enabled
    if should_score and not LLM_API_KEY:
        logger.error("未配置 LLM_API_KEY，无法执行完整打分流程")
        logger.error("请先填写 .env 中的 LLM_API_KEY，或在 config.yaml 关闭 scoring.enabled")
        return False

    try:
        selected_sources = sources or ENABLED_SOURCES
        source_keywords = _source_keywords_override(selected_sources, keyword_override)
        logger.info("\n第一步：开始采集教育热点...")
        logger.info(f"启用搜索源: {', '.join(selected_sources)}")
        if keyword_override:
            logger.info(f"命令行覆盖关键词: {', '.join(keyword_override)}")
        crawler_manager = CrawlerManager(enabled_sources=selected_sources)
        hotspots = crawler_manager.collect_all(source_keywords=source_keywords)
        logger.info(f"采集完成，共获取 {len(hotspots)} 条热点内容")

        if not hotspots:
            logger.error("未采集到任何内容，程序退出")
            return False

        logger.info("\n采集内容预览（前5条）:")
        for i, hotspot in enumerate(hotspots[:5], 1):
            logger.info(f"  {i}. [{hotspot.source}] {hotspot.title[:50]}")

        logger.info("\n第二步：合并多源数据为统一 JSON 文件...")
        merger = DataMerger()

        merged_file = merger.merge_sources(hotspots, source_names=selected_sources)
        if not merged_file:
            logger.error("数据合并失败")
            return False
        logger.info(f"合并文件已生成: {merged_file}")

        if not should_score:
            logger.info("\n第三步：config.yaml 已关闭智能打分，本次只采集并合并数据")
            logger.info("\n" + "=" * 60)
            logger.info("教育热点搜集任务完成（未打分）")
            logger.info("=" * 60)
            logger.info("\n今日成果:")
            logger.info(f"   - 采集内容: {len(hotspots)} 条")
            logger.info(f"   - 合并文件: {merged_file}")
            logger.info(f"   - 日志文件: {LOG_FILE}")
            return True

        logger.info("\n第三步：开始对内容进行智能打分...")
        scorer = ContentScorer()
        scored_hotspots = scorer.score_batch(hotspots)
        failed_scores = [hotspot for hotspot in scored_hotspots if _is_scoring_failed(hotspot)]
        if failed_scores:
            logger.warning(f"打分异常内容: {len(failed_scores)}/{len(scored_hotspots)} 条")
        use_random_fallback = (
            scored_hotspots
            and len(failed_scores) == len(scored_hotspots)
            and SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES
        )
        logger.info("打分完成，所有内容已评分")

        logger.info("\n评分概览（前5条）:")
        for i, hotspot in enumerate(scored_hotspots[:5], 1):
            logger.info(f"  {i}. 评分: {hotspot.score:.2f} | {hotspot.title[:40]}")

        logger.info("\n第四步：保存打分后的数据到 scored_data...")
        scored_merger = DataMerger(output_dir="./scored_data")
        scored_file = scored_merger.merge_sources(
            scored_hotspots,
            source_names=selected_sources,
        )
        if scored_file:
            logger.info(f"打分数据已保存: {scored_file}")
        else:
            logger.warning("打分数据保存失败")

        logger.info(f"\n第五步：筛选至少前 {TOP_N_SELECT_COUNT} 条高分内容，同分并列保留...")
        if use_random_fallback:
            top_hotspots = _select_random_fallback(scored_hotspots, TOP_N_SELECT_COUNT)
        else:
            top_hotspots = scorer.select_top_n(scored_hotspots, TOP_N_SELECT_COUNT)
        logger.info(f"筛选完成，最终选取 {len(top_hotspots)} 条优质内容")

        logger.info("\n最终入选热点（按评分排序）:")
        for i, hotspot in enumerate(top_hotspots, 1):
            logger.info(f"  {i}. {hotspot.score:.1f}分 | {hotspot.title[:50]}")

        logger.info("\n第六步：生成 Markdown 日报...")
        generator = MarkdownGenerator()
        output_file = generator.generate_daily_report(top_hotspots)
        logger.info(f"日报生成成功，文件位置: {output_file}")

        material_dir = ""
        if MATERIAL_EXPORT_ENABLED:
            logger.info("\n第七步：生成通用素材包...")
            material_dir = str(
                MaterialExporter().export(
                    top_hotspots,
                    source_names=selected_sources,
                )
            )
            logger.info(f"素材包目录: {material_dir}")

        logger.info("\n" + "=" * 60)
        logger.info("教育热点搜集任务全部完成")
        logger.info("=" * 60)
        logger.info("\n今日成果:")
        logger.info(f"   - 采集内容: {len(hotspots)} 条")
        logger.info(f"   - 合并文件: {merged_file}")
        logger.info(f"   - 打分数据: {scored_file}")
        logger.info(f"   - 最终入选: {len(top_hotspots)} 条")
        logger.info(f"   - 输出文件: {output_file}")
        if material_dir:
            logger.info(f"   - 素材包: {material_dir}")
        logger.info(f"   - 最高评分: {top_hotspots[0].score:.2f}")
        logger.info(f"   - 日志文件: {LOG_FILE}")
        return True
    except Exception as exc:
        logger.error(f"程序执行出错: {exc}", exc_info=True)
        return False


def run_search_task(
    sources: list[str] | None = None,
    keyword_override: list[str] | None = None,
) -> bool:
    """只执行搜索采集和合并输出，不做打分。"""
    logger.info("=" * 60)
    logger.info("教育热点搜索任务启动")
    logger.info("=" * 60)

    try:
        selected_sources = sources or ENABLED_SOURCES
        source_keywords = _source_keywords_override(selected_sources, keyword_override)
        logger.info(f"启用搜索源: {', '.join(selected_sources)}")
        if keyword_override:
            logger.info(f"命令行覆盖关键词: {', '.join(keyword_override)}")
        crawler_manager = CrawlerManager(enabled_sources=selected_sources)
        hotspots = crawler_manager.collect_all(source_keywords=source_keywords)
        logger.info(f"搜索完成，共获取 {len(hotspots)} 条热点内容")

        if not hotspots:
            logger.error("未采集到任何内容")
            return False

        logger.info("\n搜索结果预览（前10条）:")
        for i, hotspot in enumerate(hotspots[:10], 1):
            logger.info(
                f"  {i}. [{hotspot.source}] "
                f"{hotspot.publish_time:%Y-%m-%d %H:%M} | "
                f"{hotspot.title[:60]}"
            )
        merger = DataMerger()
        merged_file = merger.merge_sources(hotspots, source_names=selected_sources)
        if not merged_file:
            logger.error("搜索结果保存失败")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("教育热点搜索任务完成")
        logger.info("=" * 60)
        logger.info(f"   - 搜索内容: {len(hotspots)} 条")
        logger.info(f"   - 输出文件: {merged_file}")
        logger.info(f"   - 日志文件: {LOG_FILE}")
        return True
    except Exception as exc:
        logger.error(f"搜索任务执行出错: {exc}", exc_info=True)
        return False


def start_scheduler(
    sources: list[str] | None = None,
    keyword_override: list[str] | None = None,
) -> None:
    """启动定时任务调度器。"""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    setup_logger()
    logger.info("=" * 60)
    logger.info("教育热点搜集 Agent - 定时调度模式")
    logger.info("=" * 60)

    hour, minute = 8, 0
    if ":" in SCHEDULE_TIME:
        hour, minute = map(int, SCHEDULE_TIME.split(":"))

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_collection_task,
        kwargs={
            "sources": sources or ENABLED_SOURCES,
            "keyword_override": keyword_override,
            "scoring_enabled": None,
        },
        trigger=CronTrigger(hour=hour, minute=minute),
        id="daily_education_hotspot",
        name="每日教育热点采集",
        replace_existing=True,
    )

    logger.info(f"已添加每日定时任务: 每天 {hour:02d}:{minute:02d} 执行")
    logger.info("提示: 按 Ctrl+C 停止调度器\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("\n调度器被用户中断")
        scheduler.shutdown(wait=False)
        logger.info("调度器已关闭")


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="教育热点搜集 Agent")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["search", "run", "start"],
        help="执行命令: search(只搜索), run(完整执行), start(定时调度)",
    )
    parser.add_argument(
        "-s",
        "--sources",
        help=(
            "本次运行启用的搜索源，逗号分隔；"
            "例如 wechat,xiaohongshu,zhihu，或 all"
        ),
    )
    parser.add_argument(
        "-k",
        "--keywords",
        help="本次运行覆盖所有搜索源的关键词，逗号分隔；不填则使用各来源配置",
    )
    args = parser.parse_args()

    try:
        selected_sources = parse_sources_arg(args.sources)
        keyword_override = parse_keywords_arg(args.keywords)
    except ValueError as exc:
        parser.error(str(exc))

    if args.command == "search":
        setup_logger()
        success = run_search_task(
            sources=selected_sources,
            keyword_override=keyword_override,
        )
    elif args.command == "run":
        setup_logger()
        success = run_collection_task(
            sources=selected_sources,
            keyword_override=keyword_override,
        )
    else:
        start_scheduler(
            sources=selected_sources,
            keyword_override=keyword_override,
        )
        return

    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
