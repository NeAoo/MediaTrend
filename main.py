"""
教育热点搜集 Agent - 主入口
支持单次执行和定时调度两种模式
功能：自动采集教育类热点 → AI 打分排序 → 筛选优质内容 → 生成 Markdown 日报
"""

# ========================= 导入依赖库 =========================
import argparse
from pathlib import Path
from loguru import logger

# 导入项目核心模块
from crawlers.manager import CrawlerManager       # 爬虫管理器（多平台采集）
from merger.data_merger import DataMerger     # 数据合并器（多源数据合并）
from scorers.scorer import ContentScorer          # 内容打分器（AI 评分排序）
from formatters.markdown import MarkdownGenerator # Markdown 报告生成器
from config.settings import (
    INITIAL_COLLECT_COUNT,  # 初始采集数量配置
    TOP_N_SELECT_COUNT,     # 最终筛选 TOP N 配置
    KEYWORDS,               # 搜索关键词列表
    LOG_FILE,               # 日志文件路径
    LOG_LEVEL,              # 日志输出级别
    SCHEDULE_TIME           # 定时任务执行时间
)


def setup_logger():
    """配置日志输出"""
    # 确保日志目录存在
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 移除默认的处理器
    logger.remove()
    
    # 添加控制台输出（带颜色）
    logger.add(
        lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="10 MB",  # 日志文件超过10MB自动切割
        retention="30 days",  # 保留30天的日志
        encoding="utf-8"
    )


def run_collection_task():
    """
    执行一次完整的采集任务
    
    Returns:
        bool: 是否成功
    """
    logger.info("=" * 60)
    logger.info("教育热点搜集 Agent 启动")
    logger.info("=" * 60)
    
    try:
        # ==================== 第一步：采集热点内容 ====================
        logger.info("\n第一步：开始采集教育热点...")
        crawler_manager = CrawlerManager()
        
        # 使用配置文件中的关键词
        logger.info(f"搜索关键词: {', '.join(KEYWORDS)}")
        hotspots = crawler_manager.collect_all(KEYWORDS)

        logger.info(f"采集完成，共获取 {len(hotspots)} 条热点内容")
        
        if not hotspots:
            logger.error("未采集到任何内容，程序退出")
            return False
        
        # 打印采集结果概览
        logger.info("\n采集内容预览（前5条）:")
        for i, hotspot in enumerate(hotspots[:5], 1):
            logger.info(f"  {i}. [{hotspot.source}] {hotspot.title[:50]}")

        # ==================== 第二步：合并多源数据 ====================
        logger.info("\n第二步：合并多源数据为统一JSON文件...")
        merger = DataMerger()
        
        # 获取启用的数据源列表
        from config.settings import ENABLED_SOURCES
        merged_file = merger.merge_sources(hotspots, source_names=ENABLED_SOURCES)
        
        if not merged_file:
            logger.error("数据合并失败")
            return False
        
        logger.info(f"合并文件已生成: {merged_file}")

        # ==================== 第三步：大模型打分排序 ====================
        logger.info("\n第三步：开始对内容进行智能打分...")
        scorer = ContentScorer()
        scored_hotspots = scorer.score_batch(hotspots)
        
        logger.info(f"打分完成，所有内容已评分")
        
        # 打印评分概览
        logger.info("\n评分概览（前5条）:")
        for i, hotspot in enumerate(scored_hotspots[:5], 1):
            logger.info(f"  {i}. 评分: {hotspot.score:.2f} | {hotspot.title[:40]}")
        
        # ==================== 第四步：保存打分后的数据 ====================
        logger.info("\n第四步：保存打分后的数据到 scored_data...")
        scored_merger = DataMerger(output_dir="./scored_data")
        scored_file = scored_merger.merge_sources(
            scored_hotspots, 
            source_names=ENABLED_SOURCES
        )
        
        if scored_file:
            logger.info(f"✅ 打分数据已保存: {scored_file}")
        else:
            logger.warning("⚠️ 打分数据保存失败")

        # ==================== 第五步：筛选 Top N ====================
        logger.info(f"\n第五步：筛选前 {TOP_N_SELECT_COUNT} 条高分内容...")
        top_hotspots = scorer.select_top_n(scored_hotspots, TOP_N_SELECT_COUNT)
        
        logger.info(f"筛选完成，最终选取 {len(top_hotspots)} 条优质内容")
        
        # 打印最终结果
        logger.info("\n最终入选热点（按评分排序）:")
        for i, hotspot in enumerate(top_hotspots, 1):
            logger.info(f"  {i}. {hotspot.score:.1f}分 | {hotspot.title[:50]}")
        
        # ==================== 第六步：生成 Markdown 日报 ====================
        logger.info("\n第六步：生成 Markdown 日报...")
        generator = MarkdownGenerator()
        output_file = generator.generate_daily_report(top_hotspots)
        
        logger.info(f"日报生成成功！")
        logger.info(f"文件位置: {output_file}")
        
        # ==================== 完成 ====================
        logger.info("\n" + "=" * 60)
        logger.info("教育热点搜集任务全部完成！")
        logger.info("=" * 60)
        logger.info(f"\n今日成果:")
        logger.info(f"   - 采集内容: {len(hotspots)} 条")
        logger.info(f"   - 合并文件: {merged_file}")
        logger.info(f"   - 打分数据: {scored_file}")
        logger.info(f"   - 最终入选: {len(top_hotspots)} 条")
        logger.info(f"   - 输出文件: {output_file}")
        logger.info(f"   - 最高评分: {top_hotspots[0].score:.2f}")
        logger.info(f"   - 日志文件: {LOG_FILE}")
        
        return True
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)
        return False


