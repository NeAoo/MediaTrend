"""
longxia 人工候选 Markdown 导出器。

longxia 侧约定：一个 md 文件代表一篇候选，文件名必须以日期开头。
"""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import re
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from loguru import logger

from config.settings import (
    LONGXIA_CANDIDATE_CONTENT_MAX_CHARS,
    LONGXIA_CANDIDATE_EXPORT_DIR,
    LONGXIA_CANDIDATE_TIMEZONE,
)
from models.hotspot import EducationHotspot


class LongxiaCandidateExporter:
    """将已筛选热点导出为 longxia 可读取的候选 md 文件。"""

    def __init__(self, output_root: str = LONGXIA_CANDIDATE_EXPORT_DIR):
        self.output_root = Path(output_root)

    def export(
        self,
        hotspots: Iterable[EducationHotspot],
        candidate_date: date | None = None,
    ) -> Path:
        """导出候选文件，并返回当天候选目录。"""
        items = list(hotspots)
        if not items:
            raise ValueError("没有可导出的 longxia 候选内容")

        target_date = candidate_date or _today_in_longxia_timezone()
        date_label = target_date.strftime("%Y-%m-%d")
        output_dir = self.output_root / date_label
        output_dir.mkdir(parents=True, exist_ok=True)

        for old_file in output_dir.glob(f"{date_label}_*.md"):
            old_file.unlink()

        for index, hotspot in enumerate(items, start=1):
            file_path = output_dir / f"{date_label}_{index:02d}.md"
            file_path.write_text(
                self._build_candidate_markdown(index, hotspot),
                encoding="utf-8",
            )

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "date": date_label,
                    "count": len(items),
                    "content_max_chars": LONGXIA_CANDIDATE_CONTENT_MAX_CHARS,
                    "items": [
                        self._build_manifest_item(index, hotspot, date_label)
                        for index, hotspot in enumerate(items, start=1)
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(f"longxia 候选 md 已生成: {output_dir} ({len(items)} 篇)")
        return output_dir

    def _build_candidate_markdown(self, index: int, hotspot: EducationHotspot) -> str:
        title = _compact_line(hotspot.title, 120) or f"候选文章 {index}"
        account = _single_line(hotspot.author or hotspot.source or "")
        source = _single_line(hotspot.source)
        published_at = hotspot.publish_time.strftime("%Y-%m-%d %H:%M")
        url = _single_line(hotspot.url)
        content = _truncate_text(
            str(hotspot.content or "").strip(),
            LONGXIA_CANDIDATE_CONTENT_MAX_CHARS,
        )

        sections = [
            "---",
            f"title: {_yaml_value(title)}",
            f"account: {_yaml_value(account)}",
            f"source: {_yaml_value(source)}",
            f"published_at: {_yaml_value(published_at)}",
            f"url: {_yaml_value(url)}",
            "---",
            "",
            f"# {title}",
            "",
            "## 正文",
            "",
            content or title,
            "",
        ]
        return "\n".join(sections)

    def _build_manifest_item(self, index: int, hotspot: EducationHotspot, date_label: str) -> dict:
        return {
            "rank": index,
            "file": f"{date_label}_{index:02d}.md",
            "title": _compact_line(hotspot.title, 120),
            "account": _single_line(hotspot.author or hotspot.source or ""),
            "source": _single_line(hotspot.source),
            "published_at": hotspot.publish_time.strftime("%Y-%m-%d %H:%M"),
            "url": _single_line(hotspot.url),
        }


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


def _today_in_longxia_timezone() -> date:
    try:
        return datetime.now(ZoneInfo(LONGXIA_CANDIDATE_TIMEZONE)).date()
    except ZoneInfoNotFoundError:
        logger.warning(f"未知时区 {LONGXIA_CANDIDATE_TIMEZONE}，使用本机当前日期")
        return datetime.now().date()
