"""
Markdown 文档生成器
将筛选出的热点候选整合成 Markdown 文档
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger
import json
import argparse

from config.settings import OUTPUT_DIR, OUTPUT_FILENAME_PATTERN
from models.hotspot import CONTENT_MAX_LENGTH, EducationHotspot


class MarkdownGenerator:
    """Markdown 文档生成器"""

    def __init__(self, output_dir: str | None = None):
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(self, hotspots: List[EducationHotspot], date: datetime = None) -> str:
        """
        生成每日热点候选报告

        Args:
            hotspots: Top 10 热点列表
            date: 报告日期

        Returns:
            str: 生成的文件路径
        """
        if date is None:
            date = datetime.now()

        # 生成文件名
        filename = OUTPUT_FILENAME_PATTERN.format(
            date=date.strftime("%Y%m%d"),
            datetime=date.strftime("%Y%m%d_%H%M%S"),
        )
        filepath = self.output_dir / filename

        logger.info(f"正在生成日报: {filename}")

        # 生成 Markdown 内容
        content = self._build_markdown_content(hotspots, date)

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"日报已保存至: {filepath}")
        return str(filepath)

    def convert_scored_json_to_md(self, json_file: str, output_file: str = None) -> str:
        """
        将打分后的JSON文件转换为Markdown文档（参考 xhs_scored_json_to_md.py）
        
        Args:
            json_file: 打分后的JSON文件路径
            output_file: 输出文件路径（可选），默认自动生成
            
        Returns:
            str: 生成的Markdown文件路径
        """
        json_path = Path(json_file)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {json_file}")
        
        # 读取JSON数据
        with open(json_path, 'r', encoding='utf-8') as f:
            scored_data = json.load(f)
        
        if not scored_data:
            raise ValueError("JSON文件为空")
        
        # 生成输出文件名
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            top_n = len(scored_data)
            output_file = str(self.output_dir / f"教育热点_Top{top_n}_{timestamp}.md")
        
        logger.info(f"正在转换打分JSON: {len(scored_data)} 条数据")
        
        # 构建Markdown内容
        md_content = self._build_markdown_from_scored_data(scored_data)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"✅ Markdown报告已保存至: {output_file}")
        return output_file

    def _build_markdown_from_scored_data(self, scored_data: List[Dict]) -> str:
        """
        从打分数据构建Markdown内容（参考 xhs_scored_json_to_md.py）
        
        Args:
            scored_data: 打分后的数据列表
            
        Returns:
            str: Markdown内容字符串
        """
        # 统计信息
        total_items = len(scored_data)
        avg_score = sum(item.get('score', 0) for item in scored_data) / total_items if total_items > 0 else 0
        max_score = max((item.get('score', 0) for item in scored_data), default=0)
        min_score = min((item.get('score', 0) for item in scored_data), default=0)
        
        # 计算总热度
        total_popularity = sum(item.get('popularity', 0) for item in scored_data)
        
        md_content = f"""# 📚 热点候选精选（AI智能评分版）

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据来源**: 多平台采集 + AI智能评分  
**精选数量**: {total_items} 篇优质内容  

---

## 📊 评分概览

- **平均评分**: {avg_score:.2f} / 10.0
- **最高评分**: {max_score:.2f}
- **最低评分**: {min_score:.2f}
- **总热度值**: {total_popularity:,.0f}
- **评分维度**: 热度(35%) + 时效性(18%) + 大众共鸣(18%) + 对标价值(14%) + 内容质量(8%) + 权威性(4%) + 风险控制(3%)

---

## 🔥 Top {total_items} 热点详情

"""
        
        # 逐个添加笔记
        for item in scored_data:
            md_content += self._format_scored_note(item)
        
        # 页脚
        md_content += f"""
---

## 🤖 评分说明

本报告采用AI大模型对内容进行多维度智能评分：

### 评分维度
1. **🔥 热度 (35%)**: 内容的关注度、打开率和传播度
2. **⏰ 信息时效性 (18%)**: 内容的新鲜程度和发布窗口
3. **💡 大众共鸣 (18%)**: 普通读者是否有讨论、转发、评论或共情的理由
4. **🧭 对标价值 (14%)**: 是否适合作为标题、冲突、叙事节奏和情绪推进的母稿
5. **📚 内容质量 (8%)**: 信息的完整性、准确性和深度
6. **👑 权威性 (4%)**: 信息来源的可靠性和可核查性
7. **🛡️ 风险控制 (3%)**: 是否适合公开改写和发布

### 综合评分公式
综合评分 = 热度×0.35 + 时效性×0.18 + 大众共鸣×0.18 + 对标价值×0.14 + 内容质量×0.08 + 权威性×0.04 + 风险控制×0.03

