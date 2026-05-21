from __future__ import annotations

import time
import asyncio
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from config.app_config import AppConfig, load_app_config
from web.backend.config_service import read_yaml_config, write_validated_config
from web.backend.env_service import read_env_value, write_env_value


LOGIN_REQUIRED_SOURCES = {"wechat_mp", "xiaohongshu", "zhihu"}
NO_LOGIN_SOURCES = {"wechat", "google_news", "aihot"}
SUPPORTED_AUTH_SOURCES = LOGIN_REQUIRED_SOURCES | NO_LOGIN_SOURCES
LOGIN_SESSION_TTL_SECONDS = 600
DEFAULT_VIEWPORT = {"width": 1280, "height": 900}
XHS_HOME_URL = "https://www.xiaohongshu.com"
ZHIHU_LOGIN_URL = "https://www.zhihu.com/signin?next=%2F"
WECHAT_MP_HOME_URL = "https://mp.weixin.qq.com/"

SOURCE_LABELS = {
    "wechat": "搜狗微信关键词",
    "wechat_mp": "微信公众号账号",
    "xiaohongshu": "小红书",
    "zhihu": "知乎",
    "google_news": "Google News",
    "aihot": "AI HOT",
}


@dataclass
class LoginSession:
    source: str
    playwright: Any
    browser: Any | None
    context: Any
    page: Any
    state_path: Path | None
    created_at: float
    login_url: str


def _has_login_state(path: Path) -> bool:
    if path.is_file():
        return path.stat().st_size > 0
    if not path.is_dir():
        return False
    for child in path.rglob("*"):
        if child.is_file() and child.stat().st_size > 0:
            return True
    return False


def _profile_has_cookie_name(profile_path: Path, cookie_name: str) -> bool:
    cookie_db_path = profile_path / "Default" / "Cookies"
    if not cookie_db_path.exists():
        return False
    with tempfile.TemporaryDirectory() as tmp_dir:
        copied_cookie_db = Path(tmp_dir) / "Cookies"
        try:
            shutil.copy2(cookie_db_path, copied_cookie_db)
        except OSError:
            return False
        try:
            with sqlite3.connect(copied_cookie_db) as connection:
                row = connection.execute(
                    """
                    select 1
                    from cookies
                    where name = ?
                      and host_key like '%zhihu.com'
                      and (length(value) > 0 or length(encrypted_value) > 0)
                    limit 1
                    """,
                    (cookie_name,),
                ).fetchone()
            return row is not None
        except sqlite3.DatabaseError:
            return False


def _source_label(source: str) -> str:
    return SOURCE_LABELS.get(source, source)


def _state_payload(
    source: str,
    status: str,
    label: str,
    message: str,
    *,
    login_url: str = "",
    checked_by: str = "static",
    requires_login: bool | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "display_name": _source_label(source),
        "requires_login": source in LOGIN_REQUIRED_SOURCES if requires_login is None else requires_login,
        "status": status,
        "label": label,
        "message": message,
        "login_url": login_url,
        "checked_by": checked_by,
    }


