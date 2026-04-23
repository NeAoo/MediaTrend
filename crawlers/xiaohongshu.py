"""
小红书内容采集器
集成 MediaCrawler 的 Pipeline 到统一的采集框架

小红书采集数据字段
{
  "note_id": "笔记唯一ID",
  "type": "笔记类型",
  "title": "笔记标题",
  "desc": "笔记正文描述与话题标签",
  "video_url": "视频资源链接",
  "time": "笔记发布时间（毫秒时间戳）",
  "last_update_time": "笔记最后更新时间（毫秒时间戳）",
  "user_id": "发布作者用户ID",
  "nickname": "作者昵称",
  "avatar": "作者头像图片链接",
  "liked_count": "笔记点赞数量",
  "collected_count": "笔记收藏数量",
  "comment_count": "笔记评论数量",
  "share_count": "笔记分享数量",
  "ip_location": "发布IP属地",
  "image_list": "笔记配图链接集合（多图逗号分隔）",
  "tag_list": "笔记话题标签列表（逗号分隔）",
  "last_modify_ts": "爬虫采集数据时间（毫秒时间戳）",
  "note_url": "笔记网页原生链接",
  "source_keyword": "采集检索源关键词",
  "xsec_token": "小红书页面鉴权访问令牌"
}
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import subprocess
import os
import json
from loguru import logger

from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot, CollectionResult
from config.settings import KEYWORDS, TIME_RANGE_MAX


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书采集器
    
    使用 MediaCrawler 项目进行数据采集，然后转换为统一格式
    """
    
    def __init__(self):
        super().__init__("xiaohongshu")
        self.mediacrawler_dir = Path("D:/AITrend/MediaCrawler")
        
    def collect(self, keywords: List[str] = None, 
                time_range_hours: tuple = (0, 48)) -> CollectionResult:
        """
        从小红书采集教育热点
        
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
        
        logger.info(f"📱 开始从小红书采集教育热点...")
        logger.info(f"   关键词: {', '.join(keywords)}")
        logger.info(f"   时间范围: 最近 {max_hours} 小时")
        
        try:
            # Step 1: 执行爬虫采集（增加超时时间到15分钟）
            success = self._run_crawler(keywords, max_hours, timeout=900)
            
            if not success:
                logger.error("❌ 小红书爬虫执行失败或超时")
                result.error_messages.append("爬虫执行失败或超时")
                return result
            
            # Step 2: 加载并转换数据
            hotspots = self._load_and_convert_data()
            
            result.items = hotspots
            result.success_count = len(hotspots)
            
            logger.info(f"✅ 小红书采集完成，共 {len(hotspots)} 条内容")
            
        except Exception as e:
            logger.error(f"❌ 小红书采集异常: {e}", exc_info=True)
            result.error_messages.append(str(e))
        
        return result
    
    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """
        解析单条小红书数据为标准格式
        
        Args:
            raw_data: 原始数据字典
            
        Returns:
            EducationHotspot: 标准化后的热点数据
        """
        try:
            # 提取时间戳并转换
            time_value = raw_data.get('time', 0)
            if time_value:
                # 处理毫秒级时间戳
                if time_value > 1000000000000:
                    time_value = time_value / 1000
                publish_time = datetime.fromtimestamp(time_value)
            else:
                publish_time = datetime.now()
            
            # 解析完整图片列表
            image_list = self._parse_image_list(raw_data.get('image_list', ''))
            
            # 构建热点对象
            hotspot = EducationHotspot(
                title=raw_data.get('title', '无标题'),
                source='xiaohongshu',
                author=raw_data.get('nickname', '未知作者'),
                publish_time=publish_time,
                content_summary=raw_data.get('desc', '')[:500],
                url=raw_data.get('note_url', ''),
                popularity=float(raw_data.get('liked_count', 0) or 0),
                cover_image=self._extract_first_image(raw_data.get('image_list', '')),
                image_list=image_list,
                tags=self._parse_tags(raw_data.get('tag_list', ''))
            )
            
            return hotspot
            
        except Exception as e:
            logger.warning(f"小红书数据解析失败: {e}, 数据ID: {raw_data.get('note_id', 'unknown')}")
            # 返回默认对象
            return EducationHotspot(
                title=raw_data.get("title", "未知标题"),
                source="xiaohongshu",
                author=raw_data.get("nickname", "未知作者"),
                publish_time=datetime.now(),
                content_summary=raw_data.get("desc", "")[:300],
                url=raw_data.get("note_url", ""),
                popularity=float(raw_data.get("liked_count", 0) or 0),
                tags=[]
            )
    
    def _extract_first_image(self, image_list_str: str) -> Optional[str]:
        """从图片列表字符串中提取第一张图片URL"""
        if not image_list_str:
            return None
        
        try:
            urls = image_list_str.split(',')
            return urls[0].strip() if urls else None
        except Exception:
            return None
    
    def _parse_image_list(self, image_list_str: str) -> List[str]:
        """解析完整图片列表"""
        if not image_list_str:
            return []
        
        try:
            urls = [url.strip() for url in image_list_str.split(',') if url.strip()]
            return urls
        except Exception:
            return []
    
    def _parse_tags(self, tag_list_str: str) -> List[str]:
        """解析标签列表"""
        if not tag_list_str:
            return []
        
        try:
            return [tag.strip() for tag in tag_list_str.split(',') if tag.strip()]
        except Exception:
            return []
    
    def _run_crawler(self, keywords: List[str], time_range_hours: int, timeout: int = 900) -> bool:
        """
        运行 MediaCrawler 爬虫
        
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
            env["MEDIA_CRAWLER_KEYWORDS"] = keywords_str
            env["MEDIA_CRAWLER_TIME_RANGE_MAX"] = str(time_range_hours)
            
            # 从配置中读取每个关键词的爬取数量
            from config.settings import MEDIA_CRAWLER_MAX_NOTES_COUNT
            env["MEDIA_CRAWLER_MAX_NOTES_COUNT"] = str(MEDIA_CRAWLER_MAX_NOTES_COUNT)
            
            logger.info(f"🔑 传递给 MediaCrawler 的关键词: {keywords_str}")
            logger.info(f"⏰ 时间范围: {time_range_hours} 小时")
            logger.info(f"📊 每个关键词爬取数量: {MEDIA_CRAWLER_MAX_NOTES_COUNT}")
            
            # 构建命令
            cmd = [
                "uv", "run", "main.py",
                "--platform", "xhs",
                "--lt", "qrcode",
                "--type", "search"
            ]
            
            logger.info(f"执行 MediaCrawler: {' '.join(cmd)}")
            logger.info(f"超时时间: {timeout} 秒 ({timeout/60:.1f} 分钟)")
            
            # 执行爬虫
            result = subprocess.run(
                cmd,
                cwd=self.mediacrawler_dir,
                env=env,
                capture_output=False,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error(f"爬虫执行超时（{timeout/60:.1f} 分钟）")
            return False
        except Exception as e:
            logger.error(f"爬虫执行异常: {e}")
            return False
    
    def _load_and_convert_data(self) -> List[EducationHotspot]:
        """
        加载 JSONL 数据并转换为 EducationHotspot
        
        Returns:
            List[EducationHotspot]: 热点列表
        """
        # 查找最新的 JSONL 文件
        jsonl_dir = self.mediacrawler_dir / "data" / "xhs" / "jsonl"
        
        if not jsonl_dir.exists():
            logger.error(f"JSONL 目录不存在: {jsonl_dir}")
            return []
        
        jsonl_files = list(jsonl_dir.glob("search_contents_*.jsonl"))
        
        if not jsonl_files:
            logger.error("未找到 JSONL 文件")
            return []
        
        # 取最新的文件
        latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"使用数据文件: {latest_file.name}")
        
        # 加载并转换数据
        hotspots = []
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_data = json.loads(line)
                        hotspot = self.parse_item(raw_data)
                        hotspots.append(hotspot)
                    except json.JSONDecodeError as e:
                        logger.warning(f"第{line_num}行JSON解析失败: {e}")
                        continue
            
            logger.info(f"成功转换 {len(hotspots)} 条小红书数据")
            
        except Exception as e:
            logger.error(f"小红书数据转换失败: {e}", exc_info=True)
        
        return hotspots