### 使用说明
- 评分越高表示内容价值越大
- 建议优先阅读高分内容
- 点击"查看原文"可跳转到完整页面
- 本报告由自动化工具生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return md_content

    def _format_scored_note(self, item: Dict) -> str:
        """
        格式化单个打分后的笔记为Markdown（参考 xhs_scored_json_to_md.py）

        Args:
            item: 单条打分数据

        Returns:
            str: Markdown格式的笔记内容
        """
        rank = item.get('rank', 0)
        score = item.get('score', 0)
        score_details = item.get('score_details', {})
        title = item.get('title', '无标题')
        author = item.get('author', '未知作者')
        source = item.get('source', '未知来源')
        publish_time_str = item.get('publish_time', '')
        article_content = item.get('content', '')
        url = item.get('url', '')
        popularity = item.get('popularity', 0)
        cover_image = item.get('cover_image', '')
        image_list = item.get('image_list', [])
        tags = item.get('tags', [])

        # 解析发布时间
        if publish_time_str:
            try:
                publish_time = datetime.fromisoformat(publish_time_str).strftime('%Y-%m-%d')
            except Exception:
                publish_time = publish_time_str
        else:
            publish_time = '未知'

        # 奖牌图标
        medal_icons = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medal_icons.get(rank, f'#{rank}')

        # 评分星级
        star_count = int(score / 2)  # 5星制
        stars = '⭐' * star_count + '☆' * (5 - star_count)

        content = f"""### {medal} No.{rank} - {title}

**评分**: {score:.2f}/10.0 {stars}  
**作者**: {author} | **来源**: {source} | **发布**: {publish_time} | **热度**: {popularity:,.0f}

"""

        # 添加评分详情
        if score_details and isinstance(score_details, dict):
            heat = score_details.get('heat', 0)
            authority = score_details.get('authority', 0)
            quality = score_details.get('quality', 0)
            resonance = score_details.get('resonance', score_details.get('practicality', 0))
            timeliness = score_details.get('timeliness', 0)
            reference_value = score_details.get('reference_value', score_details.get('education_family_relevance', score_details.get('account_fit', 0)))
            risk_control = score_details.get('risk_control', 0)

            content += f"""**📈 评分详情**:
- 🔥 热度: {heat:.1f}/10
- 👑 权威性: {authority:.1f}/10
- 📚 内容质量: {quality:.1f}/10
- 💡 大众共鸣: {resonance:.1f}/10
- ⏰ 时效性: {timeliness:.1f}/10
- 🧭 对标价值: {reference_value:.1f}/10
- 🛡️ 风险控制: {risk_control:.1f}/10

"""

        # 添加正文
        if article_content:
            article_content = article_content[:CONTENT_MAX_LENGTH]
            content += f"**📝 内容**:\n\n{article_content}\n\n"

        # 添加标签
        if tags:
            tags_str = ' '.join([f"`{tag}`" for tag in tags[:5]])
            content += f"**🏷️ 标签**: {tags_str}\n\n"

        # 添加图片展示（最多前3张）
        if image_list and isinstance(image_list, list):
            display_images = image_list[:3]  # 只取前3张
            image_count = len(display_images)
            
            content += f"**🖼️ 图片预览** (共{len(image_list)}张，展示前{image_count}张):\n\n"
            
            for idx, img_url in enumerate(display_images, 1):
                if img_url:
                    content += f"![图片{idx}]({img_url})\n\n"
        
        elif cover_image:
            # 如果没有image_list但有cover_image，则显示封面图
            content += f"**🖼️ 封面预览**:\n\n![封面图]({cover_image})\n\n"

        # 原文链接
        content += f"[🔗 查看原文]({url})\n\n---\n\n"

        return content

    def convert_xhs_jsonl_to_md(self, jsonl_file: str, output_file: str = None, max_items: int = 10) -> str:
        """
        将小红书 JSONL 数据转换为 Markdown 文档
        
        Args:
            jsonl_file: JSONL 文件路径
            output_file: 输出文件路径（可选）
            max_items: 最大处理条目数
            
        Returns:
            str: 生成的文件路径
        """
        # 读取 JSONL 文件
        notes = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    notes.append(json.loads(line))
        
        # 限制数量
        notes = notes[:max_items]
        
        # 生成文件名
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = str(self.output_dir / f"小红书教育热点_{timestamp}.md")
        
        logger.info(f"正在转换小红书数据: {len(notes)} 条笔记")
        
        # 构建 Markdown 内容
        md_content = self._build_xhs_markdown(notes)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"小红书报告已保存至: {output_file}")
        return output_file

    def _parse_count(self, count_str: str) -> int:
        """
        解析小红书互动数字符串（如 "1.8万", "9528"）
        
        Args:
            count_str: 数字字符串
            
        Returns:
            int: 转换后的整数
        """
        if not count_str or count_str == '未知':
            return 0
        
        count_str = str(count_str).strip()
        
        # 处理 "万" 单位
        if '万' in count_str:
            try:
                num = float(count_str.replace('万', ''))
                return int(num * 10000)
            except ValueError:
                return 0
        
        # 处理 "亿" 单位
        if '亿' in count_str:
            try:
                num = float(count_str.replace('亿', ''))
                return int(num * 100000000)
            except ValueError:
                return 0
        
        # 普通数字
        try:
            return int(float(count_str))
        except ValueError:
            return 0

    def _build_xhs_markdown(self, notes: list) -> str:
        """
        构建小红书 Markdown 内容
        
        Args:
            notes: 小红书笔记列表
            
        Returns:
            str: Markdown 内容
        """
        # 统计信息
        total_likes = sum(self._parse_count(note.get('liked_count', 0)) for note in notes)
        total_collects = sum(self._parse_count(note.get('collected_count', 0)) for note in notes)
        video_count = sum(1 for note in notes if note.get('type') == 'video')
        image_count = len(notes) - video_count
        
        md_content = f"""# 📕 小红书教育热点精选

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据来源**: 小红书平台  
**精选数量**: {len(notes)} 篇优质内容  

---

## 📊 数据概览

- **总点赞数**: {total_likes:,}
- **总收藏数**: {total_collects:,}
- **内容类型**: {image_count} 篇图文 + {video_count} 个视频
- **平均互动**: {total_likes // len(notes) if notes else 0} 点赞/篇

---

## 🔥 热点详情

"""
        
        # 逐个添加笔记
        for idx, note in enumerate(notes, 1):
            md_content += self._format_xhs_note(idx, note)
        
        # 页脚
        md_content += f"""
---

## 📌 说明

- 以上内容来自小红书平台教育相关话题
- 图片可能需要设置 Referer 才能正常显示
- 建议点击原文链接查看完整内容和评论区讨论
- 本报告由自动化工具生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return md_content

    def _format_xhs_note(self, index: int, note: dict) -> str:
        """
        格式化单个小红书笔记
        
        Args:
            index: 序号
            note: 笔记数据字典
            
        Returns:
            str: Markdown 格式内容
        """
        title = note.get('title', '无标题')
        desc = note.get('desc', '')
        nickname = note.get('nickname', '未知作者')
        liked_count = note.get('liked_count', '0')
        collected_count = note.get('collected_count', '0')
        comment_count = note.get('comment_count', '0')
        note_url = note.get('note_url', '')
        note_type = note.get('type', 'normal')
        
        # 时间戳转换（毫秒级）
        time_ms = note.get('time', 0)
        if time_ms:
            publish_time = datetime.fromtimestamp(time_ms / 1000).strftime('%Y-%m-%d')
        else:
            publish_time = '未知'
        
        # 类型图标
        type_icon = "🎥" if note_type == 'video' else "📝"
        type_name = "视频" if note_type == 'video' else "图文"
        
        # 解析图片列表
        image_urls = note.get('image_list', '').split(',') if note.get('image_list') else []
        
        content = f"""### {index}. {type_icon} {title}

