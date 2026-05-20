from __future__ import annotations

import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Literal

from loguru import logger

from config.app_config import AppConfig, load_app_config
from models.hotspot import EducationHotspot
from web.backend.job_store import JobStore
from web.backend.models import JobSnapshot
from web.backend.progress import count_progress, expected_count_warning


MAX_SOURCE_WORKERS = 4
UnitType = Literal["source", "keyword", "account"]


@dataclass
class JobArtifacts:
    merged_file: str = ""
    scored_file: str = ""
    report_file: str = ""
    candidate_dir: str = ""


@dataclass
class CrawlUnit:
    unit_type: UnitType
    unit_name: str
    keywords: list[str]
    creator_urls: list[str]
    keyword_time_range: tuple[int, int] | None
    account_time_range: tuple[int, int] | None
    max_count: int
    expected_min: int


def _reload_runtime_modules() -> None:
    module_names = [
        "config.settings",
        "crawlers.wechat",
        "crawlers.wechat_mp",
        "crawlers.xiaohongshu",
        "crawlers.zhihu",
        "crawlers.google_news",
        "crawlers.aihot",
        "crawlers.manager",
        "scorers.scorer",
        "formatters.markdown",
        "formatters.material_exporter",
    ]
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
        except Exception as exc:
            logger.warning(f"刷新运行时模块失败 {module_name}: {exc}")


def _source_units(config: AppConfig, source_name: str) -> list[CrawlUnit]:
    if source_name == "wechat":
        item = config.wechat.keyword_search
        return [
            CrawlUnit(
                unit_type="keyword",
                unit_name=keyword,
                keywords=[keyword],
                creator_urls=[],
                keyword_time_range=(item.time_range_hours.min, item.time_range_hours.max),
                account_time_range=None,
                max_count=item.max_results_per_keyword,
                expected_min=item.expected_min_results,
            )
            for keyword in item.keywords
        ]
    if source_name == "wechat_mp":
        item = config.wechat.account_crawl
        return [
            CrawlUnit(
                unit_type="account",
                unit_name=account,
                keywords=[account],
                creator_urls=[],
                keyword_time_range=None,
                account_time_range=(item.time_range_hours.min, item.time_range_hours.max),
                max_count=item.max_results_per_account,
                expected_min=item.expected_min_results,
            )
            for account in item.accounts
        ]
    if source_name == "xiaohongshu":
        keyword_item = config.xiaohongshu.keyword_search
        account_item = config.xiaohongshu.account_crawl
        keyword_units = [
            CrawlUnit(
                unit_type="keyword",
                unit_name=keyword,
                keywords=[keyword],
                creator_urls=[],
                keyword_time_range=(keyword_item.time_range_hours.min, keyword_item.time_range_hours.max),
                account_time_range=None,
                max_count=keyword_item.max_results_per_keyword,
                expected_min=keyword_item.expected_min_results,
            )
            for keyword in keyword_item.keywords
        ]
        account_units = [
            CrawlUnit(
                unit_type="account",
                unit_name=url,
                keywords=[],
                creator_urls=[url],
                keyword_time_range=None,
                account_time_range=(account_item.time_range_hours.min, account_item.time_range_hours.max),
                max_count=account_item.max_results_per_account,
                expected_min=account_item.expected_min_results,
            )
            for url in account_item.creator_urls
        ]
        return keyword_units + account_units
    if source_name == "zhihu":
        keyword_item = config.zhihu.keyword_search
        account_item = config.zhihu.account_crawl
        keyword_units = [
            CrawlUnit(
                unit_type="keyword",
                unit_name=keyword,
                keywords=[keyword],
                creator_urls=[],
                keyword_time_range=(keyword_item.time_range_hours.min, keyword_item.time_range_hours.max),
                account_time_range=None,
                max_count=keyword_item.max_results_per_keyword,
                expected_min=keyword_item.expected_min_results,
            )
            for keyword in keyword_item.keywords
        ]
        account_units = [
            CrawlUnit(
                unit_type="account",
                unit_name=url,
                keywords=[],
                creator_urls=[url],
                keyword_time_range=None,
                account_time_range=(account_item.time_range_hours.min, account_item.time_range_hours.max),
                max_count=account_item.max_results_per_account,
                expected_min=account_item.expected_min_results,
            )
            for url in account_item.creator_urls
        ]
        return keyword_units + account_units
    if source_name == "google_news":
        return [
            CrawlUnit(
                unit_type="keyword",
                unit_name=keyword,
                keywords=[keyword],
                creator_urls=[],
                keyword_time_range=None,
                account_time_range=None,
                max_count=config.google_news.max_results_per_keyword,
                expected_min=config.google_news.expected_min_results,
            )
            for keyword in config.google_news.keywords
        ]
    if source_name == "aihot":
        keywords = config.aihot.keywords or ["精选池"]
        return [
            CrawlUnit(
                unit_type="source",
                unit_name=keyword,
                keywords=[] if keyword == "精选池" else [keyword],
                creator_urls=[],
                keyword_time_range=None,
                account_time_range=None,
                max_count=config.aihot.max_results_per_query,
                expected_min=config.aihot.expected_min_results,
            )
            for keyword in keywords
        ]
    return []