def start_scheduler():
    """启动定时任务调度器"""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    setup_logger()
    
    logger.info("=" * 60)
    logger.info("🚀 教育热点搜集 Agent - 定时调度模式")
    logger.info("=" * 60)
    
    # 解析配置的时间
    hour, minute = 8, 0
    if ":" in SCHEDULE_TIME:
        hour, minute = map(int, SCHEDULE_TIME.split(":"))
    
    scheduler = BlockingScheduler()
    
    # 添加每日定时任务
    scheduler.add_job(
        run_collection_task,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='daily_education_hotspot',
        name='每日教育热点采集',
        replace_existing=True
    )
    
    logger.info(f"✅ 已添加每日定时任务: 每天 {hour:02d}:{minute:02d} 执行")
    logger.info(f"💡 提示: 按 Ctrl+C 停止调度器\n")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("\n⌨️  调度器被用户中断")
        scheduler.shutdown(wait=False)
        logger.info("✅ 调度器已关闭")


def show_usage():
    """显示使用说明"""
    print("""
教育热点搜集 Agent - 使用帮助

用法:
  python main.py run          # 立即执行一次采集任务
  python main.py start        # 启动定时任务调度器
  python main.py --help       # 显示帮助信息

示例:
  # 立即执行一次采集
  python main.py run
  
  # 启动定时任务（每天 8:00 执行，可在 config/settings.py 中配置）
  python main.py start

配置:
  - 修改 config/settings.py 中的 SCHEDULE_TIME 调整执行时间
  - 修改 config/settings.py 中的 ENABLED_SOURCES 启用/禁用数据源
  - 修改 config/settings.py 中的 KEYWORDS 调整搜索关键词

支持的数据源:
  - wechat: 微信公众号（搜狗微信搜索）
  - xiaohongshu: 小红书（需要配置 MediaCrawler）
  - zhihu: 知乎（需要配置 MediaCrawler）
  - general: 通用资讯（可扩展）
  - demo: 演示数据（测试用）

处理流程:
  1. 多源采集 → 2. 数据合并(JSON) → 3. AI打分 → 4. 保存打分数据 → 5. Top N筛选 → 6. Markdown报告

输出文件:
  - merged_data/: 采集后的原始合并数据（无评分）
  - scored_data/: 打分后的完整数据（含评分）
  - output/: 最终的 Markdown 日报

日志:
  - 控制台输出: 实时查看
  - 文件日志: logs/agent.log
""")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='教育热点搜集 Agent')
    parser.add_argument('command', nargs='?', default='run',
                       choices=['run', 'start'],
                       help='执行命令: run(单次执行), start(定时调度)')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # 初始化日志
        setup_logger()
        # 立即执行一次
        success = run_collection_task()
        import sys
        sys.exit(0 if success else 1)
    elif args.command == 'start':
        # 启动定时调度
        start_scheduler()


if __name__ == "__main__":
    main()