**类型**: {type_name} | **作者**: {nickname} | **发布**: {publish_time}  
**👍 点赞**: {liked_count} | **⭐ 收藏**: {collected_count} | **💬 评论**: {comment_count}

"""
        
        # 添加描述
        if desc:
            content += f"**📝 描述**:\n\n{desc}\n\n"
        
        # 添加图片（最多3张）
        if image_urls:
            content += "**🖼️ 内容预览**:\n\n"
            for i, url in enumerate(image_urls[:3], 1):
                if url.strip():
                    content += f"![图片{i}]({url.strip()})\n\n"
            
            if len(image_urls) > 3:
                content += f"*（还有 {len(image_urls) - 3} 张图片，请查看原文）*\n\n"
        
        # 原文链接
        content += f"[🔗 查看原文]({note_url})\n\n---\n\n"
        
        return content

    def _build_markdown_content(self, hotspots: List[EducationHotspot], date: datetime) -> str:
        """
        构建 Markdown 内容

        Args:
            hotspots: 热点列表
            date: 日期

        Returns:
            str: Markdown 内容
        """
        # 从配置中读取时间范围
        from config.settings import TIME_RANGE_MIN, TIME_RANGE_MAX
        
        # 生成时间范围描述
        if TIME_RANGE_MIN == 0:
            time_range_desc = f"最近{TIME_RANGE_MAX}小时"
        else:
            time_range_desc = f"{TIME_RANGE_MIN}-{TIME_RANGE_MAX}小时"
        
        # 文档头部
        md_content = f"""# 📚 热点候选日报

