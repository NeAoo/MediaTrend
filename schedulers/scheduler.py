"""
定时任务调度器
负责管理教育热点采集的定时执行
"""
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from crawlers.manager import CrawlerManager
from scorers.scorer import ContentScorer
from formatters.markdown import MarkdownGenerator
from config.settings import (
    INITIAL_COLLECT_COUNT,
    TOP_N_SELECT_COUNT,
    SCHEDULE_TIME,
    LOG_FILE
)


class EducationHotspotScheduler:
    """教育热点采集调度器"""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.setup_listeners()

    def setup_listeners(self):
        """设置任务监听器"""
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def _job_listener(self, event):
        """任务执行事件监听"""
        if event.exception:
            logger.error(f"❌ 任务执行失败: {event.exception}")
        else:
            logger.info(f"✅ 任务执行成功: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def add_daily_job(self, hour: int = 8, minute: int = 0):
        """
        添加每日定时任务

        Args:
            hour: 执行小时（0-23）
            minute: 执行分钟（0-59）
        """
        # 解析配置的时间
        if ":" in SCHEDULE_TIME:
            hour, minute = map(int, SCHEDULE_TIME.split(":"))

        self.scheduler.add_job(
            self._run_collection_task,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_education_hotspot',
            name='每日教育热点采集',
            replace_existing=True
        )

        logger.info(f"已添加每日定时任务: 每天 {hour:02d}:{minute:02d} 执行")

    def add_interval_job(self, hours: int = 24):
        """
        添加间隔任务

        Args:
            hours: 间隔小时数
        """
        from apscheduler.triggers.interval import IntervalTrigger

        self.scheduler.add_job(
            self._run_collection_task,
            trigger=IntervalTrigger(hours=hours),
            id='interval_education_hotspot',
            name='间隔教育热点采集',
            replace_existing=True
        )

        logger.info(f"已添加间隔任务: 每 {hours} 小时执行一次")

    def run_immediately(self):
        """立即执行一次任务"""
        logger.info("立即执行采集任务...")
        try:
            self._run_collection_task()
        except Exception as e:
            logger.error(f"立即执行任务失败: {e}", exc_info=True)

    def start(self):
        """启动调度器"""
        logger.info("=" * 60)
        logger.info("🚀 教育热点采集调度器启动")
        logger.info("=" * 60)

        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("调度器被用户中断")
            self.shutdown()

    def shutdown(self):
        """关闭调度器"""
        logger.info("正在关闭调度器...")
        self.scheduler.shutdown(wait=False)
        logger.info("调度器已关闭")

    def _run_collection_task(self):
        """执行采集任务（核心逻辑）"""
        task_start_time = datetime.now()
        logger.info("\n" + "=" * 60)
        logger.info(f"⏰ 开始执行采集任务: {task_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        try:
            # ==================== 第一步：采集热点内容 ====================
            logger.info("\n📥 第一步：开始采集教育热点...")
            crawler_manager = CrawlerManager()

            keywords = [
                "教育", "家庭教育", "升学政策", "学习方法",
                "中考", "高考", "素质教育", "双减"
            ]

            hotspots = crawler_manager.collect_all(keywords)

            logger.info(f"✅ 采集完成，共获取 {len(hotspots)} 条热点内容")

            if not hotspots:
                logger.warning("⚠️ 未采集到任何内容，任务结束")
                return

            # 打印采集结果概览
            logger.info("\n📋 采集内容预览（前5条）:")
            for i, hotspot in enumerate(hotspots[:5], 1):
                logger.info(f"  {i}. [{hotspot.source}] {hotspot.title[:50]}")

            # ==================== 第二步：大模型打分排序 ====================
            logger.info("\n🎯 第二步：开始对内容进行智能打分...")
            scorer = ContentScorer()
            scored_hotspots = scorer.score_batch(hotspots)

            logger.info(f"✅ 打分完成，所有内容已评分")

            # 打印评分概览
            logger.info("\n📊 评分概览（前5条）:")
            for i, hotspot in enumerate(scored_hotspots[:5], 1):
                logger.info(f"  {i}. 评分: {hotspot.score:.2f} | {hotspot.title[:40]}")

            # ==================== 第三步：筛选 Top 10 ====================
            logger.info(f"\n🏆 第三步：筛选前 {TOP_N_SELECT_COUNT} 条高分内容...")
            top_hotspots = scorer.select_top_n(scored_hotspots, TOP_N_SELECT_COUNT)

            logger.info(f"✅ 筛选完成，最终选取 {len(top_hotspots)} 条优质内容")

            # 打印最终结果
            logger.info("\n🎉 最终入选热点（按评分排序）:")
            for i, hotspot in enumerate(top_hotspots, 1):
                logger.info(f"  {i}. ⭐{hotspot.score:.1f} | {hotspot.title[:50]}")

            # ==================== 第四步：生成 Markdown 日报 ====================
            logger.info("\n📝 第四步：生成 Markdown 日报...")
            generator = MarkdownGenerator()
            output_file = generator.generate_daily_report(top_hotspots)

            logger.info(f"✅ 日报生成成功！")
            logger.info(f"📄 文件位置: {output_file}")

            # ==================== 第五步：发送通知（可选） ====================
            task_end_time = datetime.now()
            duration = (task_end_time - task_start_time).total_seconds()

            logger.info("\n" + "=" * 60)
            logger.info("🎊 教育热点采集任务完成！")
            logger.info("=" * 60)
            logger.info(f"\n✨ 任务执行报告:")
            logger.info(f"   - 开始时间: {task_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   - 结束时间: {task_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   - 执行耗时: {duration:.1f} 秒")
            logger.info(f"   - 采集内容: {len(hotspots)} 条")
            logger.info(f"   - 最终入选: {len(top_hotspots)} 条")
            logger.info(f"   - 输出文件: {output_file}")
            logger.info(f"   - 最高评分: {top_hotspots[0].score:.2f}")

            # 发送通知
            self._send_notification(output_file, task_start_time, task_end_time, duration)

        except Exception as e:
            logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
            # 发送失败通知
            self._send_failure_notification(e, task_start_time)

    def _send_notification(self, output_file: str, start_time: datetime,
                          end_time: datetime, duration: float):
        """
        发送任务完成通知

        Args:
            output_file: 输出文件路径
            start_time: 开始时间
            end_time: 结束时间
            duration: 执行耗时
        """
        # TODO: 实现通知发送（邮件、微信、钉钉等）
        # 目前仅记录日志

        logger.info("\n📧 任务完成通知:")
        logger.info(f"  ✅ 教育热点日报已生成")
        logger.info(f"  📄 文件: {output_file}")
        logger.info(f"  ⏱️  耗时: {duration:.1f} 秒")
        logger.info(f"  📅 日期: {end_time.strftime('%Y年%m月%d日')}")

        # 示例：邮件通知
        # self._send_email_notification(output_file, start_time, end_time, duration)

        # 示例：钉钉 webhook 通知
        # self._send_dingtalk_notification(output_file, start_time, end_time, duration)

    def _send_failure_notification(self, error: Exception, start_time: datetime):
        """
        发送任务失败通知

        Args:
            error: 异常信息
            start_time: 开始时间
        """
        # TODO: 实现失败通知发送

        logger.error("\n🚨 任务失败通知:")
        logger.error(f"  ❌ 采集任务执行失败")
        logger.error(f"  🐛 错误: {str(error)}")
        logger.error(f"  📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def list_jobs(self):
        """列出所有任务"""
        logger.info("\n已注册的任务:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")
            try:
                if hasattr(job, 'trigger'):
                    next_run = job.next_run_time if hasattr(job, 'next_run_time') else "未设置"
                    logger.info(f"    下次执行: {next_run}")
            except:
                logger.info(f"    下次执行: 待计算")
