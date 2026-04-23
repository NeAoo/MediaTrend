"""
任务监控模块
监控采集任务的执行状态、性能指标和健康状况
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class TaskMetrics:
    """任务执行指标"""
    task_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    status: str  # success, failed, partial
    collected_count: int
    scored_count: int
    final_count: int
    output_file: str
    error_message: Optional[str] = None
    highest_score: float = 0.0
    api_calls: int = 0
    api_tokens_used: int = 0


class TaskMonitor:
    """任务监控器"""

    def __init__(self, metrics_dir: str = "./metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "task_metrics.json"
        self.current_metrics: Optional[TaskMetrics] = None

    def start_task(self, task_id: str) -> TaskMetrics:
        """
        开始记录任务

        Args:
            task_id: 任务标识

        Returns:
            TaskMetrics: 任务指标对象
        """
        self.current_metrics = TaskMetrics(
            task_id=task_id,
            start_time=datetime.now().isoformat(),
            end_time="",
            duration_seconds=0,
            status="running",
            collected_count=0,
            scored_count=0,
            final_count=0,
            output_file=""
        )

        logger.info(f"📊 开始监控任务: {task_id}")
        return self.current_metrics

    def update_metrics(self, **kwargs):
        """更新任务指标"""
        if self.current_metrics:
            for key, value in kwargs.items():
                if hasattr(self.current_metrics, key):
                    setattr(self.current_metrics, key, value)

    def complete_task(self, status: str = "success", error: str = None):
        """
        完成任务记录

        Args:
            status: 任务状态 (success, failed, partial)
            error: 错误信息
        """
        if not self.current_metrics:
            logger.warning("没有正在监控的任务")
            return

        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.current_metrics.start_time)
        duration = (end_time - start_time).total_seconds()

        self.current_metrics.end_time = end_time.isoformat()
        self.current_metrics.duration_seconds = duration
        self.current_metrics.status = status

        if error:
            self.current_metrics.error_message = error

        # 保存指标
        self._save_metrics(self.current_metrics)

        logger.info(f"✅ 任务监控完成: {self.current_metrics.task_id}")
        logger.info(f"   状态: {status}")
        logger.info(f"   耗时: {duration:.1f} 秒")
        logger.info(f"   采集: {self.current_metrics.collected_count} 条")
        logger.info(f"   入选: {self.current_metrics.final_count} 条")

        self.current_metrics = None

    def _save_metrics(self, metrics: TaskMetrics):
        """保存指标到文件"""
        # 读取现有指标
        existing_metrics = []
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    existing_metrics = json.load(f)
            except:
                existing_metrics = []

        # 添加新指标
        metrics_dict = asdict(metrics)
        existing_metrics.append(metrics_dict)

        # 只保留最近 100 条记录
        if len(existing_metrics) > 100:
            existing_metrics = existing_metrics[-100:]

        # 保存
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(existing_metrics, f, ensure_ascii=False, indent=2)

        logger.debug(f"指标已保存到: {self.metrics_file}")

    def get_metrics_summary(self, days: int = 7) -> Dict:
        """
        获取最近 N 天的指标汇总

        Args:
            days: 天数

        Returns:
            Dict: 汇总统计
        """
        if not self.metrics_file.exists():
            return {"message": "暂无监控数据"}

        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                all_metrics = json.load(f)
        except:
            return {"message": "读取指标文件失败"}

        # 过滤最近 N 天的数据
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in all_metrics
            if datetime.fromisoformat(m['start_time']) >= cutoff_time
        ]

        if not recent_metrics:
            return {"message": f"最近 {days} 天无执行记录"}

        # 统计
        total_tasks = len(recent_metrics)
        success_tasks = sum(1 for m in recent_metrics if m['status'] == 'success')
        failed_tasks = sum(1 for m in recent_metrics if m['status'] == 'failed')

        total_collected = sum(m['collected_count'] for m in recent_metrics)
        total_final = sum(m['final_count'] for m in recent_metrics)

        avg_duration = sum(m['duration_seconds'] for m in recent_metrics) / total_tasks

        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "success_tasks": success_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": f"{success_tasks / total_tasks * 100:.1f}%",
            "total_collected": total_collected,
            "total_final": total_final,
            "avg_duration_seconds": f"{avg_duration:.1f}",
            "latest_run": recent_metrics[-1]['start_time'],
        }

    def get_health_status(self) -> Dict:
        """
        获取系统健康状态

        Returns:
            Dict: 健康状态
        """
        summary = self.get_metrics_summary(days=1)

        if "message" in summary:
            return {
                "status": "unknown",
                "message": summary["message"]
            }

        # 检查最近一次执行
        if summary['failed_tasks'] > 0:
            status = "warning"
        elif summary['success_rate'] == "100.0%":
            status = "healthy"
        else:
            status = "degraded"

        return {
            "status": status,
            "last_24h": summary,
            "recommendations": self._get_recommendations(summary)
        }

    def _get_recommendations(self, summary: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        success_rate = float(summary.get('success_rate', '0').replace('%', ''))
        avg_duration = float(summary.get('avg_duration_seconds', '0'))

        if success_rate < 90:
            recommendations.append("⚠️  成功率较低，建议检查数据源可用性")

        if avg_duration > 600:  # 超过 10 分钟
            recommendations.append("⚠️  执行时间较长，建议优化采集效率")

        if summary.get('total_collected', 0) < 30:
            recommendations.append("📊 采集数量不足，建议增加数据源")

        if not recommendations:
            recommendations.append("✅ 系统运行正常")

        return recommendations

    def generate_report(self, output_file: str = None) -> str:
        """
        生成监控报告

        Args:
            output_file: 输出文件路径

        Returns:
            str: 报告内容
        """
        if output_file is None:
            output_file = self.metrics_dir / "monitor_report.md"
        else:
            output_file = Path(output_file)

        summary_7d = self.get_metrics_summary(days=7)
        summary_30d = self.get_metrics_summary(days=30)
        health = self.get_health_status()

        report = f"""# 📊 教育热点采集系统监控报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 🏥 系统健康状态