**报告日期**: {date.strftime('%Y年%m月%d日')}  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**热点数量**: {len(hotspots)} 条  
**时间范围**: {time_range_desc}

---

## 📊 今日热点概览

> 本报告精选了{time_range_desc}内最适合作为公众号对标母稿的热点候选，重点关注打开率、传播性、社会情绪、冲突强度和可改写空间。

### 热点分布
- **政策/规则**: {self._count_by_category(hotspots, '政策')} 条
- **家庭/关系**: {self._count_by_category(hotspots, '家庭')} 条
- **升学/教育**: {self._count_by_category(hotspots, '升学')} 条
- **其他社会热点**: {len(hotspots) - self._count_by_category(hotspots, '政策') - self._count_by_category(hotspots, '家庭') - self._count_by_category(hotspots, '升学')} 条

---

## 🔥 Top {len(hotspots)} 热点候选详情

"""

        # 逐个添加热点内容
        for i, hotspot in enumerate(hotspots, 1):
            md_content += self._format_hotspot_item(i, hotspot)

        # 文档尾部
        md_content += f"""
---

## 💡 使用提示

1. **优先看传播性**: 高分内容更适合作为公众号热点对标母稿
2. **多方求证**: 涉及具体人物、机构、政策、医疗等内容，发布前仍需二次核查
3. **看结构而不是照搬**: 重点借鉴标题、冲突、叙事节奏和情绪推进
4. **轻量转化**: 智趣点读广告适合放在结尾，避免硬转教育

---

## 📌 数据来源

本报告数据来源于微信公众号、小红书、资讯网站等多个渠道，经AI智能评分筛选后生成。

**评分维度**: 热度、时效性、大众共鸣、对标价值、内容质量、权威性、风险控制

---

"""

        return md_content

    def _format_hotspot_item(self, index: int, hotspot: EducationHotspot) -> str:
        """
        格式化单个热点条目

        Args:
            index: 序号
            hotspot: 热点对象

        Returns:
            str: Markdown 格式的热点内容
        """
        # 评分星级显示
        score = hotspot.score or 0
        stars = "⭐" * int(score / 2)  # 5星制

        # 分类标签
        category_tag = self._categorize_hotspot(hotspot)

        content = f"""### {index}. {hotspot.title}

**📌 分类**: {category_tag}  
**📢 来源**: {hotspot.source}  
**⏰ 发布时间**: {hotspot.publish_time.strftime('%Y-%m-%d %H:%M')}  
**🔥 综合评分**: {score:.1f}/10 {stars}  
**👁️ 热度指标**: {hotspot.popularity or '未知'}

"""

        # 添加图片展示（最多前3张）
        if hotspot.image_list and isinstance(hotspot.image_list, list) and len(hotspot.image_list) > 0:
            display_images = hotspot.image_list[:3]  # 只取前3张
            image_count = len(display_images)
            total_count = len(hotspot.image_list)
            
            content += f"**🖼️ 图片预览** (共{total_count}张，展示前{image_count}张):\n\n"
            
            for idx, img_url in enumerate(display_images, 1):
                if img_url:
                    content += f"![图片{idx}]({img_url})\n\n"
        
        elif hotspot.cover_image:
            # 如果没有image_list但有cover_image，则显示封面图
            content += f"**🖼️ 封面预览**:\n\n![封面图]({hotspot.cover_image})\n\n"

        content += f"""**📝 内容**:

{hotspot.content}

**💬 推荐理由**:

{self._generate_recommendation(hotspot)}

**📊 评分详情**:
- 热度: {self._get_score_detail(hotspot, 'heat'):.1f}
- 权威性: {self._get_score_detail(hotspot, 'authority'):.1f}
- 内容质量: {self._get_score_detail(hotspot, 'quality'):.1f}
- 大众共鸣: {self._get_score_detail(hotspot, 'resonance'):.1f}
- 时效性: {self._get_score_detail(hotspot, 'timeliness'):.1f}
- 对标价值: {self._get_score_detail(hotspot, 'reference_value'):.1f}
- 风险控制: {self._get_score_detail(hotspot, 'risk_control'):.1f}

[🔗 查看原文]({hotspot.url})

---

