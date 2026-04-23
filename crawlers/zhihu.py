"""
知乎内容采集器
集成 TrendCrawlerRuntime 的知乎平台数据采集

知乎采集数据字段
{
  "content_id": "回答内容唯一ID",
  "content_type": "内容类型",
  "content_text": "回答正文文本内容",
  "content_url": "回答网页链接",
  "question_id": "所属问题ID",
  "title": "问题标题",
  "desc": "问题详细描述补充内容",
  "created_time": "回答发布时间（秒时间戳）",
  "updated_time": "回答最后编辑更新时间（秒时间戳）",
  "voteup_count": "回答赞同（点赞）数量",
  "comment_count": "回答评论数量",
  "source_keyword": "采集检索源关键词",
  "user_id": "回答作者用户ID",
  "user_link": "作者个人主页链接",
  "user_nickname": "作者昵称",
  "user_avatar": "作者头像图片链接",
  "user_url_token": "作者主页URL唯一标识",
  "last_modify_ts": "爬虫采集数据时间（毫秒时间戳）"
}
"""
from typing import List
from datetime import datetime
from pathlib import Path
import subprocess
import os
from loguru import logger

from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot, CollectionResult
from config.settings import KEYWORDS, TIME_RANGE_MAX


class ZhihuCrawler(BaseCrawler):
    """
    知乎采集器

    使用 TrendCrawlerRuntime 项目进行数据采集，然后转换为统一格式
    """

    def __init__(self):
        super().__init__("zhihu")
        self.trendcrawler_dir = Path("D:/AITrend/TrendCrawlerRuntime")

    def collect(self, keywords: List[str] = None,
                time_range_hours: tuple = (0, 48)) -> CollectionResult:
        """
        从知乎采集教育热点

        Args:
            keywords: 搜索关键词列表
            time_range_hours: 时间范围（最小小时，最大小时）

        Returns:
            CollectionResult: 采集结果
        """
        if keywords is None:
            keywords = KEYWORDS

        # 使用时间范围配置
        max_hours = time_range_hours[1] if isinstance(time_range_hours, tuple) else time_range_hours

        result = CollectionResult(source=self.name)

        logger.info(f"📚 开始从知乎采集教育热点...")
        logger.info(f"   关键词: {', '.join(keywords)}")
        logger.info(f"   时间范围: 最近 {max_hours} 小时")

        try:
            # Step 1: 执行爬虫采集
            success = self._run_crawler(keywords, max_hours, timeout=900)

            if not success:
                logger.error("❌ 知乎爬虫执行失败或超时")
                result.error_messages.append("爬虫执行失败或超时")
                return result

            # Step 2: 加载并转换数据
            hotspots = self._load_and_convert_data()

            result.items = hotspots
            result.success_count = len(hotspots)

            logger.info(f"✅ 知乎采集完成，共 {len(hotspots)} 条内容")

        except Exception as e:
            logger.error(f"❌ 知乎采集异常: {e}", exc_info=True)
            result.error_messages.append(str(e))

        return result

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """
        解析单条数据为标准格式
        严格按照 EducationHotspot 模型字段进行映射
        
        Args:
            raw_data: 原始数据字典
            
        Returns:
            EducationHotspot: 标准化后的热点数据
        """
        try:
            # 提取时间戳
            time_value = raw_data.get('created_time', 0) or raw_data.get('updated_time', 0)
            if time_value:
                if time_value > 1000000000000:  # 毫秒级
                    time_value = time_value / 1000
                publish_time = datetime.fromtimestamp(time_value)
            else:
                publish_time = datetime.now()
            
            # 计算热度（赞同数 + 评论数*2）
            voteup_count = int(raw_data.get('voteup_count', 0) or 0)
            comment_count = int(raw_data.get('comment_count', 0) or 0)
            popularity = float(voteup_count + comment_count * 2)
            
            # 获取标题（优先使用问题标题）
            title = raw_data.get('title', '无标题')
            
            # 获取作者（知乎使用 user_nickname 字段）
            author = raw_data.get('user_nickname', '未知作者')
            
            # 获取摘要（知乎使用 content_text 字段，其次 desc）
            content_text = raw_data.get('content_text', '') or raw_data.get('desc', '')
            
            # 提取URL（知乎使用 content_url 字段）
            url = raw_data.get('content_url', '')
            
            # 知乎通常没有图片列表和标签，设置为空
            # 如果未来知乎数据包含图片，可以在此扩展
            cover_image = None
            image_list = []
            tags = ["教育", "知乎"]  # 默认标签
            
            return EducationHotspot(
                title=title[:100],
                source="zhihu",
                author=author,
                publish_time=publish_time,
                content_summary=content_text[:500],
                url=url,
                popularity=popularity,
                cover_image=cover_image,
                image_list=image_list,
                tags=tags
            )
        except Exception as e:
            logger.warning(f"知乎数据解析失败: {e}")
            return EducationHotspot(
                title="解析失败",
                source="zhihu",
                author="未知",
                publish_time=datetime.now(),
                content_summary="",
                url="",
                popularity=0.0,
                cover_image=None,
                image_list=[],
                tags=[]
            )

    def _run_crawler(self, keywords: List[str], time_range_hours: int, timeout: int = 900) -> bool:
        """
        运行 TrendCrawlerRuntime 知乎爬虫

        Args:
            keywords: 关键词列表
            time_range_hours: 时间范围（小时）
            timeout: 超时时间（秒），默认15分钟

        Returns:
            bool: 是否成功
        """
        try:
            # 设置环境变量
            env = os.environ.copy()
            keywords_str = ",".join(keywords)
            env["TREND_CRAWLER_RUNTIME_KEYWORDS"] = keywords_str
            env["TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX"] = str(time_range_hours)
            
            # 从配置中读取每个关键词的爬取数量
            from config.settings import TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT
            env["TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT"] = str(TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT)

            logger.info(f"🔑 传递给 TrendCrawlerRuntime 的关键词: {keywords_str}")
            logger.info(f"⏰ 时间范围: {time_range_hours} 小时")
            logger.info(f"📊 每个关键词爬取数量: {TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT}")

            # 构建命令
            cmd = [
                "python", "main.py",
                "--platform", "zhihu",
                "--lt", "qrcode",
                "--type", "search"
            ]

            logger.info(f"执行 TrendCrawlerRuntime 知乎: {' '.join(cmd)}")
            logger.info(f"超时时间: {timeout} 秒 ({timeout/60:.1f} 分钟)")

            # 执行爬虫
            result = subprocess.run(
                cmd,
                cwd=self.trendcrawler_dir,
                env=env,
                capture_output=False,
                text=True,
                timeout=timeout
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error(f"知乎爬虫执行超时（{timeout/60:.1f} 分钟）")
            return False
        except Exception as e:
            logger.error(f"知乎爬虫执行异常: {e}")
            return False

    def _load_and_convert_data(self) -> List[EducationHotspot]:
        """
        加载 JSONL 数据并转换为 EducationHotspot

        Returns:
            List[EducationHotspot]: 热点列表
        """
        # 查找最新的 JSONL 文件
        jsonl_dir = self.trendcrawler_dir / "data" / "zhihu" / "jsonl"

        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []

        jsonl_files = list(jsonl_dir.glob("search_contents_*.jsonl"))

        if not jsonl_files:
            logger.error("未找到知乎 JSONL 文件")
            return []

        # 取最新的文件
        latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"使用知乎数据文件: {latest_file.name}")

        # 加载并转换数据
        hotspots = []
        try:
            import json

            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_data = json.loads(line)
                        hotspot = self.parse_item(raw_data)
                        hotspots.append(hotspot)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON解析失败: {e}")
                        continue

            logger.info(f"成功转换 {len(hotspots)} 条知乎数据")

        except Exception as e:
            logger.error(f"知乎数据转换失败: {e}", exc_info=True)

        return hotspots