def _source_result_plan(config: AppConfig, source_name: str) -> tuple[int, int]:
    units = _source_units(config, source_name)
    return (
        max(1, sum(unit.max_count for unit in units)),
        sum(unit.expected_min for unit in units),
    )


def _deduplicate(items: list[EducationHotspot]) -> list[EducationHotspot]:
    seen_keys: set[str] = set()
    unique_items: list[EducationHotspot] = []
    for item in items:
        key = item.url or f"{item.source}:{item.title}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_items.append(item)
    return unique_items


def collect_one_unit(source_name: str, unit: CrawlUnit) -> list[EducationHotspot]:
    from crawlers.manager import CrawlerManager

    manager = CrawlerManager(enabled_sources=[source_name])
    return manager.collect_all(
        source_keywords={source_name: unit.keywords},
        source_creator_urls={source_name: unit.creator_urls},
        source_keyword_time_ranges=(
            {source_name: unit.keyword_time_range} if unit.keyword_time_range else None
        ),
        source_account_time_ranges=(
            {source_name: unit.account_time_range} if unit.account_time_range else None
        ),
    )


def run_merge_score_report(
    hotspots: list[EducationHotspot],
    selected_sources: list[str],
    scoring_enabled: bool,
    output_root: Path | None = None,
) -> JobArtifacts:
    if output_root:
        output_root.mkdir(parents=True, exist_ok=True)
    merged_dir = output_root / "merged_data" if output_root else Path("./merged_data")
    scored_dir = output_root / "scored_data" if output_root else Path("./scored_data")
    report_dir = output_root / "output" if output_root else None

    from config import settings
    from formatters.markdown import MarkdownGenerator
    from merger.data_merger import DataMerger

    merged_file = DataMerger(output_dir=str(merged_dir)).merge_sources(
        hotspots,
        source_names=selected_sources,
    )
    if not scoring_enabled:
        return JobArtifacts(merged_file=merged_file)

    from scorers.scorer import ContentScorer

    scorer = ContentScorer()
    scored_hotspots = scorer.score_batch(hotspots)
    scored_file = DataMerger(output_dir=str(scored_dir)).merge_sources(
        scored_hotspots,
        source_names=selected_sources,
    )
    top_hotspots = scorer.select_top_n(scored_hotspots, settings.TOP_N_SELECT_COUNT)
    report_file = MarkdownGenerator(
        output_dir=str(report_dir) if report_dir else None
    ).generate_daily_report(top_hotspots)
    return JobArtifacts(
        merged_file=merged_file,
        scored_file=scored_file,
        report_file=report_file,
    )


def _collect_source_units(
    source_name: str,
    config: AppConfig,
    emit_event: Callable[..., None],
) -> tuple[list[EducationHotspot], list[str]]:
    source_items: list[EducationHotspot] = []
    warnings: list[str] = []
    for unit in _source_units(config, source_name):
        emit_event(
            type="unit_started",
            source=source_name,
            unit_type=unit.unit_type,
            unit_name=unit.unit_name,
            status="running",
            max_count=unit.max_count,
            expected_min_count=unit.expected_min,
            progress=0.05,
            message=f"{source_name} / {unit.unit_name} 开始",
        )
        items = collect_one_unit(source_name, unit)
        warning = expected_count_warning(unit.unit_name, len(items), unit.expected_min)
        if warning:
            warnings.append(warning)
        emit_event(
            type="unit_completed",
            source=source_name,
            unit_type=unit.unit_type,
            unit_name=unit.unit_name,
            status="succeeded",
            current_count=len(items),
            max_count=unit.max_count,
            expected_min_count=unit.expected_min,
            progress=count_progress(len(items), unit.max_count),
            message=f"{source_name} / {unit.unit_name} 完成：{len(items)} 条",
        )
        source_items.extend(items)
    return (_deduplicate(source_items), warnings)


