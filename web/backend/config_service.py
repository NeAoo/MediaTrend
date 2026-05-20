from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from config.app_config import ConfigValidationError, load_app_config


class ConfigWriteError(ValueError):
    pass


def read_yaml_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise ConfigWriteError(f"配置文件不存在: {config_path}")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigWriteError("config.yaml root must be a mapping")
    return payload


def _backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.name}.bak.{timestamp}")


def write_validated_config(config_path: Path, data: dict[str, Any]) -> None:
    config_path = config_path.resolve()
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")
    rendered = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    tmp_path.write_text(rendered, encoding="utf-8")
    try:
        load_app_config(tmp_path)
    except (ConfigValidationError, ValueError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise ConfigWriteError(str(exc)) from exc
    if config_path.exists():
        _backup_path(config_path).write_text(original, encoding="utf-8")
    tmp_path.replace(config_path)


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text_file_with_backup(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _backup_path(path).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    tmp_path.replace(path)


def validate_scoring_prompt(system_prompt: str, user_prompt: str) -> list[str]:
    warnings: list[str] = []
    if not system_prompt.strip():
        warnings.append("system prompt 为空")
    if not user_prompt.strip():
        warnings.append("user prompt 为空")
    for field_name in ["title", "source", "author", "publish_time", "url", "popularity", "content"]:
        if "{" + field_name + "}" not in user_prompt:
            warnings.append(f"user prompt 缺少变量 {{{field_name}}}")
    if "overall" not in user_prompt:
        warnings.append("user prompt 未包含 overall 字段说明")
    left_brace_count = user_prompt.count("{")
    right_brace_count = user_prompt.count("}")
    if left_brace_count != right_brace_count:
        warnings.append("user prompt 花括号数量不匹配，JSON 示例或变量可能写错")
    try:
        json_start = user_prompt.index("{")
        json_end = user_prompt.index("}", json_start) + 1
        json.loads(user_prompt[json_start:json_end])
    except (ValueError, json.JSONDecodeError):
        warnings.append("user prompt 中的第一个 JSON 示例无法直接解析")
    return warnings