**状态**: {'🟢 健康' if health['status'] == 'healthy' else '🟡 警告' if health['status'] == 'warning' else '🔴 异常'}

---

## 📈 最近 7 天统计

| 指标 | 数值 |
|------|------|
| 总执行次数 | {summary_7d.get('total_tasks', 0)} 次 |
| 成功次数 | {summary_7d.get('success_tasks', 0)} 次 |
| 失败次数 | {summary_7d.get('failed_tasks', 0)} 次 |
| 成功率 | {summary_7d.get('success_rate', 'N/A')} |
| 总采集内容 | {summary_7d.get('total_collected', 0)} 条 |
| 总入选内容 | {summary_7d.get('total_final', 0)} 条 |
| 平均执行时间 | {summary_7d.get('avg_duration_seconds', 'N/A')} 秒 |

---

## 📊 最近 30 天统计

| 指标 | 数值 |
|------|------|
| 总执行次数 | {summary_30d.get('total_tasks', 0)} 次 |
| 成功次数 | {summary_30d.get('success_tasks', 0)} 次 |
| 失败次数 | {summary_30d.get('failed_tasks', 0)} 次 |
| 成功率 | {summary_30d.get('success_rate', 'N/A')} |
| 总采集内容 | {summary_30d.get('total_collected', 0)} 条 |
| 总入选内容 | {summary_30d.get('total_final', 0)} 条 |

---

## 💡 优化建议

{chr(10).join([f"- {rec}" for rec in health.get('recommendations', [])])}

---

## 📋 最近执行记录

| 时间 | 状态 | 采集数 | 入选数 | 耗时 |
|------|------|--------|--------|------|
"""

        # 添加最近 10 条执行记录
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    all_metrics = json.load(f)

                for metrics in all_metrics[-10:][::-1]:  # 最近的在前
                    status_icon = "✅" if metrics['status'] == 'success' else "❌"
                    start_time = datetime.fromisoformat(metrics['start_time'])

                    report += f"| {start_time.strftime('%m-%d %H:%M')} | {status_icon} | {metrics['collected_count']} | {metrics['final_count']} | {metrics['duration_seconds']:.0f}s |\n"
            except:
                report += "| 暂无记录 | - | - | - | - |\n"

        report += f"""
---

*本报告由教育热点采集系统自动生成*
"""

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"监控报告已生成: {output_file}")
        return str(output_file)