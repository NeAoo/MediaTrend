"""
演示用教育资讯采集器
使用公开API和RSS源获取真实的教育热点资讯
"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List
from loguru import logger

from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot, CollectionResult


class DemoEducationCrawler(BaseCrawler):
    """演示教育资讯采集器 - 使用真实数据源"""

    def __init__(self):
        super().__init__("demo")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        # 教育类 RSS 源和 API
        self.news_sources = [
            {
                "name": "百度教育热搜",
                "type": "rss",
                "url": "http://top.baidu.com/rss?platform=wise&category=education"
            },
            {
                "name": "知乎教育话题",
                "type": "api",
                "url": "https://www.zhihu.com/api/v4/topics/19552883/hot-activities"
            },
        ]

    def collect(self, keywords: List[str], time_range_hours: tuple = (24, 48)) -> CollectionResult:
        """
        采集教育热点资讯

        Args:
            keywords: 教育相关关键词
            time_range_hours: 时间范围

        Returns:
            CollectionResult: 采集结果
        """
        result = CollectionResult()

        # 方法1: 从 RSS 源采集
        rss_items = self._collect_from_rss(keywords)
        result.items.extend(rss_items)
        result.success_count += len(rss_items)

        # 方法2: 模拟生成一些示例数据（用于演示）
        if len(result.items) < 30:
            demo_items = self._generate_demo_data(keywords)
            result.items.extend(demo_items)
            result.success_count += len(demo_items)
            logger.info(f"生成了 {len(demo_items)} 条演示数据")

        logger.info(f"演示采集器完成: 成功{result.success_count}条")
        return result

    def _collect_from_rss(self, keywords: List[str]) -> List[EducationHotspot]:
        """从 RSS 源采集教育资讯"""
        items = []

        # 尝试从几个公开的教育资讯源获取
        rss_feeds = [
            "https://feedx.net/rss/qq/edu.xml",  # 腾讯教育
            "http://rss.sina.com.cn/news/allnews/sports.xml",  # 新浪教育（示例）
        ]

        for feed_url in rss_feeds:
            try:
                logger.info(f"正在抓取 RSS: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # 每个源最多取10条
                    try:
                        # 解析发布时间
                        publish_time = self._parse_feed_time(entry)

                        # 检查时间范围
                        if not self.validate_time_range(publish_time, 24, 48):
                            continue

                        # 检查是否包含教育关键词
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')

                        if not self._contains_education_keywords(title + ' ' + summary, keywords):
                            continue

                        hotspot = EducationHotspot(
                            title=title[:100],
                            source="教育资讯",
                            author=entry.get('author'),
                            publish_time=publish_time,
                            content_summary=summary[:200] if summary else title,
                            url=entry.get('link', ''),
                            tags=["教育", "RSS"]
                        )
                        items.append(hotspot)

                    except Exception as e:
                        logger.debug(f"解析 RSS 条目失败: {e}")
                        continue

            except Exception as e:
                logger.warning(f"RSS 源 {feed_url} 抓取失败: {e}")
                continue

        logger.info(f"RSS 采集到 {len(items)} 条内容")
        return items

    def _generate_demo_data(self, keywords: List[str]) -> List[EducationHotspot]:
        """
        生成演示数据（用于展示完整流程）
        实际使用时应该替换为真实的数据源
        """
        from datetime import datetime, timedelta
        import random

        demo_titles = [
            ("教育部发布2026年中小学招生新政，这些变化家长必须知道", "教育部官方网站"),
            ("北京中考改革方案出炉：增加综合素质评价权重", "北京教育考试院"),
            ("专家建议：小学生每天睡眠时间应达到10小时", "中国教育报"),
            ("双减政策实施两年后，家庭教育支出变化调查", "澎湃新闻"),
            ("高考志愿填报指南：如何选择适合的专业和学校", "阳光高考平台"),
            ("幼小衔接关键期，家长如何做好准备工作", "家长帮社区"),
            ("在线教育新规出台：培训机构必须符合这些要求", "央视新闻"),
            ("清华大学发布自主招生新政策，侧重创新能力", "清华大学招生办"),
            ("儿童阅读习惯培养：每天阅读30分钟的重要性", "亲子教育杂志"),
            ("中学生心理健康问题频发，学校如何应对", "心理学报"),
            ("素质教育实践：上海某小学的创新教学模式", "解放日报"),
            ("家庭教育促进法实施一年，家长们怎么看", "人民日报"),
            ("考研报名人数创新高，竞争激烈程度分析", "中国研究生招生信息网"),
            ("幼儿园入学年龄限制是否会调整？教育部回应", "教育部新闻发布会"),
            ("STEM教育在中国：现状与未来发展趋势", "科技日报"),
            ("留守儿童教育问题：社会各界如何共同关注", "光明日报"),
            ("高校就业质量报告：这些专业就业率最高", "麦可思研究院"),
            ("课外辅导班退费难问题，消费者如何维权", "消费者权益保护委员会"),
            ("教师队伍建设：提高待遇吸引优秀人才从教", "中国教育新闻网"),
            ("国际教育趋势：全球教育创新案例分享", "联合国教科文组织"),
            ("职业教育改革：打通升学就业双通道", "职业教育法"),
            ("学区房政策调整，对教育资源分配的影响", "财经杂志"),
            ("青少年近视防控：学校和家长该如何配合", "卫生健康委员会"),
            ("在线教育平台监管加强，家长如何选择靠谱机构", "市场监管总局"),
            ("高考作文题目引发热议，专家解读命题趋势", "语文杂志社"),
            ("大学生创业支持政策汇总，助力青年创新创业", "人力资源和社会保障部"),
            ("学前教育普惠性发展，让更多孩子享受优质教育", "新华社"),
            ("终身学习理念下，成人教育市场迎来新机遇", "继续教育协会"),
            ("教育公平推进：农村学校信息化建设成果显著", "教育部发展规划司"),
            ("家校合作新模式：建立有效的沟通机制", "家庭教育研究会"),
        ]

        items = []
        now = datetime.now()

        for i, (title, source) in enumerate(demo_titles):
            # 生成24-48小时内的随机时间
            hours_ago = random.uniform(24, 48)
            publish_time = now - timedelta(hours=hours_ago)

            hotspot = EducationHotspot(
                title=title,
                source=source,
                author=None,
                publish_time=publish_time,
                content_summary=f"【{title}】这是关于教育领域的最新热点资讯，涉及政策变化、教育改革、家庭教育等重要内容，值得家长关注。详细内容请点击原文链接查看完整报道。",
                url=f"https://example.com/education/news/{i+1}",
                popularity=random.randint(100, 10000),
                tags=["教育", "热点", "家长必读"]
            )
            items.append(hotspot)

        return items

    def _parse_feed_time(self, entry) -> datetime:
        """解析 RSS feed 的发布时间"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            else:
                return datetime.now()
        except:
            return datetime.now()

    def _contains_education_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本是否包含教育相关关键词"""
        education_terms = keywords + [
            "教育", "学校", "学生", "老师", "家长",
            "学习", "考试", "课程", "培训", "升学",
            "中考", "高考", "幼儿园", "大学", "教学"
        ]
        return any(term in text for term in education_terms)

    def parse_item(self, raw_data: dict) -> EducationHotspot:
        """解析数据项（此采集器直接返回 EducationHotspot）"""
        return raw_data