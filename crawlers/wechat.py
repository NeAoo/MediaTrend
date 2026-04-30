"""
微信公众号文章采集器
支持多种采集方式：
1. 搜狗微信搜索（使用 Playwright 浏览器，绕过反爬）
2. 详情页抓取（获取完整正文和准确时间）
"""
import asyncio
import json
import random
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from loguru import logger

from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot, CollectionResult
from config.settings import (
    SOGOU_WECHAT_COOKIE,
    TIME_RANGE_MAX,
    TIME_RANGE_MIN,
    WECHAT_FETCH_DETAIL_PAGE,
    WECHAT_MAX_RESULTS_PER_KEYWORD,
    WECHAT_USE_PLAYWRIGHT,
)


class WechatCrawler(BaseCrawler):
    """微信公众号采集器"""

    def __init__(self):
        super().__init__("wechat")
        self.session = requests.Session()

        # 配置请求头，模拟浏览器（用于详情页访问）
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })

        self.sogou_cookie = SOGOU_WECHAT_COOKIE
        if self.sogou_cookie:
            logger.info("已加载搜狗微信 Cookie")

        # 代理配置（可选）
        self.proxy = None

        # 请求延迟配置（秒）
        self.request_delay = (3, 5)

        # 浏览器实例缓存（避免重复启动）
        self._browser_instance = None
        self._browser_context = None

        # 配置选项
        self.config = {
            "fetch_detail_page": WECHAT_FETCH_DETAIL_PAGE,
            "use_playwright": WECHAT_USE_PLAYWRIGHT,
        }

    def collect(self, keywords: List[str] = None, time_range_hours: tuple = None) -> CollectionResult:
        """
        采集公众号教育热点文章

        Args:
            keywords: 教育相关关键词（如果为None，由Manager传入）
            time_range_hours: 时间范围 (最小小时数, 最大小时数)，默认从settings读取

        Returns:
            CollectionResult: 采集结果
        """
        # 如果没有传入时间范围，从配置文件读取
        if time_range_hours is None:
            from config.settings import TIME_RANGE_MIN, TIME_RANGE_MAX
            time_range_hours = (TIME_RANGE_MIN, TIME_RANGE_MAX)

        result = CollectionResult()

        if not keywords:
            logger.warning("未提供关键词，无法采集")
            return result

        logger.info(f"准备搜索 {len(keywords)} 个关键词")
        logger.info(f"时间范围: {time_range_hours[0]}-{time_range_hours[1]} 小时")

        for keyword in keywords:
            try:
                logger.info(f"正在搜索公众号关键词: {keyword}")

                items = self._search_sogou_wechat(
                    keyword,
                    max_results=WECHAT_MAX_RESULTS_PER_KEYWORD,
                )

                if not items:
                    logger.warning(f"关键词 '{keyword}' 未获取到数据")
                    continue

                keyword_success = 0
                for item in items:
                    try:
                        # 先快速解析基本信息
                        hotspot = self.parse_item(item)

                        # 如果需要精确时间，访问详情页
                        if self.config.get("fetch_detail_page", False) and hotspot.url:
                            logger.debug(f"正在获取详情页时间: {hotspot.title[:30]}...")
                            detail_time = self._fetch_article_detail_time(hotspot.url)
                            if detail_time:
                                hotspot.publish_time = detail_time
                                logger.debug(f"详情页时间: {detail_time}")
                            else:
                                logger.debug(f"未能获取详情页时间，使用搜索结果时间")

                        # 验证时间范围
                        if self.validate_time_range(
                            hotspot.publish_time,
                            time_range_hours[0],
                            time_range_hours[1]
                        ):
                            result.items.append(hotspot)
                            result.success_count += 1
                            keyword_success += 1
                            time_diff = (datetime.now() - hotspot.publish_time).total_seconds() / 3600
                            logger.info(f"✓ 成功采集: {hotspot.title[:30]}... (距今 {time_diff:.1f} 小时)")
                        else:
                            time_diff = (datetime.now() - hotspot.publish_time).total_seconds() / 3600
                            logger.debug(f"✗ 时间不符合: {hotspot.title[:30]}... (距今 {time_diff:.1f}h)")

                    except Exception as e:
                        logger.error(f"解析公众号文章失败: {e}")
                        result.failed_count += 1
                        result.error_messages.append(str(e))

                # 如果这个关键词找到了足够多的文章，继续下一个
                if keyword_success >= 5:
                    logger.info(f"关键词 '{keyword}' 已找到 {keyword_success} 篇，继续下一个")

                # 随机延迟，避免被封
                delay = random.uniform(*self.request_delay)
                logger.debug(f"等待 {delay:.1f} 秒...")
                time.sleep(delay)

            except Exception as e:
                logger.error(f"搜索关键词 {keyword} 失败: {e}")
                result.error_messages.append(f"关键词 {keyword}: {str(e)}")

                # 遇到错误时增加延迟
                time.sleep(5)

        logger.info(f"公众号采集完成: 成功{result.success_count}, 失败{result.failed_count}")

        # 按发布时间倒序排列（最新的在前）
        if result.items:
            result.items.sort(key=lambda x: x.publish_time, reverse=True)
            logger.info(f"已按时间倒序排列，最新文章: {result.items[0].title[:30]}...")

        # 保存原始数据到文件
        self._save_raw_data(result.items, keyword_list=keywords)

        return result

    def _save_raw_data(self, items: List[EducationHotspot], keyword_list: List[str]):
        """
        保存微信爬虫的原始数据到JSON文件

        Args:
            items: 采集到的热点列表
            keyword_list: 使用的关键词列表
        """
        if not items:
            logger.warning("没有数据需要保存")
            return

        try:
            from pathlib import Path
            import json

            # 创建输出目录
            output_dir = Path("./raw_data/wechat")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"wechat_raw_{timestamp}.json"

            # 转换为可序列化的格式
            raw_data = []
            for idx, item in enumerate(items, 1):
                raw_data.append({
                    "rank": idx,
                    "title": item.title,
                    "source": item.source,
                    "author": item.author,
                    "publish_time": item.publish_time.isoformat(),
                    "content_summary": item.content_summary,
                    "url": item.url,
                    "popularity": item.popularity,
                    "tags": item.tags,
                    "cover_image": item.cover_image,
                    "image_list": item.image_list
                })

            # 添加元信息
            output_content = {
                "metadata": {
                    "source": "wechat",
                    "crawl_time": datetime.now().isoformat(),
                    "keywords": keyword_list,
                    "time_range_hours": [TIME_RANGE_MIN, TIME_RANGE_MAX],
                    "total_count": len(items)
                },
                "data": raw_data
            }

            # 保存为JSON文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_content, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 微信原始数据已保存: {output_file}")

        except Exception as e:
            logger.error(f"保存微信原始数据失败: {e}", exc_info=True)

    def _search_sogou_wechat(self, keyword: str, max_results: int = 5) -> List[dict]:
        """
        使用搜狗微信搜索公众号文章
        
        Args:
            keyword: 搜索关键词
            max_results: 最大返回结果数
            
        Returns:
            List[dict]: 文章数据列表
        """
        try:
            if self.config.get("use_playwright", False):
                logger.info(f"使用 Playwright 浏览器搜索：{keyword}")
                articles = self._search_with_playwright(keyword, max_results)
                if articles:
                    return articles
                logger.warning("Playwright 未返回结果，回退到 requests 搜索")

            logger.info(f"使用 requests 搜索：{keyword}")
            return self._search_with_requests(keyword, max_results)
        except Exception as e:
            logger.error(f"搜索失败：{e}", exc_info=True)
            return []

    def _search_with_playwright(self, keyword: str, max_results: int = 5) -> List[dict]:
        """使用 Playwright 浏览器搜索（绕过反爬）"""
        try:
            from playwright.sync_api import sync_playwright
            
            articles = []
            
            with sync_playwright() as p:
                # 启动浏览器
                logger.debug("启动 Chromium 浏览器...")
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                # 创建上下文
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="zh-CN",
                    viewport={"width": 1920, "height": 1080}
                )
                
                # 设置 Cookie
                if self.sogou_cookie:
                    cookies = self._parse_cookie_string(self.sogou_cookie)
                    if cookies:
                        context.add_cookies(cookies)
                        logger.debug(f"已设置 {len(cookies)} 个 Cookie")
                
                # 创建页面
                page = context.new_page()
                
                # 访问搜狗微信搜索
                search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}&page=1"
                logger.debug(f"访问：{search_url}")
                
                try:
                    page.goto(search_url, wait_until="networkidle", timeout=15000)
                except Exception as e:
                    logger.warning(f"页面加载超时，尝试继续：{e}")
                
                # 等待搜索结果加载
                time.sleep(2)
                
                # 检查是否被拦截
                html = page.content()
                if "验证码" in html or "antispider" in html:
                    logger.warning("⚠ Playwright 也触发验证码，可能需要手动验证")
                    # 保存页面用于调试
                    with open("sogou_blocked_playwright.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    browser.close()
                    return []
                
                logger.debug(f"获取 HTML 成功，长度：{len(html)}")
                
                # 解析 HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找文章列表
                news_items = soup.find_all('div', class_='txt-box')
                if not news_items:
                    news_items = soup.find_all('li', class_='fw-item')
                
                logger.info(f"找到 {len(news_items)} 个搜索结果")
                
                # 解析每篇文章
                for i, item in enumerate(news_items[:max_results]):
                    try:
                        article_data = self._parse_sogou_result(item, keyword)
                        if article_data:
                            articles.append(article_data)
                    except Exception as e:
                        logger.debug(f"解析第{i+1}条结果失败：{e}")
                        continue
                
                logger.info(f"成功解析 {len(articles)} 篇文章")
                
                # 关闭浏览器
                browser.close()
            
            return articles
            
        except ImportError:
            logger.error("Playwright 未安装，请运行：pip install playwright")
            return []
        except Exception as e:
            logger.error(f"Playwright 搜索失败：{e}", exc_info=True)
            return []

    def _search_with_requests(self, keyword: str, max_results: int = 5) -> List[dict]:
        """使用 requests 搜索（传统方式，容易被反爬）"""
        articles = []
        
        try:
            # 搜狗微信搜索 URL
            base_url = "https://weixin.sogou.com/weixin"
            
            params = {
                "type": "2",      # 2 表示搜索文章
                "query": keyword,
                "page": 1,
            }
            
            logger.debug(f"搜索 URL: {base_url}, 参数：{params}")
            
            response = self.session.get(
                base_url, 
                params=params, 
                timeout=10,
                proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None
            )
            
            if response.status_code != 200:
                logger.error(f"请求失败：{response.status_code}")
                return articles
            
            # 检查是否被反爬
            if "验证码" in response.text or "antispider" in response.text:
                logger.warning("触发搜狗反爬验证，需要人工验证或更换 IP")
                with open("sogou_blocked.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.warning("已保存拦截页面到 sogou_blocked.html")
                return articles
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找文章列表
            news_items = soup.find_all('div', class_='txt-box')
            if not news_items:
                news_items = soup.find_all('li', class_='fw-item')
            
            logger.info(f"找到 {len(news_items)} 个搜索结果")
            
            # 解析每篇文章
            for i, item in enumerate(news_items[:max_results]):
                try:
                    article_data = self._parse_sogou_result(item, keyword)
                    if article_data:
                        articles.append(article_data)
                except Exception as e:
                    logger.debug(f"解析第{i+1}条结果失败：{e}")
                    continue
            
            logger.info(f"成功解析 {len(articles)} 篇文章")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败：{e}")
        except Exception as e:
            logger.error(f"搜狗搜索失败：{e}", exc_info=True)
        
        return articles

    def _parse_cookie_string(self, cookie_str: str) -> List[Dict]:
        """解析 Cookie 字符串为 Playwright 格式"""
        if not cookie_str:
            return []
        
        cookies = []
        cookie_pairs = cookie_str.split(';')
        
        for pair in cookie_pairs:
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.sogou.com',
                    'path': '/'
                })
        
        return cookies

    def _parse_sogou_result(self, item, keyword: str) -> Optional[dict]:
        """
        解析搜狗搜索结果中的单篇文章

        Args:
            item: BeautifulSoup元素
            keyword: 搜索关键词

        Returns:
            dict: 文章数据，失败返回None
        """
        try:
            # 提取标题和链接
            # 方法1: 查找 h3 标签内的 a 标签
            h3_tag = item.find('h3')
            title_tag = None
            if h3_tag:
                title_tag = h3_tag.find('a', href=True)

            # 方法2: 如果没找到，尝试直接查找带href的a标签
            if not title_tag:
                title_tag = item.find('a', href=True, target='_blank')

            # 方法3: 最后的备选
            if not title_tag:
                title_tag = item.find('a', href=True)

            if not title_tag:
                logger.debug("未找到带href的链接标签")
                return None

            title = title_tag.get_text(strip=True)
            raw_url = title_tag.get('href', '')

            logger.debug(f"找到链接标签，原始URL: {raw_url[:100] if raw_url else 'None'}")

            # 清理标题
            title = re.sub(r'<[^>]+>', '', title)  # 移除HTML标签
            title = re.sub(r'\s+', ' ', title).strip()  # 清理空白

            if not title or len(title) < 5:
                return None

            # 处理搜狗代理链接，提取真实URL
            url = ""
            if raw_url:
                url = self._extract_real_wechat_url(raw_url)
                logger.debug(f"提取后URL: {url[:100] if url else 'None'}")
            else:
                logger.warning("原始URL为空")

            # 提取摘要（优先从详情页获取）
            summary = ""

            # 尝试从详情页获取完整内容
            if url and self.config.get("fetch_detail_page", False):
                detail_content = self._fetch_article_detail_content(url)
                if detail_content:
                    summary = detail_content[:800]  # 取前800字作为摘要
                    logger.debug(f"从详情页获取摘要: {len(summary)}字")

            # 如果详情页获取失败，使用搜索结果摘要
            if not summary:
                summary_tag = item.find('p', class_='txt-info') or item.find('p')
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                logger.debug(f"使用搜索结果摘要: {len(summary)}字")

            # 提取发布时间
            publish_time = self._extract_publish_time(item)

            # 提取公众号名称
            account_name = self._extract_account_name(item)

            # 提取阅读量（如果有）
            read_count = self._extract_read_count(item)

            # 调试日志：输出解析到的时间信息
            logger.debug(f"文章: {title[:30]}... | 时间: {publish_time} | 作者: {account_name}")
            logger.debug(f"最终URL: {url[:80] if url else 'None'}")

            return {
                "title": title[:200],
                "url": url,
                "summary": summary[:800] if summary else title,  # 增加到800字
                "publish_time": publish_time,
                "author": account_name,
                "read_count": read_count,
                "source_keyword": keyword
            }

        except Exception as e:
            logger.debug(f"解析搜狗结果失败: {e}", exc_info=True)
            return None

    def _extract_real_wechat_url(self, sogou_url: str) -> str:
        """
        从搜狗代理链接中提取真实的微信文章URL

        Args:
            sogou_url: 搜狗代理链接，如 /link?url=xxx

        Returns:
            str: 真实的微信文章URL
        """
        if not sogou_url:
            return ""

        try:
            # 如果已经是mp.weixin.qq.com链接，直接返回
            if "mp.weixin.qq.com" in sogou_url:
                return sogou_url

            # 如果是相对路径，先转换为绝对路径
            if sogou_url.startswith('/'):
                sogou_url = f"https://weixin.sogou.com{sogou_url}"

            # 尝试从查询参数中提取url参数
            from urllib.parse import urlparse, parse_qs, unquote

            parsed = urlparse(sogou_url)
            query_params = parse_qs(parsed.query)

            # 尝试从url参数中获取真实链接
            if 'url' in query_params:
                real_url = query_params['url'][0]
                # URL解码
                real_url = unquote(real_url)

                logger.debug(f"从参数提取的URL: {real_url[:100]}")

                # 验证是否是微信文章链接
                if "mp.weixin.qq.com" in real_url:
                    logger.debug(f"✓ 提取到真实URL")
                    return real_url

            # 如果参数提取失败，尝试访问链接获取重定向后的URL
            logger.debug("尝试访问搜狗链接获取重定向...")
            response = self.session.get(sogou_url, timeout=5, allow_redirects=False)

            # 检查是否有Location头（重定向）
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location', '')
                if redirect_url and "mp.weixin.qq.com" in redirect_url:
                    logger.debug(f"✓ 从重定向获取URL: {redirect_url[:80]}")
                    return redirect_url

            # 如果没有重定向，返回原始链接（让Camoufox去访问）
            logger.debug("⚠ 无法提取真实URL，使用搜狗代理链接")
            return sogou_url

        except Exception as e:
            logger.debug(f"提取真实URL失败: {e}")
            return sogou_url

    def _extract_publish_time(self, item) -> datetime:
        """
        从搜索结果中提取发布时间

        Args:
            item: BeautifulSoup元素

        Returns:
            datetime: 发布时间
        """
        try:
            # 方法1: 查找 span.s2 中的时间戳（JavaScript timeConvert）
            time_tag = item.find('span', class_='s2')
            if time_tag:
                # 提取 script 标签中的时间戳
                script_tag = time_tag.find('script')
                if script_tag:
                    script_content = script_tag.string or script_tag.get_text()
                    # 匹配 timeConvert('1776782340') 或 timeConvert("1776782340")
                    match = re.search(r"timeConvert\(['\"](\d+)['\"]\)", script_content)
                    if match:
                        timestamp = int(match.group(1))
                        result = datetime.fromtimestamp(timestamp)
                        logger.debug(f"从时间戳解析成功: {result} (timestamp: {timestamp})")
                        return result

                    logger.debug(f"Script内容: {script_content[:100]}")

            # 方法2: 在整个item中搜索时间戳模式（备用方案）
            html_str = str(item)
            timestamp_match = re.search(r"timeConvert\(['\"](\d{10,13})['\"]\)", html_str)
            if timestamp_match:
                timestamp = int(timestamp_match.group(1))
                # 处理毫秒级时间戳
                if timestamp > 1e12:
                    timestamp = timestamp / 1000
                result = datetime.fromtimestamp(timestamp)
                logger.debug(f"从HTML中提取时间戳成功: {result}")
                return result

            # 方法3: 查找其他可能的时间显示方式
            for selector in [
                {'class_': 'post-date'},
                {'class_': 'time'},
                {'class_': 'date'},
            ]:
                time_tag = item.find('span', **selector)
                if time_tag:
                    time_text = time_tag.get_text(strip=True)

                    # 尝试解析各种格式
                    if time_text:
                        # 格式1: "2024-01-15"
                        match = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', time_text)
                        if match:
                            year, month, day = match.groups()
                            try:
                                result = datetime(int(year), int(month), int(day))
                                logger.debug(f"解析成功(日期格式): {result}")
                                return result
                            except:
                                continue

                        # 格式2: "昨天", "今天"
                        if '今天' in time_text:
                            logger.debug("解析成功(今天)")
                            return datetime.now()
                        elif '昨天' in time_text:
                            logger.debug("解析成功(昨天)")
                            return datetime.now() - timedelta(days=1)

                        # 格式3: "X小时前"
                        match = re.search(r'(\d+)\s*小时前', time_text)
                        if match:
                            hours_ago = int(match.group(1))
                            result = datetime.now() - timedelta(hours=hours_ago)
                            logger.debug(f"解析成功({hours_ago}小时前): {result}")
                            return result

                        # 格式4: "X天前"
                        match = re.search(r'(\d+)\s*天前', time_text)
                        if match:
                            days_ago = int(match.group(1))
                            result = datetime.now() - timedelta(days=days_ago)
                            logger.debug(f"解析成功({days_ago}天前): {result}")
                            return result

            # 如果所有方法都失败，使用默认时间（假设为24小时前）
            logger.warning(f"无法解析时间，使用默认值(24小时前)。HTML片段: {str(item)[:200]}")
            return datetime.now() - timedelta(hours=24)

        except Exception as e:
            logger.error(f"提取发布时间失败: {e}", exc_info=True)
            return datetime.now() - timedelta(hours=24)

    def _extract_account_name(self, item) -> Optional[str]:
        """
        提取公众号名称

        Args:
            item: BeautifulSoup元素

        Returns:
            str: 公众号名称
        """
        try:
            # 根据诊断结果，公众号名称在 class="all-time-y2" 的span中
            account_tag = item.find('span', class_='all-time-y2')

            if account_tag:
                name = account_tag.get_text(strip=True)
                # 清理可能的数字后缀（如 "智慧的母亲3798" -> "智慧的母亲"）
                # 但有些公众号名本身就包含数字，所以谨慎处理
                return name if name else None

            # 备用方案：查找其他可能的标签
            account_tag = item.find('a', class_='account') or item.find('span', class_='account')
            if account_tag:
                return account_tag.get_text(strip=True)

            # 尝试其他方式
            account_tag = item.find('a', href=re.compile(r'profile\.ext'))
            if account_tag:
                return account_tag.get_text(strip=True)

            return None

        except Exception as e:
            logger.debug(f"提取公众号名称失败: {e}")
            return None

    def _extract_read_count(self, item) -> Optional[int]:
        """
        提取阅读量（搜狗搜索结果中可能不显示）

        Args:
            item: BeautifulSoup元素

        Returns:
            int: 阅读量
        """
        try:
            # 搜狗搜索结果通常不显示阅读量
            # 如果需要，可以访问文章详情页获取
            return None
        except:
            return None

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """
        解析公众号文章数据为标准模型

        Args:
            raw_data: 原始文章数据

        Returns:
            EducationHotspot: 标准化热点对象
        """
        # 计算热度分数（基于阅读量或其他指标）
        read_count = raw_data.get("read_count")
        popularity = float(read_count) if read_count else None

        # 构建标签
        tags = ["教育", "公众号"]
        if raw_data.get("source_keyword"):
            tags.append(raw_data["source_keyword"])

        # 获取摘要（支持更长的内容）
        summary = raw_data.get("summary", "")
        if len(summary) > 500:
            # 如果摘要超过500字，截取并添加省略号
            content_summary = summary[:500] + "..."
        else:
            content_summary = summary

        return EducationHotspot(
            title=raw_data.get("title", ""),
            source="微信公众号",
            author=raw_data.get("author"),
            publish_time=raw_data.get("publish_time", datetime.now()),
            content_summary=content_summary,
            url=raw_data.get("url", ""),
            popularity=popularity,
            tags=tags
        )

    def _fetch_article_detail_content(self, url: str) -> Optional[str]:
        """
        访问文章详情页获取完整正文
        
        Args:
            url: 文章URL
            
        Returns:
            str: 正文内容，失败返回None
        """
        if not url:
            return None
        
        try:
            # 使用 Playwright 访问详情页
            if self.config.get("use_playwright", False):
                return self._fetch_detail_with_playwright(url)
            else:
                return self._fetch_detail_with_requests(url)
            
        except Exception as e:
            logger.debug(f"获取详情页正文失败：{e}")
            return None

    def _fetch_detail_with_playwright(self, url: str) -> Optional[str]:
        """使用 Playwright 访问详情页（绕过反爬）"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="zh-CN"
                )
                
                page = context.new_page()
                
                # 访问详情页
                logger.debug(f"Playwright 访问详情页：{url[:80]}...")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)
                except Exception as e:
                    logger.debug(f"页面加载超时：{e}")
                
                # 等待内容加载
                time.sleep(2)
                
                # 获取 HTML
                html = page.content()
                browser.close()
                
                # 检查是否被拦截
                if "验证码" in html or "antispider" in html:
                    logger.warning("⚠ 详情页触发反爬验证")
                    return None
                
                # 解析正文
                return self._extract_content_from_html(html)
                
        except Exception as e:
            logger.debug(f"Playwright 访问详情页失败：{e}")
            return None

    def _fetch_detail_with_requests(self, url: str) -> Optional[str]:
        """使用 requests 访问详情页（传统方式）"""
        # 随机延迟
        delay = random.uniform(3, 6)
        time.sleep(delay)
        
        try:
            if "weixin.sogou.com" not in url and "mp.weixin.qq.com" not in url:
                logger.debug(f"非微信文章链接：{url}")
                return None
            
            response = self.session.get(url, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # 检查是否被拦截
            if "验证码" in html or "antispider" in html or "security_check" in html:
                logger.warning("⚠ 详情页触发反爬验证，跳过此文章")
                with open("sogou_blocked_detail.html", "w", encoding="utf-8") as f:
                    f.write(html)
                return None
            
            return self._extract_content_from_html(html)
            
        except Exception as e:
            logger.debug(f"Requests 访问失败：{e}")
            return None

    def _extract_content_from_html(self, html: str) -> Optional[str]:
        """从 HTML 中提取正文内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 方法1: 查找微信文章正文容器
            content_div = soup.find('div', id='js_content') or soup.find('div', class_='rich_media_content')
            
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                clean_text = '\n'.join(lines)
                
                if len(clean_text) > 100:
                    logger.debug(f"✓ 成功提取正文：{len(clean_text)}字")
                    return clean_text[:800]  # 取前 800 字
            
            # 方法2: 查找所有段落
            paragraphs = soup.find_all('p')
            if paragraphs:
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
                full_text = '\n'.join(texts)
                
                if len(full_text) > 100:
                    logger.debug(f"✓ 从段落提取正文：{len(full_text)}字")
                    return full_text
            
            return None
            
        except Exception as e:
            logger.debug(f"提取正文失败：{e}")
            return None

    def _fetch_article_detail_time(self, url: str) -> Optional[datetime]:
        """
        访问文章详情页获取准确的发布时间

        Args:
            url: 文章URL（可以是搜狗代理链接或微信直链）

        Returns:
            datetime: 发布时间，失败返回None
        """
        if not url:
            return None

        try:
            # 接受搜狗代理链接或微信直链
            if "weixin.sogou.com" not in url and "mp.weixin.qq.com" not in url:
                logger.debug(f"非微信文章链接: {url}")
                return None

            # 如果配置使用Camoufox
            if self.config.get("use_camoufox", False):
                return self._fetch_with_camoufox(url)
            else:
                # 使用普通requests（可能被拦截）
                return self._fetch_with_requests(url)

        except Exception as e:
            logger.debug(f"获取详情页时间失败: {e}")
            return None

    def _fetch_with_requests(self, url: str) -> Optional[datetime]:
        """使用requests访问详情页"""
        # 随机延迟
        delay = random.uniform(3, 6)
        time.sleep(delay)

        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                logger.debug(f"详情页请求失败: {response.status_code}")
                return None

            html = response.text

            # 检查是否被拦截
            if "验证码" in html or "security_check" in html or "antispider" in html:
                logger.warning("⚠ 详情页触发验证码，跳过")
                return None

            return self._extract_time_from_html(html)

        except Exception as e:
            logger.debug(f"Requests访问失败: {e}")
            return None

    def _fetch_with_camoufox(self, url: str) -> Optional[datetime]:
        """使用Camoufox浏览器访问详情页（同步包装）"""
        try:
            # 运行异步函数
            return asyncio.run(self._async_fetch_with_camoufox(url))
        except Exception as e:
            logger.warning(f"Camoufox访问失败，回退到requests: {e}")
            return self._fetch_with_requests(url)

    async def _async_fetch_with_camoufox(self, url: str) -> Optional[datetime]:
        """使用Camoufox浏览器访问详情页（异步实现）"""
        try:
            from camoufox.async_api import AsyncCamoufox

            logger.debug("启动Camoufox浏览器...")
            # 禁用addon加载，避免manifest.json错误
            async with AsyncCamoufox(headless=True, addons=[]) as browser:
                page = await browser.new_page()

                # 设置超时
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                # 等待正文加载
                try:
                    await page.wait_for_selector("#js_content", timeout=5000)
                except Exception:
                    logger.debug("未找到#js_content，继续尝试")

                # 额外等待确保JS执行完毕
                await asyncio.sleep(2)

                # 获取页面HTML
                html = await page.content()
                logger.debug(f"Camoufox获取HTML成功，长度: {len(html)}")

            return self._extract_time_from_html(html)

        except ImportError as e:
            logger.error(f"Camoufox未正确安装: {e}")
            raise
        except Exception as e:
            logger.debug(f"Camoufox访问失败: {e}")
            raise

    def _extract_time_from_html(self, html: str) -> Optional[datetime]:
        """从HTML中提取发布时间"""
        try:
            # 方法1: JsDecode格式 (create_time : JsDecode('1776782340'))
            match = re.search(r"create_time\s*:\s*JsDecode\(['\"](\d+)['\"]\)", html)
            if match:
                timestamp = int(match.group(1))
                result = datetime.fromtimestamp(timestamp)
                logger.debug(f"✓ 从JsDecode提取时间: {result}")
                return result

            # 方法2: 纯数字格式 (create_time : '1776782340' 或 create_time = 1776782340)
            match = re.search(r"create_time\s*[:=]\s*['\"]?(\d{10,13})['\"]?", html)
            if match:
                timestamp = int(match.group(1))
                # 处理毫秒级时间戳
                if timestamp > 1e12:
                    timestamp = timestamp / 1000
                result = datetime.fromtimestamp(timestamp)
                logger.debug(f"✓ 从时间戳提取时间: {result}")
                return result

            # 方法3: meta标签
            soup = BeautifulSoup(html, 'html.parser')
            meta_time = soup.find('meta', property='article:published_time')
            if meta_time:
                time_str = meta_time.get('content', '')
                if time_str:
                    try:
                        if 'T' in time_str:
                            result = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            logger.debug(f"✓ 从meta标签提取时间: {result}")
                            return result
                        else:
                            result = datetime.strptime(time_str, '%Y-%m-%d')
                            logger.debug(f"✓ 从meta标签提取日期: {result}")
                            return result
                    except Exception as e:
                        logger.debug(f"解析meta时间失败: {e}")

            # 方法4: 查找常见的发布时间元素
            for selector in [
                {'id': 'publish_time'},
                {'class_': 'rich_media_meta_text'},
                {'class_': 'post-date'},
            ]:
                time_elem = soup.find(**selector)
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    match = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', time_text)
                    if match:
                        year, month, day = match.groups()
                        try:
                            result = datetime(int(year), int(month), int(day))
                            logger.debug(f"✓ 从页面元素提取时间: {result}")
                            return result
                        except:
                            continue

            logger.debug("⚠ 未能从HTML中提取时间")
            return None

        except Exception as e:
            logger.debug(f"✗ 解析HTML时间失败: {e}")
            return None

    def set_proxy(self, proxy_url: str):
        """
        设置代理

        Args:
            proxy_url: 代理地址，如 "http://ip:port"
        """
        self.proxy = proxy_url
        logger.info(f"已设置代理: {proxy_url}")

    def set_request_delay(self, min_delay: float, max_delay: float):
        """
        设置请求延迟范围

        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self.request_delay = (min_delay, max_delay)
        logger.info(f"请求延迟设置为: {min_delay}-{max_delay} 秒")
