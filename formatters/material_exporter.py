"""Generic material package exporter for downstream content generation."""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import re
import shutil
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from loguru import logger

from config.settings import (
    MATERIAL_CONTENT_MAX_CHARS,
    MATERIAL_EXPORT_DIR,
    MATERIAL_TIMEZONE,
)
from models.hotspot import EducationHotspot


SCORE_DIMENSIONS = (
    "heat",
    "authority",
    "quality",
    "resonance",
    "timeliness",
    "reference_value",
    "risk_control",
)


class MaterialExporter:
    """Export selected hotspots as a stable material package."""

    def __init__(self, output_root: str = MATERIAL_EXPORT_DIR):
        self.output_root = Path(output_root)

    def export(
        self,
        hotspots: Iterable[EducationHotspot],
        material_date: date | None = None,
        source_names: list[str] | None = None,
    ) -> Path:
        items = list(hotspots)
        if not items:
            raise ValueError("没有可导出的素材内容")

        target_date = material_date or _today_in_material_timezone()
        date_label = target_date.strftime("%Y-%m-%d")
        output_dir = self.output_root / date_label
        candidates_dir = output_dir / "candidates"
        if candidates_dir.exists():
            shutil.rmtree(candidates_dir)
        candidates_dir.mkdir(parents=True, exist_ok=True)

        manifest_items: list[dict] = []
        for index, hotspot in enumerate(items, start=1):
            md_name = f"{index:03d}.md"
            json_name = f"{index:03d}.json"
            md_path = candidates_dir / md_name
            json_path = candidates_dir / json_name
            md_path.write_text(
                self._build_candidate_markdown(index, hotspot),
                encoding="utf-8",
            )
            metadata = self._build_metadata(index, hotspot, md_name, json_name)
            json_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_items.append(metadata)

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "date": date_label,
                    "generated_at": _now_in_material_timezone().isoformat(),
                    "count": len(items),
                    "source_names": source_names or [],
                    "content_max_chars": MATERIAL_CONTENT_MAX_CHARS,
                    "items": manifest_items,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        logger.info(f"素材包已生成: {output_dir} ({len(items)} 篇)")
        return output_dir

    def _build_candidate_markdown(self, index: int, hotspot: EducationHotspot) -> str:
        title = _compact_line(hotspot.title, 120) or f"候选素材 {index}"
        account = _single_line(hotspot.author or hotspot.source or "")
        source = _single_line(hotspot.source)
        published_at = hotspot.publish_time.strftime("%Y-%m-%d %H:%M")
        url = _single_line(hotspot.url)
        score_front_matter = _build_score_front_matter_lines(hotspot)
        score_markdown = _build_score_markdown_lines(hotspot)
        content = _truncate_text(
            str(hotspot.content or "").strip(),
            MATERIAL_CONTENT_MAX_CHARS,
        )

        sections = [
            "---",
            f"title: {_yaml_value(title)}",
            f"account: {_yaml_value(account)}",
            f"source: {_yaml_value(source)}",
            f"published_at: {_yaml_value(published_at)}",
            f"url: {_yaml_value(url)}",
            *score_front_matter,
            "---",
            "",
            f"# {title}",
            "",
            *score_markdown,
            "## 正文",
            "",
            content or title,
            "",
        ]
        return "\n".join(sections)

    def _build_metadata(
        self,
        index: int,
        hotspot: EducationHotspot,
        md_name: str,
        json_name: str,
    ) -> dict:
        item = {
            "rank": index,
            "file": f"candidates/{md_name}",
            "metadata_file": f"candidates/{json_name}",
            "title": _compact_line(hotspot.title, 120),
            "account": _single_line(hotspot.author or hotspot.source or ""),
            "source": _single_line(hotspot.source),
            "published_at": hotspot.publish_time.strftime("%Y-%m-%d %H:%M"),
            "url": _single_line(hotspot.url),
        }
        score_payload = _build_score_manifest_payload(hotspot)
        if score_payload:
            item.update(score_payload)
        return item


def _single_line(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _compact_line(value: str, max_chars: int) -> str:
    text = _single_line(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _truncate_text(value: str, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def _yaml_value(value: str) -> str:
    escaped = str(value or "").replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _build_score_front_matter_lines(hotspot: EducationHotspot) -> list[str]:
    score = _numeric_value(hotspot.score)
    score_details = hotspot.score_details if isinstance(hotspot.score_details, dict) else {}
    if score is None and not score_details:
        return []

    lines: list[str] = []
    if score is not None:
        lines.append(f"score: {_format_number(score)}")
    for dimension in SCORE_DIMENSIONS:
        value = _numeric_value(score_details.get(dimension))
        if value is not None:
            lines.append(f"{dimension}: {_format_number(value)}")
    return lines


def _build_score_markdown_lines(hotspot: EducationHotspot) -> list[str]:
    score = _numeric_value(hotspot.score)
    score_details = hotspot.score_details if isinstance(hotspot.score_details, dict) else {}
    if score is None and not score_details:
        return []

    lines = ["## AITrend 评分", ""]
    if score is not None:
        lines.append(f"- 综合分：{_format_number(score)}")
    for dimension in SCORE_DIMENSIONS:
        value = _numeric_value(score_details.get(dimension))
        if value is not None:
            lines.append(f"- {dimension}：{_format_number(value)}")

    reason = _single_line(score_details.get("reason", ""))
    best_angle = _single_line(score_details.get("best_angle", ""))
    if reason:
        lines.append(f"- reason：{reason}")
    if best_angle:
        lines.append(f"- best_angle：{best_angle}")
    lines.append("")
    return lines


def _build_score_manifest_payload(hotspot: EducationHotspot) -> dict:
    score = _numeric_value(hotspot.score)
    score_details = hotspot.score_details if isinstance(hotspot.score_details, dict) else {}
    if score is None and not score_details:
        return {}

    payload: dict = {}
    if score is not None:
        payload["score"] = score
    detail_payload = {
        dimension: value
        for dimension in SCORE_DIMENSIONS
        if (value := _numeric_value(score_details.get(dimension))) is not None
    }
    for text_key in ("reason", "best_angle"):
        text = _single_line(score_details.get(text_key, ""))
        if text:
            detail_payload[text_key] = text
    if detail_payload:
        payload["score_details"] = detail_payload
    return payload


def _numeric_value(value) -> float | None:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _format_number(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _today_in_material_timezone() -> date:
    return _now_in_material_timezone().date()


def _now_in_material_timezone() -> datetime:
    try:
        return datetime.now(ZoneInfo(MATERIAL_TIMEZONE))
    except ZoneInfoNotFoundError:
        logger.warning(f"未知时区 {MATERIAL_TIMEZONE}，使用本机当前日期")
        return datetime.now()
