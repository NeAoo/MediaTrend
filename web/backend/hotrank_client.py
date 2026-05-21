from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from web.backend.hotrank_aggregator import CHANNEL_NAMES, parse_hot_value
from web.backend.hotrank_models import HotrankChannelItem, HotrankFetchResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOST = "https://api.cimidata.com"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_TOKEN_CACHE = PROJECT_ROOT / "web_jobs" / "hotrank" / "token.json"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_REQUEST_INTERVAL_SECONDS = 1.05
TOKEN_ENDPOINT = "/api/v2/token"
HOTRANK_ENDPOINT = "/api/v3/hotrank"
TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
TOKEN_REFRESH_MARGIN_SECONDS = 12 * 60 * 60


class CimiDataError(RuntimeError):
    pass


class CimiDataHttpError(CimiDataError):
    def __init__(self, path: str, status: int, body: str) -> None:
        super().__init__(f"{path} HTTP {status}: {body[:240]}")
        self.path = path
        self.status = status
        self.body = body


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class CimiDataHotrankClient:
    def __init__(
        self,
        host: str | None = None,
        env_file: Path = DEFAULT_ENV_FILE,
        token_cache: Path = DEFAULT_TOKEN_CACHE,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        request_interval_seconds: float = DEFAULT_REQUEST_INTERVAL_SECONDS,
    ) -> None:
        self.host = (host or os.environ.get("CIMIDATA_HOST") or DEFAULT_HOST).rstrip("/")
        self.env_file = env_file
        self.token_cache = token_cache
        self.timeout_seconds = timeout_seconds
        self.request_interval_seconds = max(request_interval_seconds, DEFAULT_REQUEST_INTERVAL_SECONDS)

    def fetch_channels(self, channel_ids: list[int]) -> list[HotrankFetchResult]:
        assert channel_ids, "channel_ids must not be empty"
        load_env_file(self.env_file)
        app_id = os.environ.get("CIMIDATA_APP_ID", "").strip()
        app_secret = os.environ.get("CIMIDATA_APP_SECRET", "").strip()
        if not app_id or not app_secret:
            raise CimiDataError("CIMIDATA_APP_ID / CIMIDATA_APP_SECRET 未配置")
        access_token = self._load_token(app_id, app_secret)

        results: list[HotrankFetchResult] = []
        for index, channel_id in enumerate(channel_ids):
            if index > 0:
                time.sleep(self.request_interval_seconds)
            channel_name = CHANNEL_NAMES.get(channel_id, f"channel-{channel_id}")
            try:
                results.append(self.fetch_channel(access_token, channel_id))
            except Exception as exc:
                results.append(
                    HotrankFetchResult(
                        channel_id=channel_id,
                        channel_name=channel_name,
                        ok=False,
                        error=str(exc),
                    )
                )
        return results

    def fetch_channel(self, access_token: str, channel_id: int) -> HotrankFetchResult:
        channel_name = CHANNEL_NAMES.get(channel_id, f"channel-{channel_id}")
        response = self._get_json(
            HOTRANK_ENDPOINT,
            {
                "access_token": access_token,
                "channel_id": channel_id,
            },
        )
        code = int(response.get("code", 0) or 0)
        if code != 200:
            raise CimiDataError(f"{HOTRANK_ENDPOINT} returned code={code}, msg={response.get('msg', '')}")
        data = response.get("data")
        if not isinstance(data, list):
            raise CimiDataError(f"{HOTRANK_ENDPOINT} returned non-list data")

        items = [
            self._parse_item(channel_id, channel_name, index, item)
            for index, item in enumerate(data, start=1)
            if isinstance(item, dict)
        ]
        return HotrankFetchResult(
            channel_id=channel_id,
            channel_name=channel_name,
            ok=True,
            items=items,
            balance=_safe_int(response.get("balance")),
            raw_response=response,
        )

    def _load_token(self, app_id: str, app_secret: str) -> str:
        now = time.time()
        if self.token_cache.exists():
            try:
                cached = self._read_json(self.token_cache)
                token = str(cached.get("access_token", "") or "").strip()
                expires_at = float(cached.get("expires_at", 0) or 0)
                if token and now + TOKEN_REFRESH_MARGIN_SECONDS < expires_at:
                    return token
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        response = self._post_json(
            TOKEN_ENDPOINT,
            {
                "app_id": app_id,
                "app_secret": app_secret,
            },
        )
        code = int(response.get("code", 0) or 0)
        if code != 200:
            raise CimiDataError(f"{TOKEN_ENDPOINT} returned code={code}, msg={response.get('msg', '')}")
        data = response.get("data") or {}
        if not isinstance(data, dict):
            raise CimiDataError("token response data is not an object")
        token = str(data.get("access_token") or data.get("token") or "").strip()
        if not token:
            raise CimiDataError("CimiData token response did not include access_token")

        self._write_json(
            self.token_cache,
            {
                "access_token": token,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "expires_at": now + TOKEN_TTL_SECONDS,
                "refresh_margin_seconds": TOKEN_REFRESH_MARGIN_SECONDS,
            },
        )
        self.token_cache.chmod(0o600)
        return token

    def _parse_item(
        self,
        channel_id: int,
        channel_name: str,
        rank: int,
        item: dict[str, Any],
    ) -> HotrankChannelItem:
        raw_hot = str(item.get("hot", "") or "")
        return HotrankChannelItem(
            id=_safe_int(item.get("id")),
            channel_id=channel_id,
            channel_name=channel_name,
            rank=rank,
            title=str(item.get("title", "") or "").strip(),
            url=str(item.get("url", "") or ""),
            hot=raw_hot,
            hot_value=parse_hot_value(raw_hot),
            hot_tag=str(item.get("hot_tag", "") or ""),
            summary=str(item.get("summary", "") or ""),
            created_at=str(item.get("created_at", "") or "") or None,
        )

    def _get_json(self, path: str, query: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path, query)
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        return self._open_json(path, request)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self._url(path, None),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        return self._open_json(path, request)

    def _url(self, path: str, query: dict[str, Any] | None) -> str:
        assert path.startswith("/api/"), f"Unexpected CimiData path: {path}"
        url = self.host + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        return url

    def _open_json(self, path: str, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            raise CimiDataHttpError(path, error.code, body) from error
        except urllib.error.URLError as error:
            raise CimiDataError(f"{path} request failed: {error}") from error

        parsed = json.loads(raw_body)
        if not isinstance(parsed, dict):
            raise CimiDataError(f"{path} returned non-object JSON")
        return parsed

    def _read_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"JSON object expected: {path}")
        return data

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