"""
        return content

    def _categorize_hotspot(self, hotspot: EducationHotspot) -> str:
        """对热点进行分类"""
        title_lower = hotspot.title.lower()

        if any(kw in title_lower for kw in ['政策', '规定', '改革', '通知', '发布']):
            return "📋 政策/规则"
        elif any(kw in title_lower for kw in ['家庭', '亲子', '家长', '育儿']):
            return "👨‍👩‍👧 家庭/关系"
        elif any(kw in title_lower for kw in ['中考', '高考', '升学', '志愿', '招生']):
            return "🎓 升学/教育"
        elif any(kw in title_lower for kw in ['学习', '方法', '习惯', '阅读']):
            return "📖 学习/成长"
        elif any(kw in title_lower for kw in ['心理', '健康', '近视', '睡眠']):
            return "💚 健康/生活"
        else:
            return "📰 社会热点"

    def _generate_recommendation(self, hotspot: EducationHotspot) -> str:
        """生成推荐理由"""
        score = hotspot.score or 0

        if score >= 8.5:
            return "⭐⭐⭐ 强烈推荐！这条内容具备较强打开率和对标价值，建议优先进入候选。"
        elif score >= 7.5:
            return "⭐⭐ 值得关注的优质热点，适合进一步核查后改写。"
        elif score >= 6.0:
            return "⭐ 具有一定参考价值，可作为备选热点线索。"
        else:
            return "可作为一般性了解，建议结合其他信息源综合判断。"

    def _get_score_detail(self, hotspot: EducationHotspot, dimension: str) -> float:
        """获取评分细节"""
        if hotspot.score_details and isinstance(hotspot.score_details, dict):
            if dimension == "reference_value":
                return hotspot.score_details.get(
                    "reference_value",
                    hotspot.score_details.get(
                        "education_family_relevance",
                        hotspot.score_details.get("account_fit", 5.0),
                    ),
                )
            fallback_keys = {
                "resonance": "practicality",
            }
            return hotspot.score_details.get(
                dimension,
                hotspot.score_details.get(fallback_keys.get(dimension, ""), 5.0),
            )
        return 5.0

    def _count_by_category(self, hotspots: List[EducationHotspot], keyword: str) -> int:
        """统计某类别的数量"""
        count = 0
        for hotspot in hotspots:
            if keyword in hotspot.title or keyword in hotspot.content:
                count += 1
        return count


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='教育热点 Markdown 报告生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 1. 将打分后的JSON转换为Markdown
  python markdown.py json --input scored_results/xiaohongshu_scored_20260422_210516.json
  
  # 2. 将小红书JSONL转换为Markdown
  python markdown.py xhs --input TrendCrawlerRuntime/data/xhs/jsonl/search_contents_2026-04-22_22-55-51.jsonl --max-items 10
  
  # 3. 指定输出文件
  python markdown.py json --input data.json --output ./output/my_report.md
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令类型')
    
    # JSON 转 Markdown 子命令
    json_parser = subparsers.add_parser('json', help='将打分后的JSON转换为Markdown')
    json_parser.add_argument('--input', '-i', required=True, help='输入的JSON文件路径')
    json_parser.add_argument('--output', '-o', default=None, help='输出的Markdown文件路径（可选）')
    
    # 小红书 JSONL 转 Markdown 子命令
    xhs_parser = subparsers.add_parser('xhs', help='将小红书JSONL转换为Markdown')
    xhs_parser.add_argument('--input', '-i', required=True, help='输入的JSONL文件路径')
    xhs_parser.add_argument('--output', '-o', default=None, help='输出的Markdown文件路径（可选）')
    xhs_parser.add_argument('--max-items', '-m', type=int, default=10, help='最大处理条目数（默认10）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 创建生成器
    generator = MarkdownGenerator()
    
    try:
        if args.command == 'json':
            logger.info("=" * 60)
            logger.info("开始转换打分JSON到Markdown")
            logger.info("=" * 60)
            
            output_file = generator.convert_scored_json_to_md(
                json_file=args.input,
                output_file=args.output
            )
            
            logger.info(f"✅ 转换完成！文件已保存至: {output_file}")
            
        elif args.command == 'xhs':
            logger.info("=" * 60)
            logger.info("开始转换小红书JSONL到Markdown")
            logger.info("=" * 60)
            
            output_file = generator.convert_xhs_jsonl_to_md(
                jsonl_file=args.input,
                output_file=args.output,
                max_items=args.max_items
            )
            
            logger.info(f"✅ 转换完成！文件已保存至: {output_file}")
    
    except FileNotFoundError as e:
        logger.error(f"❌ 文件未找到: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ 数据错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 程序执行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
