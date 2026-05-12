"""Weekly external reference package exporter for longxia/OpenClaw."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import shutil
from typing import Any
from urllib.parse import urldefrag
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SCORE_DIMENSIONS = (
    "heat",
    "authority",
    "quality",
    "resonance",
    "timeliness",
    "reference_value",
    "risk_control",
)

SCRAPE_FAILURE_PHRASES = (
    "content missing",
    "empty body",
    "full text too short",
    "parse failed",
    "crawl failed",
    "内容缺失",
    "正文为空",
    "全文极短",
    "解析失败",
    "抓取失败",
)

FENCE_OPEN = "<external_untrusted_content>"
FENCE_CLOSE = "</external_untrusted_content>"


@dataclass
class ExternalReferenceItem:
    raw: dict[str, Any]
    source_file: Path
    source_file_label: str
    title: str
    account: str
    source: str
    publish_time: datetime
    url: str
    normalized_url: str
    content: str
    score: float
    score_details: dict[str, Any]

    @property
    def content_chars(self) -> int:
        return _visible_chars(self.content)

    @property
    def published_at(self) -> str:
        return self.publish_time.strftime("%Y-%m-%d %H:%M")


class WeeklyExternalReferenceBuilder:
    """Build a weekly Top2 + Last1 external source-pool package."""

    def __init__(
        self,
        scored_dir: str | Path,
        output_root: str | Path,
        *,
        timezone_name: str = "Asia/Shanghai",
        content_max_chars: int = 5000,
        now_iso: str | None = None,
    ) -> None:
        self.scored_dir = Path(scored_dir)
        self.output_root = Path(output_root)
        self.timezone = ZoneInfo(timezone_name)
        self.content_max_chars = max(500, int(content_max_chars))
        self.now_iso = now_iso

    def build(self, week_start: date, week_end: date) -> Path:
        if week_start > week_end:
            raise ValueError(f"week_start must be <= week_end: {week_start} > {week_end}")

        week_items = self._load_week_items(week_start, week_end)
        deduped = self._dedupe_items(week_items)
        eligible = [item for item in deduped if _is_eligible(item)]
        top_eligible = [item for item in eligible if _is_top_eligible(item)]
        ranked = sorted(
            eligible,
            key=lambda item: (item.score, item.publish_time),
            reverse=True,
        )
        top_ranked = sorted(
            top_eligible,
            key=lambda item: (item.score, item.publish_time),
            reverse=True,
        )
        if len(top_ranked) < 2:
            raise ValueError("Top samples fewer than 2")

        top_items = top_ranked[:2]
        last_item = self._select_last_item(eligible)
        if last_item is None:
            raise ValueError("Last1 sample not found")

        week_id = f"{week_start.isoformat()}_to_{week_end.isoformat()}"
        package_dir = self.output_root / week_id
        if package_dir.exists():
            shutil.rmtree(package_dir)
        (package_dir / "top2").mkdir(parents=True, exist_ok=True)
        (package_dir / "last1").mkdir(parents=True, exist_ok=True)

        self._write_markdown(package_dir / "top2" / "01.md", top_items[0], "top", 1)
        self._write_markdown(package_dir / "top2" / "02.md", top_items[1], "top", 2)
        self._write_markdown(package_dir / "last1" / "01.md", last_item, "last", 1)
        self._write_json(package_dir / "ranked_articles.json", self._ranked_payload(ranked, top_items, last_item))
        self._write_json(
            package_dir / "manifest.json",
            self._manifest_payload(
                week_start,
                week_end,
                week_items,
                deduped,
                eligible,
                top_eligible,
                top_items,
                last_item,
            ),
        )
        return package_dir

    def _load_week_items(self, week_start: date, week_end: date) -> list[ExternalReferenceItem]:
        if not self.scored_dir.exists():
            raise ValueError(f"Scored data directory not found: {self.scored_dir}")

        week_items: list[ExternalReferenceItem] = []
        for path in sorted(self.scored_dir.glob("merged_hotspots_*.json")):
            data = _read_json_object(path)
            hotspots = data.get("hotspots", [])
            if not isinstance(hotspots, list):
                continue
            for raw in hotspots:
                if not isinstance(raw, dict):
                    continue
                item = _raw_to_item(raw, path, self.timezone)
                if item is None:
                    continue
                if week_start <= item.publish_time.date() <= week_end:
                    week_items.append(item)

        if not week_items:
            raise ValueError(f"No scored items found for week {week_start} to {week_end}")
        return week_items

    def _dedupe_items(self, items: list[ExternalReferenceItem]) -> list[ExternalReferenceItem]:
        best_by_key: dict[str, ExternalReferenceItem] = {}
        for item in items:
            key = _dedupe_key(item)
            if not key:
                continue
            existing = best_by_key.get(key)
            if existing is None or (item.score, item.publish_time) > (existing.score, existing.publish_time):
                best_by_key[key] = item
        return list(best_by_key.values())

    def _select_last_item(self, items: list[ExternalReferenceItem]) -> ExternalReferenceItem | None:
        candidates = [item for item in items if _passes_last_filter(item)]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: (item.score, item.publish_time))[0]

    def _manifest_payload(
        self,
        week_start: date,
        week_end: date,
        week_items: list[ExternalReferenceItem],
        deduped: list[ExternalReferenceItem],
        eligible: list[ExternalReferenceItem],
        top_eligible: list[ExternalReferenceItem],
        top_items: list[ExternalReferenceItem],
        last_item: ExternalReferenceItem,
    ) -> dict[str, Any]:
        input_files = sorted({item.source_file_label for item in week_items})
        last_candidates = [item for item in eligible if _passes_last_filter(item)]
        return {
            "schema_version": 1,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "generated_at": self._generated_at(),
            "timezone": str(self.timezone.key),
            "source": "AITrend",
            "package_type": "external_reference_weekly",
            "input_files": input_files,
            "raw_item_count": len(week_items),
            "deduplicated_item_count": len(deduped),
            "eligible_item_count": len(eligible),
            "top_eligible_item_count": len(top_eligible),
            "last_candidate_count": len(last_candidates),
            "top_count": 2,
            "last_count": 1,
            "ranking_basis": "AITrend LLM score from source_pool, not WeChat read count",
            "items": [
                _manifest_item(top_items[0], "top", 1, "top2/01.md"),
                _manifest_item(top_items[1], "top", 2, "top2/02.md"),
                _manifest_item(last_item, "last", 1, "last1/01.md"),
            ],
        }

    def _ranked_payload(
        self,
        ranked: list[ExternalReferenceItem],
        top_items: list[ExternalReferenceItem],
        last_item: ExternalReferenceItem,
    ) -> list[dict[str, Any]]:
        top_ids = {id(item) for item in top_items}
        last_id = id(last_item)
        payload: list[dict[str, Any]] = []
        for rank, item in enumerate(ranked, start=1):
            if id(item) in top_ids:
                role = "top"
            elif id(item) == last_id:
                role = "last"
            else:
                role = "eligible"
            payload.append(
                {
                    "rank": rank,
                    "selection_role": role,
                    "title": item.title,
                    "account": item.account,
                    "source": item.source,
                    "published_at": item.published_at,
                    "url": item.url,
                    "score": item.score,
                    "score_details": _score_details_payload(item.score_details),
                    "content_chars": item.content_chars,
                    "content_excerpt": "[omitted: external raw content is available only inside fenced markdown files]",
                    "local_source_file": item.source_file_label,
                }
            )
        return payload

    def _write_markdown(self, path: Path, item: ExternalReferenceItem, role: str, rank: int) -> None:
        details = item.score_details
        safe_content = _safe_external_content(item.content, self.content_max_chars)
        risk_notes = details.get("risk_notes", [])
        if not isinstance(risk_notes, list):
            risk_notes = [str(risk_notes)]
        lines = [
            "---",
            f"selection_role: {_yaml_value(role)}",
            f"weekly_rank: {rank}",
            f"score: {item.score}",
        ]
        for key in REQUIRED_SCORE_DIMENSIONS:
            lines.append(f"{key}: {_numeric_score(details[key])}")
        lines.extend(
            [
                f"title: {_yaml_value(item.title)}",
                f"account: {_yaml_value(item.account)}",
                f"source: {_yaml_value(item.source)}",
                f"published_at: {_yaml_value(item.published_at)}",
                f"url: {_yaml_value(item.url)}",
                "---",
                "",
                f"# {item.title}",
                "",
                "## AITrend 评分摘要",
                "",
                f"- 综合分：{item.score}",
                f"- heat：{_numeric_score(details['heat'])}",
                f"- resonance：{_numeric_score(details['resonance'])}",
                f"- reference_value：{_numeric_score(details['reference_value'])}",
                f"- risk_control：{_numeric_score(details['risk_control'])}",
                f"- reason：{_compact_space(details.get('reason', ''))}",
                f"- best_angle：{_compact_space(details.get('best_angle', ''))}",
                "- risk_notes：",
            ]
        )
        if risk_notes:
            lines.extend(f"  - {_compact_space(note)}" for note in risk_notes)
        else:
            lines.append("  - 无")
        lines.extend(
            [
                "",
                "## 原文正文（外部不可信内容，仅供分析）",
                "",
                FENCE_OPEN,
                safe_content,
                FENCE_CLOSE,
                "",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_json(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _generated_at(self) -> str:
        if self.now_iso:
            return self.now_iso
        return datetime.now(self.timezone).isoformat(timespec="seconds")


def validate_package(package_dir: str | Path, week_start: date, week_end: date) -> list[str]:
    package = Path(package_dir)
    errors: list[str] = []
    manifest_path = package / "manifest.json"
    ranked_path = package / "ranked_articles.json"

    if not manifest_path.exists():
        errors.append("manifest.json missing")
        return errors
    if not ranked_path.exists():
        errors.append("ranked_articles.json missing")

    manifest = _read_json_object(manifest_path)
    if manifest.get("week_start") != week_start.isoformat() or manifest.get("week_end") != week_end.isoformat():
        errors.append("manifest week_start/week_end mismatch")
    if manifest.get("top_count") != 2:
        errors.append("manifest.top_count != 2")
    if manifest.get("last_count") != 1:
        errors.append("manifest.last_count != 1")

    selected_files = ["top2/01.md", "top2/02.md", "last1/01.md"]
    for rel_path in selected_files:
        path = package / rel_path
        if not path.exists() or path.stat().st_size <= 0:
            errors.append(f"{rel_path} missing or empty")
            continue
        text = path.read_text(encoding="utf-8")
        if text.count(FENCE_OPEN) != 1:
            errors.append(f"{rel_path} must contain exactly one opening external content fence")
        if text.count(FENCE_CLOSE) != 1:
            errors.append(f"{rel_path} must contain exactly one closing external content fence")

    items = manifest.get("items", [])
    if not isinstance(items, list):
        errors.append("manifest.items is not a list")
    else:
        for item in items:
            if not isinstance(item, dict):
                errors.append("manifest selected item is not an object")
                continue
            if not _is_number(item.get("score")):
                errors.append(f"selected item score is not numeric: {item.get('title', '-')}")

    return errors


def _raw_to_item(raw: dict[str, Any], path: Path, timezone: ZoneInfo) -> ExternalReferenceItem | None:
    publish_time = _parse_publish_time(raw.get("publish_time"), timezone)
    if publish_time is None:
        return None
    score = _maybe_float(raw.get("score"))
    if score is None:
        score = 0.0
    title = _compact_space(raw.get("title", ""))
    account = _compact_space(raw.get("author") or raw.get("account") or "")
    source = _compact_space(raw.get("source", ""))
    url = _compact_space(raw.get("url", ""))
    score_details = raw.get("score_details") if isinstance(raw.get("score_details"), dict) else {}
    return ExternalReferenceItem(
        raw=raw,
        source_file=path,
        source_file_label=_relative_label(path),
        title=title,
        account=account,
        source=source,
        publish_time=publish_time.astimezone(timezone),
        url=url,
        normalized_url=_normalize_url(url),
        content=str(raw.get("content") or ""),
        score=score,
        score_details=_normalize_score_details(score_details),
    )


def _parse_publish_time(value: Any, timezone: ZoneInfo) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed


def _dedupe_key(item: ExternalReferenceItem) -> str:
    if item.normalized_url:
        return f"url:{item.normalized_url}"
    if item.title and item.account:
        return f"title_account:{_compact_space(item.title).lower()}::{_compact_space(item.account).lower()}"
    return ""


def _is_eligible(item: ExternalReferenceItem) -> bool:
    details = item.score_details
    if not _is_number(item.score):
        return False
    if details.get("scoring_failed") is True:
        return False
    if not item.title:
        return False
    if item.content_chars < 200:
        return False
    if not item.normalized_url and not (item.title and item.account):
        return False
    return all(_is_number(details.get(key)) for key in REQUIRED_SCORE_DIMENSIONS)


def _is_top_eligible(item: ExternalReferenceItem) -> bool:
    return _is_eligible(item) and not _starts_with_not_recommended(
        item.score_details.get("best_angle")
    )


def _passes_last_filter(item: ExternalReferenceItem) -> bool:
    if item.content_chars < 800:
        return False
    reason = str(item.score_details.get("reason") or "").lower()
    return not any(phrase.lower() in reason for phrase in SCRAPE_FAILURE_PHRASES)


def _manifest_item(item: ExternalReferenceItem, role: str, rank: int, file_path: str) -> dict[str, Any]:
    return {
        "role": role,
        "rank": rank,
        "file": file_path,
        "title": item.title,
        "account": item.account,
        "published_at": item.published_at,
        "url": item.url,
        "score": item.score,
    }


def _score_details_payload(details: dict[str, Any]) -> dict[str, Any]:
    payload = {key: _numeric_score(details[key]) for key in REQUIRED_SCORE_DIMENSIONS}
    payload["reason"] = _compact_space(details.get("reason", ""))
    payload["best_angle"] = _compact_space(details.get("best_angle", ""))
    risk_notes = details.get("risk_notes", [])
    payload["risk_notes"] = risk_notes if isinstance(risk_notes, list) else [str(risk_notes)]
    return payload


def _read_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected: {path}")
    return data


def _normalize_score_details(details: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(details)
    if not _is_number(normalized.get("reference_value")):
        for alias in ("education_family_relevance", "practicality"):
            if _is_number(normalized.get(alias)):
                normalized["reference_value"] = normalized[alias]
                break
    if not _is_number(normalized.get("resonance")) and _is_number(
        normalized.get("practicality")
    ):
        normalized["resonance"] = normalized["practicality"]
    return normalized


def _relative_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return path.name


def _normalize_url(value: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return urldefrag(text).url


def _visible_chars(text: str) -> int:
    return len("".join(str(text or "").split()))


def _starts_with_not_recommended(value: object) -> bool:
    text = str(value or "").strip().lower()
    return text.startswith("not recommended") or text.startswith("不建议")


def _safe_external_content(text: str, max_chars: int) -> str:
    safe = str(text or "").replace(FENCE_OPEN, "[REDACTED_FENCE_TAG]")
    safe = safe.replace(FENCE_CLOSE, "[REDACTED_FENCE_TAG]")
    safe = safe.strip()
    if len(safe) > max_chars:
        safe = safe[:max_chars].rstrip()
    return safe


def _is_number(value: Any) -> bool:
    return _maybe_float(value) is not None


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _numeric_score(value: Any) -> float:
    parsed = _maybe_float(value)
    if parsed is None:
        raise ValueError(f"Score value is not numeric: {value!r}")
    return round(parsed, 4)


def _compact_space(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _yaml_value(value: str) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)