def _collect_sources_serial(
    sources: list[str],
    config: AppConfig,
    emit_event: Callable[..., None],
) -> tuple[list[EducationHotspot], list[str]]:
    all_items: list[EducationHotspot] = []
    warnings: list[str] = []
    for source_name in sources:
        max_count, expected_min = _source_result_plan(config, source_name)
        emit_event(
            type="source_started",
            source=source_name,
            unit_type="source",
            unit_name=source_name,
            status="running",
            max_count=max_count,
            expected_min_count=expected_min,
            progress=0.05,
            message=f"{source_name} 开始采集",
        )
        items, unit_warnings = _collect_source_units(source_name, config, emit_event)
        warnings.extend(unit_warnings)
        warning = expected_count_warning(source_name, len(items), expected_min)
        if warning:
            warnings.append(warning)
        emit_event(
            type="source_completed",
            source=source_name,
            unit_type="source",
            unit_name=source_name,
            status="succeeded",
            current_count=len(items),
            max_count=max_count,
            expected_min_count=expected_min,
            progress=count_progress(len(items), max_count),
            message=f"{source_name} 完成：{len(items)} 条",
        )
        all_items.extend(items)
    return (_deduplicate(all_items), warnings)


def _collect_sources_parallel(
    sources: list[str],
    config: AppConfig,
    emit_event: Callable[..., None],
) -> tuple[list[EducationHotspot], list[str]]:
    all_items: list[EducationHotspot] = []
    warnings: list[str] = []
    worker_count = min(MAX_SOURCE_WORKERS, max(1, len(sources)))
    for source_name in sources:
        max_count, expected_min = _source_result_plan(config, source_name)
        emit_event(
            type="source_started",
            source=source_name,
            unit_type="source",
            unit_name=source_name,
            status="running",
            max_count=max_count,
            expected_min_count=expected_min,
            progress=0.05,
            message=f"{source_name} 开始采集",
        )
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_source = {
            executor.submit(_collect_source_units, source_name, config, emit_event): source_name
            for source_name in sources
        }
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            max_count, expected_min = _source_result_plan(config, source_name)
            try:
                items, unit_warnings = future.result()
                warnings.extend(unit_warnings)
            except Exception as exc:
                warning = f"{source_name} 采集失败：{exc}"
                warnings.append(warning)
                emit_event(
                    type="source_failed",
                    source=source_name,
                    unit_type="source",
                    unit_name=source_name,
                    status="failed",
                    progress=1.0,
                    message=warning,
                )
                continue
            warning = expected_count_warning(source_name, len(items), expected_min)
            if warning:
                warnings.append(warning)
            emit_event(
                type="source_completed",
                source=source_name,
                unit_type="source",
                unit_name=source_name,
                status="succeeded",
                current_count=len(items),
                max_count=max_count,
                expected_min_count=expected_min,
                progress=count_progress(len(items), max_count),
                message=f"{source_name} 完成：{len(items)} 条",
            )
            all_items.extend(items)
    return (_deduplicate(all_items), warnings)


def run_web_job(
    store: JobStore,
    snapshot: JobSnapshot,
    config_path: Path = Path("config.yaml"),
) -> JobSnapshot:
    snapshot = store.update_job(snapshot, status="running")

    def emit_event(**event_fields) -> None:
        store.append_event(snapshot.job_id, **event_fields)

    try:
        _reload_runtime_modules()
        config = load_app_config(config_path)
        selected_sources = list(config.enabled_sources)
        emit_event(
            type="job_started",
            unit_type="stage",
            unit_name="job",
            status="running",
            progress=0.01,
            message=f"任务启动：{', '.join(selected_sources)}",
        )
        if snapshot.execution_mode == "parallel":
            hotspots, warnings = _collect_sources_parallel(selected_sources, config, emit_event)
        else:
            hotspots, warnings = _collect_sources_serial(selected_sources, config, emit_event)
        if not hotspots:
            raise RuntimeError("所有来源均未采集到内容")

        emit_event(
            type="stage_started",
            unit_type="stage",
            unit_name="merge_score_report",
            status="running",
            current_count=len(hotspots),
            progress=0.75,
            message=f"采集合并前去重后 {len(hotspots)} 条",
        )
        scoring_enabled = (
            snapshot.run_mode == "collect_score_report" and config.scoring.enabled
        )
        artifacts = run_merge_score_report(
            hotspots=hotspots,
            selected_sources=selected_sources,
            scoring_enabled=scoring_enabled,
            output_root=store.job_dir(snapshot.job_id),
        )
        store.save_artifacts(snapshot.job_id, asdict(artifacts))
        emit_event(
            type="job_completed",
            unit_type="stage",
            unit_name="job",
            status="succeeded",
            progress=1.0,
            message="任务完成",
        )
        return store.update_job(
            store.load_job(snapshot.job_id),
            status="succeeded",
            artifacts=asdict(artifacts),
            warnings=warnings,
        )
    except Exception as exc:
        message = str(exc)
        emit_event(
            type="job_failed",
            unit_type="stage",
            unit_name="job",
            status="failed",
            progress=1.0,
            message=message,
        )
        return store.update_job(
            store.load_job(snapshot.job_id),
            status="failed",
            errors=[message],
        )
