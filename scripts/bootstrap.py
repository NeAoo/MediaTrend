#!/usr/bin/env python3
"""Set up and validate an AITrend checkout."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_RUNTIME_DIRS = [
    "browser_data",
    "raw_data",
    "merged_data",
    "scored_data",
    "output",
    "logs",
]

CONFIG_VALIDATION_MODULES = {
    "yaml": "PyYAML",
    "pydantic": "pydantic",
}
LOCAL_EXAMPLE_FILES = {
    ".env": ".env.example",
    "config.yaml": "config.yaml.example",
}


def command_to_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def run_command(command: list[str], check: bool) -> int:
    print(f"$ {command_to_text(command)}")
    if check:
        return 0
    return subprocess.call(command, cwd=PROJECT_ROOT)


def run_warning_command(command: list[str], check: bool, warn_message: str) -> bool:
    exit_code = run_command(command, check=check)
    if exit_code == 0:
        return True
    print(f"WARN: {warn_message} (exit code {exit_code})")
    return False


def node_major_version(raw: str) -> int | None:
    text = raw.strip()
    if text.startswith("v"):
        text = text[1:]
    major = text.split(".", 1)[0]
    return int(major) if major.isdigit() else None


def check_node() -> bool:
    node = shutil.which("node")
    if not node:
        print("WARN: Node.js not found. Zhihu/TrendCrawlerRuntime may fail; install Node.js >= 16.")
        return False
    completed = subprocess.run([node, "--version"], capture_output=True, text=True)
    major = node_major_version(completed.stdout)
    if major is None or major < 16:
        print(f"WARN: Node.js >= 16 required, detected: {completed.stdout.strip()}")
        return False
    print(f"OK: Node.js {completed.stdout.strip()}")
    return True


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def venv_command_target(command: str) -> Path | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    target = Path(parts[-1]).expanduser()
    return target if target.name == ".venv" else None


def check_virtualenv_location() -> bool:
    expected_venv = (PROJECT_ROOT / ".venv").resolve()
    current_prefix = Path(sys.prefix).resolve()
    ok = True

    if not is_relative_to(current_prefix, PROJECT_ROOT.resolve()):
        print(
            "WARN: Python environment is outside this checkout: "
            f"{current_prefix}. Recommended: python -m venv .venv && "
            "source .venv/bin/activate"
        )
        ok = False

    pyvenv_cfg = current_prefix / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        for line in pyvenv_cfg.read_text(encoding="utf-8").splitlines():
            if not line.startswith("command ="):
                continue
            target = venv_command_target(line.split("=", 1)[1].strip())
            if target and target.resolve() != expected_venv:
                print(
                    "WARN: pyvenv.cfg was created for another checkout: "
                    f"{target}. Rebuild .venv if imports or paths behave oddly."
                )
                ok = False
            break

    return ok


def ensure_local_example_files(check: bool) -> None:
    for local_name, example_name in LOCAL_EXAMPLE_FILES.items():
        local_path = PROJECT_ROOT / local_name
        example_path = PROJECT_ROOT / example_name
        if local_path.exists():
            continue
        if not example_path.exists():
            print(f"WARN: cannot create {local_name}; missing {example_name}")
            continue
        if check:
            print(f"INFO: would create {local_name} from {example_name}")
            continue
        shutil.copyfile(example_path, local_path)
        print(f"OK: created {local_name} from {example_name}")


def missing_config_validation_modules() -> list[str]:
    return [
        package
        for module, package in CONFIG_VALIDATION_MODULES.items()
        if importlib.util.find_spec(module) is None
    ]


def runtime_dirs_from_config() -> list[str]:
    trend_crawler_runtime_dir = "TrendCrawlerRuntime"
    try:
        from config.app_config import load_app_config

        app_config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
        trend_crawler_runtime_path = app_config.resolve_path(app_config.trend_crawler_runtime.dir)
        if is_relative_to(trend_crawler_runtime_path.resolve(), PROJECT_ROOT.resolve()):
            trend_crawler_runtime_dir = str(trend_crawler_runtime_path.relative_to(PROJECT_ROOT))
        else:
            trend_crawler_runtime_dir = str(trend_crawler_runtime_path)
    except Exception:
        trend_crawler_runtime_dir = "TrendCrawlerRuntime"

    return BASE_RUNTIME_DIRS + [
        f"{trend_crawler_runtime_dir}/browser_data",
        f"{trend_crawler_runtime_dir}/data",
    ]


def ensure_runtime_dirs() -> None:
    for item in runtime_dirs_from_config():
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        label = path.relative_to(PROJECT_ROOT) if is_relative_to(path, PROJECT_ROOT) else path
        print(f"OK: directory {label}")


def trend_crawler_runtime_dir_from_config() -> Path:
    from config.app_config import load_app_config

    app_config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
    return app_config.resolve_path(app_config.trend_crawler_runtime.dir)


def has_login_state(path: Path) -> bool:
    if path.is_file():
        return path.stat().st_size > 0
    if path.is_dir():
        return any(path.iterdir())
    return False


def validate_required_files() -> bool:
    ok = True
    for name in [".env", "config.yaml"]:
        path = PROJECT_ROOT / name
        if path.exists():
            print(f"OK: found {name}")
        else:
            print(f"ERROR: missing {name}")
            ok = False
    return ok


def validate_app_config() -> bool:
    missing = missing_config_validation_modules()
    if missing:
        print(
            "ERROR: config validation dependencies are missing: "
            f"{', '.join(missing)}. Run `python scripts/bootstrap.py` first, "
            "then rerun `python scripts/bootstrap.py --check`."
        )
        return False

    try:
        from config.app_config import load_app_config

        config = load_app_config(os.getenv("AI_TREND_CONFIG", "config.yaml"))
    except Exception as exc:
        print(f"ERROR: config validation failed: {exc}")
        return False
    print(f"OK: enabled sources: {', '.join(config.enabled_sources)}")
    return True


def report_login_state() -> None:
    try:
        trend_crawler_runtime_dir = trend_crawler_runtime_dir_from_config()
    except Exception:
        trend_crawler_runtime_dir = PROJECT_ROOT / "TrendCrawlerRuntime"
    checks = [
        ("wechat_mp", PROJECT_ROOT / "browser_data" / "wechat_mp_state.json"),
        ("trendcrawler", trend_crawler_runtime_dir / "browser_data"),
    ]
    for label, path in checks:
        if has_login_state(path):
            display = path.relative_to(PROJECT_ROOT) if is_relative_to(path, PROJECT_ROOT) else path
            print(f"OK: {label} login state exists at {display}")
        else:
            print(f"INFO: {label} login state missing; first run will require QR login")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap AITrend local environment")
    parser.add_argument("--check", action="store_true", help="report actions without installing")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10+ required")
        return 1

    check_virtualenv_location()
    ensure_local_example_files(check=args.check)
    ensure_runtime_dirs()
    files_ok = validate_required_files()

    try:
        trend_crawler_runtime_dir = trend_crawler_runtime_dir_from_config()
    except Exception:
        trend_crawler_runtime_dir = PROJECT_ROOT / "TrendCrawlerRuntime"

    commands = [[sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]]
    media_requirements = trend_crawler_runtime_dir / "requirements.txt"
    if media_requirements.exists():
        commands.append(
            [sys.executable, "-m", "pip", "install", "-r", str(media_requirements)]
        )
    else:
        print(f"WARN: TrendCrawlerRuntime requirements not found: {media_requirements}")
    commands.append([sys.executable, "-m", "playwright", "install", "chromium"])
    for command in commands:
        if run_command(command, check=args.check) != 0:
            return 1

    run_warning_command(
        [sys.executable, "-m", "pip", "check"],
        check=args.check,
        warn_message="pip dependency check reported conflicts",
    )

    node_ok = check_node()
    config_ok = validate_app_config() if files_ok else False
    report_login_state()

    return 0 if files_ok and node_ok and config_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
