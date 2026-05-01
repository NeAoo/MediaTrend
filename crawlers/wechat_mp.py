"""WeChat public-platform crawler."""

import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from urllib.parse import parse_qs, urlparse

from loguru import logger
from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from config.settings import (
    WECHAT_MP_ACCOUNTS,
    WECHAT_MP_ACCOUNT_DELAY_SECONDS,
    WECHAT_MP_ACTION_DELAY_SECONDS,
    WECHAT_MP_ARTICLE_DELAY_SECONDS,
    WECHAT_MP_FETCH_DETAIL_PAGE,
    WECHAT_MP_HEADLESS,
    WECHAT_MP_LOGIN_TIMEOUT_SECONDS,
    WECHAT_MP_LOOKBACK_DAYS,
    WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
    WECHAT_MP_PAGE_DELAY_SECONDS,
    WECHAT_MP_RAW_OUTPUT_DIR,
    WECHAT_MP_SLOW_MO_MS,
    WECHAT_MP_STORAGE_STATE,
)
from crawlers.base import BaseCrawler
from models.hotspot import CollectionResult, EducationHotspot


class WechatMpCrawler(BaseCrawler):
    """Collect articles from specific WeChat official accounts."""

    def __init__(self):
        super().__init__("wechat_mp")
        self.storage_state_path = Path(WECHAT_MP_STORAGE_STATE).expanduser()
        self.raw_output_dir = Path(WECHAT_MP_RAW_OUTPUT_DIR).expanduser()

    def collect(self, keywords: List[str] | None = None, time_range_hours: tuple = None) -> CollectionResult:
        accounts = keywords or WECHAT_MP_ACCOUNTS
        result = CollectionResult()

        if not accounts:
            logger.warning("未配置 WECHAT_MP_ACCOUNTS，无法采集公众号后台内容")
            return result

        logger.info("开始从微信公众号后台采集固定公众号文章...")
        logger.info(f"公众号列表: {', '.join(accounts)}")
        logger.info(f"每个公众号最多采集: {WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT} 篇")
        logger.info(f"时间范围: 最近 {WECHAT_MP_LOOKBACK_DAYS} 天")
        logger.info(
            "浏览器模式: "
            f"{'headless' if WECHAT_MP_HEADLESS else '可见'}；"
            f"slow_mo={WECHAT_MP_SLOW_MO_MS}ms；"
            f"操作延迟≈{WECHAT_MP_ACTION_DELAY_SECONDS}s，"
            f"文章延迟≈{WECHAT_MP_ARTICLE_DELAY_SECONDS}s，"
            f"翻页延迟≈{WECHAT_MP_PAGE_DELAY_SECONDS}s，"
            f"公众号间隔≈{WECHAT_MP_ACCOUNT_DELAY_SECONDS}s"
        )

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=WECHAT_MP_HEADLESS,
                    slow_mo=WECHAT_MP_SLOW_MO_MS,
                )
                context_options = {"no_viewport": True}
                if self.storage_state_path.exists():
                    context_options["storage_state"] = str(self.storage_state_path)

                context = browser.new_context(**context_options)
                page = context.new_page()
                token = self._ensure_login(page, context)
                if not token:
                    result.error_messages.append("微信公众号后台登录失败或未获取 token")
                    browser.close()
                    return result

                for account_index, account in enumerate(accounts):
                    try:
                        if account_index > 0:
                            self._pause(page, WECHAT_MP_ACCOUNT_DELAY_SECONDS)
                        items = self._collect_account(context, page, token, account)
                        result.items.extend(items)
                        result.success_count += len(items)
                        logger.info(f"{account} 采集完成: {len(items)} 篇")
                    except Exception as exc:
                        logger.error(f"采集公众号 {account} 失败: {exc}", exc_info=True)
                        result.error_messages.append(f"{account}: {exc}")

                context.storage_state(path=str(self.storage_state_path))
                browser.close()
        except Exception as exc:
            logger.error(f"微信公众号后台采集异常: {exc}", exc_info=True)
            result.error_messages.append(str(exc))

        if result.items:
            result.items.sort(key=lambda item: item.publish_time, reverse=True)
            self._save_grouped_raw_data(result.items)

        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        return EducationHotspot(
            title=raw_data.get("title", ""),
            source="微信公众号后台",
            author=raw_data.get("account"),
            publish_time=raw_data.get("publish_time", datetime.now()),
            content=raw_data.get("content") or raw_data.get("summary") or "",
            url=raw_data.get("url", ""),
            popularity=None,
            cover_image=None,
            image_list=[],
            tags=["教育", "公众号", "wechat_mp", raw_data.get("account", "")],
        )

    def _ensure_login(self, page: Page, context: BrowserContext) -> str | None:
        self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("打开微信公众平台后台；如出现登录页，请扫码登录")
        page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=60000)

        token = self._extract_token(page.url)
        if token:
            context.storage_state(path=str(self.storage_state_path))
            return token

        try:
            page.wait_for_function(
                "() => location.href.includes('token=')",
                timeout=WECHAT_MP_LOGIN_TIMEOUT_SECONDS * 1000,
            )
        except PlaywrightTimeoutError:
            logger.error("等待微信公众号后台扫码登录超时")
            return None

        token = self._extract_token(page.url)
        if token:
            context.storage_state(path=str(self.storage_state_path))
            logger.info(f"登录状态已保存: {self.storage_state_path}")
            return token

        logger.error(f"登录后未能从 URL 获取 token: {page.url}")
        return None

    def _collect_account(
        self,
        context: BrowserContext,
        page: Page,
        token: str,
        account: str,
    ) -> list[EducationHotspot]:
        self._open_account_article_picker(page, token, account)

        articles: list[EducationHotspot] = []
        while len(articles) < WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT:
            page.wait_for_selector(
                'xpath=//*[@id="vue_app"]//label[contains(@class, "inner_link_article_item")]',
                timeout=30000,
            )
            article_items = page.locator(
                'xpath=//*[@id="vue_app"]//label[contains(@class, "inner_link_article_item")]'
            )
            item_count = article_items.count()
            logger.info(f"{account} 当前页发现 {item_count} 条文章")
            if item_count == 0:
                break

            saw_recent_article = False
            for index in range(item_count):
                if len(articles) >= WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT:
                    break

                raw_item = self._read_article_item(context, account, article_items.nth(index), index + 1)
                self._pause(page, WECHAT_MP_ARTICLE_DELAY_SECONDS)
                if not raw_item:
                    continue

                publish_time = raw_item["publish_time"]
                if not self._within_lookback_days(publish_time):
                    continue

                saw_recent_article = True
                articles.append(self.parse_item(raw_item))
                logger.info(f"采集到 [{account}] {raw_item['title'][:40]}")

            if len(articles) >= WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT:
                break
            if not saw_recent_article:
                break
            if not self._go_next_page(page):
                break

        return articles

    def _open_account_article_picker(self, page: Page, token: str, account: str) -> None:
        edit_url = (
            "https://mp.weixin.qq.com/cgi-bin/appmsg?"
            "t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0"
            f"&token={token}&lang=zh_CN"
        )
        page.goto(edit_url, wait_until="domcontentloaded", timeout=60000)
        self._pause(page, WECHAT_MP_ACTION_DELAY_SECONDS)
        page.locator("#js_editor_insertlink").click(timeout=30000)
        self._pause(page, WECHAT_MP_ACTION_DELAY_SECONDS)
        page.locator("text=选择其他账号").click(timeout=30000)
        self._pause(page, WECHAT_MP_ACTION_DELAY_SECONDS)

        search_box = page.locator('xpath=//input[@placeholder="输入文章来源的账号名称或微信号，回车进行搜索"]')
        search_box.click(timeout=30000)
        self._pause(page, WECHAT_MP_ACTION_DELAY_SECONDS)
        search_box.fill(account)
        self._pause(page, WECHAT_MP_ACTION_DELAY_SECONDS)
        search_box.press("Enter")
        self._pause(page, WECHAT_MP_PAGE_DELAY_SECONDS)

        page.wait_for_selector(".inner_link_account_avatar", timeout=30000)
        page.locator(".inner_link_account_avatar").first.click()
        self._pause(page, WECHAT_MP_PAGE_DELAY_SECONDS)

    def _read_article_item(
        self,
        context: BrowserContext,
        account: str,
        item,
        index: int,
    ) -> dict | None:
        try:
            title = self._read_item_title(item)
            date_text = self._read_item_date(item)
            publish_time = self._parse_publish_time(date_text)

            url = self._read_item_url(item)
            content = ""
            if WECHAT_MP_FETCH_DETAIL_PAGE:
                detail = self._fetch_article_detail(context, url, item, index)
                if detail:
                    url = detail["url"] or url
                    content = detail["content"]

            return {
                "account": account,
                "title": title,
                "url": url,
                "publish_time": publish_time,
                "content": content,
                "summary": title,
            }
        except Exception as exc:
            logger.warning(f"解析公众号后台文章条目失败 index={index}: {exc}")
            return None

    def _read_item_title(self, item) -> str:
        title = (item.locator(".inner_link_article_span").first.text_content(timeout=5000) or "").strip()
        if title:
            return title

        row_text = item.inner_text(timeout=5000)
        title, _ = self._split_article_row_text(row_text)
        if title:
            return title

        raise ValueError("未读取到文章标题")

    def _read_item_date(self, item) -> str:
        date_text = (item.locator(".inner_link_article_date").first.text_content(timeout=5000) or "").strip()
        if date_text:
            return date_text

        row_text = item.inner_text(timeout=5000)
        _, fallback_date = self._split_article_row_text(row_text)
        if fallback_date:
            return fallback_date

        raise ValueError("未读取到文章日期")

    def _read_item_url(self, item) -> str:
        try:
            item.hover(timeout=5000)
            anchor = item.locator("a.weui-desktop-vm_default, a", has_text="查看文章").first
            return anchor.get_attribute("href", timeout=3000) or ""
        except Exception:
            return ""

    def _fetch_article_detail(self, context: BrowserContext, url: str, item, index: int) -> dict | None:
        if url:
            return self._open_article_url(context, url, index)
        return self._open_article_detail_link(context, item, index)

    def _open_article_url(self, context: BrowserContext, url: str, index: int) -> dict | None:
        new_page = context.new_page()
        try:
            new_page.goto(url, wait_until="domcontentloaded", timeout=20000)
            self._pause(new_page, WECHAT_MP_ACTION_DELAY_SECONDS)
            content = ""
            try:
                content = new_page.locator("#js_content").inner_text(timeout=10000)
            except Exception:
                logger.info(f"第 {index} 条文章详情页未读取到正文，仅保留链接")
            return {
                "url": new_page.url,
                "content": content,
            }
        except Exception as exc:
            logger.info(f"打开第 {index} 条公众号文章链接失败，保留列表信息: {exc}")
            return None
        finally:
            new_page.close()

    def _open_article_detail_link(self, context: BrowserContext, item, index: int) -> dict | None:
        try:
            item.hover(timeout=5000)
            detail_link = item.locator("a.weui-desktop-vm_default, a", has_text="查看文章").first
            if not detail_link.is_visible(timeout=3000):
                return None

            with context.expect_page(timeout=8000) as new_page_info:
                detail_link.click(timeout=5000)
            new_page = new_page_info.value
            try:
                new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                self._pause(new_page, WECHAT_MP_ACTION_DELAY_SECONDS)
                content = ""
                try:
                    content = new_page.locator("#js_content").inner_text(timeout=10000)
                except Exception:
                    logger.info(f"第 {index} 条文章详情页未读取到正文，仅保留链接")
                return {
                    "url": new_page.url,
                    "content": content,
                }
            finally:
                new_page.close()
        except Exception as exc:
            logger.info(f"打开第 {index} 条公众号文章详情失败，保留列表信息: {exc}")
            return None

    def _split_article_row_text(self, raw_text: str) -> tuple[str, str]:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        date_text = ""
        title_parts = []

        for line in lines:
            cleaned = re.sub(r"\[?查看文章\]?\([^)]+\)", "", line).replace("查看文章", "").strip()
            date_match = re.search(r"20\d{2}[-/年.]\d{1,2}[-/月.]\d{1,2}", cleaned)
            if date_match and not date_text:
                date_text = date_match.group(0)
                cleaned = cleaned.replace(date_text, "").strip()
            if cleaned:
                title_parts.append(cleaned)

        return " ".join(title_parts).strip(), date_text

    def _go_next_page(self, page: Page) -> bool:
        try:
            next_button = page.get_by_text("下一页", exact=True)
            if not next_button.is_visible(timeout=3000):
                return False
            next_button.click(timeout=5000)
            self._pause(page, WECHAT_MP_PAGE_DELAY_SECONDS)
            return True
        except Exception:
            return False

    def _pause(self, page: Page | None, seconds: float) -> None:
        if seconds <= 0:
            return

        duration = seconds * random.uniform(0.75, 1.35)
        if page is not None and not page.is_closed():
            page.wait_for_timeout(int(duration * 1000))
            return

        time.sleep(duration)

    def _within_lookback_days(self, publish_time: datetime) -> bool:
        return datetime.now() - publish_time <= timedelta(days=WECHAT_MP_LOOKBACK_DAYS)

    def _parse_publish_time(self, raw: str) -> datetime:
        text = raw.strip()
        patterns = [
            r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})\s+(\d{1,2}):(\d{1,2})",
            r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            parts = [int(part) for part in match.groups()]
            try:
                if len(parts) == 5:
                    return datetime(parts[0], parts[1], parts[2], parts[3], parts[4])
                return datetime(parts[0], parts[1], parts[2])
            except ValueError:
                continue

        if "昨天" in text:
            return datetime.now() - timedelta(days=1)
        if "今天" in text:
            return datetime.now()

        logger.debug(f"无法解析公众号后台发布时间，使用当前时间: {raw}")
        return datetime.now()

    def _extract_token(self, url: str) -> str | None:
        parsed = urlparse(url)
        token_values = parse_qs(parsed.query).get("token")
        return token_values[0] if token_values else None

    def _save_grouped_raw_data(self, items: list[EducationHotspot]) -> None:
        date_label = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        day_dir = self.raw_output_dir / date_label
        day_dir.mkdir(parents=True, exist_ok=True)

        grouped: dict[str, list[EducationHotspot]] = {}
        for item in items:
            account = item.author or "未知公众号"
            grouped.setdefault(account, []).append(item)

        summary_payload = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "wechat_mp",
                "lookback_days": WECHAT_MP_LOOKBACK_DAYS,
                "max_articles_per_account": WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
                "total_count": len(items),
                "accounts": list(grouped.keys()),
            },
            "accounts": {},
        }

        for account, account_items in grouped.items():
            account_dir = day_dir / self._safe_path_name(account)
            account_dir.mkdir(parents=True, exist_ok=True)
            articles = [self._serialize_hotspot(item) for item in account_items]
            payload = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "source": "wechat_mp",
                    "account": account,
                    "lookback_days": WECHAT_MP_LOOKBACK_DAYS,
                    "max_articles_per_account": WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
                    "total_count": len(articles),
                },
                "articles": articles,
            }

            account_file = account_dir / f"articles_{timestamp}.json"
            with open(account_file, "w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
            logger.info(f"公众号原始数据已保存: {account_file}")
            summary_payload["accounts"][account] = articles

        summary_file = day_dir / f"all_accounts_{timestamp}.json"
        with open(summary_file, "w", encoding="utf-8") as file:
            json.dump(summary_payload, file, ensure_ascii=False, indent=2)
        logger.info(f"公众号汇总原始数据已保存: {summary_file}")

    def _serialize_hotspot(self, item: EducationHotspot) -> dict:
        return {
            "title": item.title,
            "account": item.author,
            "source": item.source,
            "publish_time": item.publish_time.isoformat(),
            "content": item.content,
            "url": item.url,
            "tags": item.tags,
        }

    def _safe_path_name(self, raw_name: str) -> str:
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", raw_name).strip()
        return safe_name or "未知公众号"
