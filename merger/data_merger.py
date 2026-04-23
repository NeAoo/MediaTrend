"""
数据合并器
负责将多个数据源的采集结果合并为统一的JSON文件
严格按照 EducationHotspot 模型字段进行序列化和反序列化

{
  "metadata": {
    "generated_at": "",
    "total_count": "",
    "source_statistics": {
      "xiaohongshu": "",
      "zhihu": ""
    },
    "sources": []
  },
  "hotspots": [
    {
      "title": "",
      "source": "",
      "publish_time": "",
      "content_summary": "",
      "url": "",
      "author": "",
      "popularity": "",
      "cover_image": "",
      "image_list": [],
      "tags": [],
      "score": "",
      "score_details": ""
    }
  ]
}

"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

from models.hotspot import EducationHotspot


class DataMerger:
    """数据合并器 - 严格遵循 EducationHotspot 模型字段"""

    def __init__(self, output_dir: str = "./merged_data"):
        """
        初始化数据合并器

        Args:
            output_dir: 合并数据的输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def merge_sources(self, hotspots: List[EducationHotspot],
                     source_names: List[str] = None) -> str:
        """
        将多个数据源的热点数据合并为一个JSON文件
        严格按照 EducationHotspot 模型字段进行序列化

        Args:
            hotspots: 所有数据源的热点列表（已去重）
            source_names: 数据来源名称列表（用于统计）

        Returns:
            str: 生成的合并JSON文件路径
        """
        if not hotspots:
            logger.warning("没有数据需要合并")
            return ""

        # 统计各数据源数量
        source_stats = {}
        for hotspot in hotspots:
            source = hotspot.source
            source_stats[source] = source_stats.get(source, 0) + 1

        logger.info("=" * 60)
        logger.info("开始合并多源数据")
        logger.info("=" * 60)
        logger.info(f"总数据量: {len(hotspots)} 条")
        logger.info(f"数据来源统计:")
        for source, count in source_stats.items():
            logger.info(f"  - {source}: {count} 条")

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_file = self.output_dir / f"merged_hotspots_{timestamp}.json"

        # 构建合并数据结构
        merged_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_count": len(hotspots),
                "source_statistics": source_stats,
                "sources": source_names or list(source_stats.keys())
            },
            "hotspots": []
        }

        # 严格按照 EducationHotspot 模型字段序列化
        for idx, hotspot in enumerate(hotspots, 1):
            hotspot_dict = {
                # 必填字段
                "title": hotspot.title,
                "source": hotspot.source,
                "publish_time": hotspot.publish_time.isoformat(),
                "content_summary": hotspot.content_summary,
                "url": hotspot.url,

                # 可选字段
                "author": hotspot.author,
                "popularity": hotspot.popularity,
                "cover_image": hotspot.cover_image,
                "image_list": hotspot.image_list if hotspot.image_list else [],
                "tags": hotspot.tags if hotspot.tags else [],

                # 打分相关字段（采集阶段为空，打分后填充）
                "score": hotspot.score,
                "score_details": hotspot.score_details
            }
            merged_data["hotspots"].append(hotspot_dict)

        # 保存为JSON文件
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 数据合并完成")
        logger.info(f"📄 合并文件: {merged_file}")
        logger.info(f"📋 包含字段: title, source, author, publish_time, content_summary, url, popularity, cover_image, image_list, tags, score, score_details")
        logger.info("=" * 60)

        return str(merged_file)

    @staticmethod
    def load_merged_data(merged_file_path: str) -> List[EducationHotspot]:
        """
        从合并的JSON文件中加载热点数据
        严格按照 EducationHotspot 模型字段进行反序列化

        Args:
            merged_file_path: 合并JSON文件路径

        Returns:
            List[EducationHotspot]: 热点列表
        """
        if not Path(merged_file_path).exists():
            raise FileNotFoundError(f"合并文件不存在: {merged_file_path}")

        logger.info(f"从合并文件加载数据: {merged_file_path}")

        with open(merged_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        hotspots = []
        for item in data.get("hotspots", []):
            try:
                # 处理发布时间：支持 ISO 格式字符串
                publish_time_str = item.get("publish_time")
                if isinstance(publish_time_str, str):
                    publish_time = datetime.fromisoformat(publish_time_str)
                elif isinstance(publish_time_str, (int, float)):
                    # 兼容时间戳格式
                    publish_time = datetime.fromtimestamp(publish_time_str)
                else:
                    publish_time = datetime.now()

                # 严格按照模型字段构建对象
                hotspot = EducationHotspot(
                    # 必填字段
                    title=item["title"],
                    source=item["source"],
                    publish_time=publish_time,
                    content_summary=item["content_summary"],
                    url=item["url"],

                    # 可选字段
                    author=item.get("author"),
                    popularity=item.get("popularity"),
                    cover_image=item.get("cover_image"),
                    image_list=item.get("image_list") or [],
                    tags=item.get("tags") or [],

                    # 打分相关字段
                    score=item.get("score"),
                    score_details=item.get("score_details")
                )
                hotspots.append(hotspot)
            except Exception as e:
                logger.warning(f"加载热点数据失败: {e}, 跳过该项")
                logger.debug(f"问题数据: {item}")
                continue

        logger.info(f"成功加载 {len(hotspots)} 条热点数据")
        return hotspots

    @staticmethod
    def validate_hotspot_fields(hotspot_dict: Dict) -> bool:
        """
        验证字典是否包含 EducationHotspot 的所有必填字段

        Args:
            hotspot_dict: 待验证的字典

        Returns:
            bool: 是否有效
        """
        required_fields = [
            "title",
            "source",
            "publish_time",
            "content_summary",
            "url"
        ]

        missing_fields = [field for field in required_fields if field not in hotspot_dict]

        if missing_fields:
            logger.error(f"缺少必填字段: {missing_fields}")
            return False

        return True