def _wechat_token_from_url(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    token_values = query.get("token", [])
    return token_values[0] if token_values else ""


def _trendcrawler_profile_paths(config: AppConfig, source: str) -> list[Path]:
    platform = "xhs" if source == "xiaohongshu" else "zhihu"
    runtime_dir = config.resolve_path(config.trend_crawler_runtime.dir)
    browser_data_dir = runtime_dir / "browser_data"
    return [
        browser_data_dir / f"cdp_{platform}_user_data_dir",
        browser_data_dir / f"{platform}_user_data_dir",
    ]


def _primary_trendcrawler_profile_path(config: AppConfig, source: str) -> Path:
    return _trendcrawler_profile_paths(config, source)[0]


def _cookie_login_is_configured(config_path: Path, source: str) -> bool:
    config = load_app_config(config_path)
    if source == "xiaohongshu":
        login_type = config.xiaohongshu.login_type or config.trend_crawler_runtime.login_type
        return login_type == "cookie" and bool(read_env_value(config_path.parent / ".env", "XIAOHONGSHU_COOKIE"))
    if source == "zhihu":
        login_type = config.zhihu.login_type or config.trend_crawler_runtime.login_type
        return login_type == "cookie" and bool(read_env_value(config_path.parent / ".env", "ZHIHU_COOKIE"))
    return False


def _set_source_login_type(config_path: Path, source: str, login_type: str) -> None:
    data = read_yaml_config(config_path)
    source_config = data.setdefault(source, {})
    if not isinstance(source_config, dict):
        source_config = {}
        data[source] = source_config
    source_config["login_type"] = login_type
    write_validated_config(config_path, data)


def _source_state_path(config: AppConfig, source: str) -> Path | None:
    if source == "wechat_mp":
        return config.resolve_path(config.wechat.account_crawl.storage_state)
    if source in {"xiaohongshu", "zhihu"}:
        for path in _trendcrawler_profile_paths(config, source):
            if _has_login_state(path):
                return path
        return _primary_trendcrawler_profile_path(config, source)
    return None


def source_auth_state(source: str, config_path: Path) -> dict[str, Any]:
    if source not in SUPPORTED_AUTH_SOURCES:
        return _state_payload(
            source,
            "error",
            "未知来源",
            "当前来源没有登录检测规则。",
            checked_by="rule",
            requires_login=False,
        )
    if source in NO_LOGIN_SOURCES:
        return _state_payload(
            source,
            "not_required",
            "不需要登录",
            "这个来源不依赖平台账号，抓取前不用扫码。",
            checked_by="rule",
            requires_login=False,
        )

    config = load_app_config(config_path)
    state_path = _source_state_path(config, source)
    if source == "zhihu":
        if _cookie_login_is_configured(config_path, source):
            return _state_payload(
                source,
                "online",
                "在线",
                "已保存知乎 Cookie；后续采集会优先使用 Cookie，过期后再重新扫码。",
                checked_by="cookie",
            )
        if state_path and _profile_has_cookie_name(state_path, "z_c0"):
            return _state_payload(
                source,
                "online",
                "在线",
                f"发现知乎 profile 中存在 z_c0：{state_path}",
                checked_by="saved_state",
            )
        return _state_payload(
            source,
            "offline",
            "未登录",
            "没有发现知乎有效 z_c0；点击后打开真实登录页，扫码完成后会保存为 Cookie。",
            checked_by="saved_state",
        )

    has_state = bool(state_path and _has_login_state(state_path))
    if not has_state and _cookie_login_is_configured(config_path, source):
        return _state_payload(
            source,
            "online",
            "在线",
            "已配置 Cookie 登录。",
            checked_by="cookie",
        )
    if has_state:
        return _state_payload(
            source,
            "online",
            "在线",
            f"发现已保存登录态：{state_path}",
            checked_by="saved_state",
        )
    return _state_payload(
        source,
        "offline",
        "未登录",
        "没有发现可用登录态；点击后会打开真实登录页。",
        checked_by="saved_state",
    )


def list_source_auth_states(config_path: Path) -> list[dict[str, Any]]:
    return [
        source_auth_state(source, config_path)
        for source in ["xiaohongshu", "zhihu", "google_news", "aihot", "wechat", "wechat_mp"]
    ]


class SourceAuthManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sessions: dict[str, LoginSession] = {}

    def _login_waiting_payload(self, session: LoginSession) -> dict[str, Any]:
        return _state_payload(
            session.source,
            "login_waiting",
            "等待登录",
            "登录页已在浏览器中打开。需要换号时直接在浏览器里操作，检测不会自动关闭窗口。",
            login_url=session.login_url,
            checked_by="login_session",
        )

    async def close_session(self, source: str) -> None:
        session = self._sessions.pop(source, None)
        if not session:
            return
        try:
            await session.context.close()
        except Exception:
            pass
        try:
            if session.browser is not None:
                await session.browser.close()
        except Exception:
            pass
        try:
            await session.playwright.stop()
        except Exception:
            pass

    async def start_login(self, source: str, config_path: Path) -> dict[str, Any]:
        async with self._lock:
            if source in NO_LOGIN_SOURCES:
                return source_auth_state(source, config_path)
            if source not in LOGIN_REQUIRED_SOURCES:
                return source_auth_state(source, config_path)
            await self.close_session(source)
            if source == "wechat_mp":
                return await self._start_wechat_mp_login(config_path)
            if source == "xiaohongshu":
                return await self._start_xiaohongshu_login(config_path)
            return await self._start_zhihu_login(config_path)

    async def poll_login(self, source: str, config_path: Path) -> dict[str, Any]:
        async with self._lock:
            session = self._sessions.get(source)
            if not session:
                return source_auth_state(source, config_path)
            if time.time() - session.created_at > LOGIN_SESSION_TTL_SECONDS:
                await self.close_session(source)
                return _state_payload(
                    source,
                    "offline",
                    "未登录",
                    "登录窗口已超时，请重新点击登录。",
                    checked_by="login_session",
                )
            if await self._session_is_online(session):
                return _state_payload(
                    source,
                    "login_waiting",
                    "已检测在线",
                    "检测到浏览器当前已登录。窗口会保持打开；如果要换号可继续在平台页操作，确认后点“完成并保存状态”。",
                    login_url=session.login_url,
                    checked_by="login_session",
                )
            return _state_payload(
                source,
                "login_waiting",
                "等待登录",
                "还没有检测到登录态。请继续在弹出的浏览器窗口完成登录，或重新打开登录页。",
                login_url=session.login_url,
                checked_by="login_session",
            )

    async def finish_login(self, source: str, config_path: Path) -> dict[str, Any]:
        async with self._lock:
            session = self._sessions.get(source)
            if not session:
                return source_auth_state(source, config_path)
            if time.time() - session.created_at > LOGIN_SESSION_TTL_SECONDS:
                await self.close_session(source)
                return _state_payload(
                    source,
                    "offline",
                    "未登录",
                    "登录窗口已超时，请重新打开登录页。",
                    checked_by="login_session",
                )
            if not await self._session_is_online(session):
                return _state_payload(
                    source,
                    "login_waiting",
                    "未检测到登录",
                    "当前浏览器还没有检测到有效登录态。请先在平台页完成登录，再点“完成并保存状态”。",
                    login_url=session.login_url,
                    checked_by="login_session",
                )
            if source == "wechat_mp" and session.state_path is not None:
                await session.context.storage_state(path=str(session.state_path))
            if source == "zhihu":
                try:
                    await _persist_zhihu_cookie_login(session.context, config_path)
                except Exception as exc:
                    return _state_payload(
                        source,
                        "error",
                        "保存失败",
                        f"知乎已登录，但 Cookie 保存失败：{exc}",
                        login_url=session.login_url,
                        checked_by="login_session",
                    )
            await self.close_session(source)
            return source_auth_state(source, config_path)

    async def _start_wechat_mp_login(self, config_path: Path) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        config = load_app_config(config_path)
        state_path = config.resolve_path(config.wechat.account_crawl.storage_state)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context_options: dict[str, Any] = {"viewport": DEFAULT_VIEWPORT}
        if _has_login_state(state_path):
            context_options["storage_state"] = str(state_path)
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        await page.goto(WECHAT_MP_HOME_URL, wait_until="domcontentloaded", timeout=60000)
        await _bring_page_to_front(page)
        self._sessions["wechat_mp"] = LoginSession(
            source="wechat_mp",
            playwright=playwright,
            browser=browser,
            context=context,
            page=page,
            state_path=state_path,
            created_at=time.time(),
            login_url=WECHAT_MP_HOME_URL,
        )
        return self._login_waiting_payload(self._sessions["wechat_mp"])

    async def _start_xiaohongshu_login(self, config_path: Path) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        config = load_app_config(config_path)
        user_data_dir = _primary_trendcrawler_profile_path(config, "xiaohongshu")
        user_data_dir.mkdir(parents=True, exist_ok=True)
        playwright = await async_playwright().start()
        context = await _launch_persistent_context(
            playwright,
            user_data_dir,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto(XHS_HOME_URL, wait_until="domcontentloaded", timeout=60000)
        await _bring_page_to_front(page)
        if not await _xhs_is_online(context, page):
            await _click_first_visible(
                page,
                [
                    "xpath=//button[normalize-space()='登录']",
                    "xpath=//*[self::button or self::span or self::div][normalize-space()='登录']",
                    "xpath=//*[self::button or self::span or self::div][contains(normalize-space(), '登录')]",
                ],
            )
        await _bring_page_to_front(page)
        self._sessions["xiaohongshu"] = LoginSession(
            source="xiaohongshu",
            playwright=playwright,
            browser=None,
            context=context,
            page=page,
            state_path=user_data_dir,
            created_at=time.time(),
            login_url=XHS_HOME_URL,
        )
        return self._login_waiting_payload(self._sessions["xiaohongshu"])

    async def _start_zhihu_login(self, config_path: Path) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        config = load_app_config(config_path)
        user_data_dir = _primary_trendcrawler_profile_path(config, "zhihu")
        user_data_dir.mkdir(parents=True, exist_ok=True)
        playwright = await async_playwright().start()
        context = await _launch_persistent_context(
            playwright,
            user_data_dir,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto(ZHIHU_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        await _bring_page_to_front(page)
        self._sessions["zhihu"] = LoginSession(
            source="zhihu",
            playwright=playwright,
            browser=None,
            context=context,
            page=page,
            state_path=user_data_dir,
            created_at=time.time(),
            login_url=ZHIHU_LOGIN_URL,
        )
        return self._login_waiting_payload(self._sessions["zhihu"])

    async def _session_is_online(self, session: LoginSession) -> bool:
        if session.source == "wechat_mp":
            return bool(_wechat_token_from_url(session.page.url))
        if session.source == "xiaohongshu":
            return await _xhs_is_online(session.context, session.page)
        if session.source == "zhihu":
            return await _zhihu_is_online(session.context)
        return False


async def _launch_persistent_context(playwright: Any, user_data_dir: Path, user_agent: str) -> Any:
    options = {
        "user_data_dir": str(user_data_dir),
        "headless": False,
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": user_agent,
    }
    try:
        return await playwright.chromium.launch_persistent_context(channel="chrome", **options)
    except Exception:
        return await playwright.chromium.launch_persistent_context(**options)


async def _has_cookie(context: Any, cookie_name: str, url: str) -> bool:
    try:
        cookies = await context.cookies([url])
    except Exception:
        cookies = await context.cookies()
    return any(cookie.get("name") == cookie_name and cookie.get("value") for cookie in cookies)


async def _xhs_is_online(context: Any, page: Any) -> bool:
    if await _has_cookie(context, "web_session", XHS_HOME_URL):
        try:
            profile_link = page.locator("a[href*='/user/profile/']").first
            if await profile_link.is_visible(timeout=800):
                return True
        except Exception:
            return True
    return False


async def _zhihu_is_online(context: Any) -> bool:
    return await _has_cookie(context, "z_c0", "https://www.zhihu.com")


async def _persist_zhihu_cookie_login(context: Any, config_path: Path) -> None:
    cookies = await context.cookies(["https://www.zhihu.com"])
    zhihu_cookies = [
        cookie
        for cookie in cookies
        if "zhihu.com" in str(cookie.get("domain", "")) and cookie.get("value")
    ]
    has_session_cookie = any(cookie.get("name") == "z_c0" for cookie in zhihu_cookies)
    if not has_session_cookie:
        raise ValueError("知乎登录态缺少 z_c0，不能保存为 Cookie 登录。")

    cookie_header = "; ".join(
        f"{cookie['name']}={cookie['value']}" for cookie in zhihu_cookies
    )
    env_path = config_path.parent / ".env"
    write_env_value(env_path, "ZHIHU_COOKIE", cookie_header)
    os.environ["ZHIHU_COOKIE"] = cookie_header
    _set_source_login_type(config_path, "zhihu", "cookie")


async def _click_first_visible(page: Any, selectors: list[str]) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=1500):
                await locator.click(timeout=3000)
                await page.wait_for_timeout(800)
                return True
        except Exception:
            continue
    return False


async def _bring_page_to_front(page: Any) -> None:
    try:
        await page.bring_to_front()
    except Exception:
        pass
