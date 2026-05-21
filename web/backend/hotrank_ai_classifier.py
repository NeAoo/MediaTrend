from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from loguru import logger
from openai import OpenAI

from web.backend.hotrank_aggregator import STANDARD_CATEGORIES
from web.backend.hotrank_models import HotrankTrendTopic


MAX_EVIDENCE_IN_PROMPT = 5
MAX_SUMMARY_CHARS = 120
CLASSIFICATION_RESPONSE_TOKENS = 80
JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*\}")
CATEGORY_ALIASES = {
    "其他": "其它",
}
ProgressCallback = Callable[[int, int], None]

DEFAULT_CLASSIFICATION_SYSTEM_PROMPT = (
    "你是中文全网热榜主题分类器。必须只从给定分类列表中选择一个最贴切的分类。"
    "优先根据标题和证据的真实语义判断，不要因为出现“热点、最新、官方、发布、消息”"
    "就归到资讯热点；涉及战机、武器、军队、战争、国家外交、国际政策的内容应归到军事国际。"
    "如果标题和证据无法稳定判断到任何具体分类，必须归到其它。"
    "只输出 JSON，不要输出 Markdown。\n"
    "可选分类：{categories}"
)
DEFAULT_CLASSIFICATION_USER_PROMPT = (
    "请给下面这个聚合热榜趋势分类。\n\n"
    "代表标题：{title}\n"
    "当前关键词分类：{current_category}\n"
    "平台数：{platform_count}\n"
    "证据：\n{evidence}\n\n"
    "输出 JSON，格式必须是：{\"category\":\"分类名\"}"
)


@dataclass(frozen=True)
class HotrankAiClassifierConfig:
    api_key: str
    base_url: str
    model: str
    workers: int
    timeout_seconds: float
    max_retries: int
    max_completion_tokens: int = CLASSIFICATION_RESPONSE_TOKENS
    reasoning_effort: str = ""
    system_prompt: str = DEFAULT_CLASSIFICATION_SYSTEM_PROMPT
    user_prompt_template: str = DEFAULT_CLASSIFICATION_USER_PROMPT


class HotrankAiClassifier:
    def __init__(self, config: HotrankAiClassifierConfig):
        assert config.api_key.strip(), "api_key must not be empty"
        assert config.base_url.strip(), "base_url must not be empty"
        assert config.model.strip(), "model must not be empty"
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    def classify_topics(
        self,
        topics: list[HotrankTrendTopic],
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, str]:
        if not topics:
            return {}

        worker_count = min(max(1, self.config.workers), len(topics))
        logger.info(
            f"开始 AI 热榜主题分类：{len(topics)} 个趋势，并发 {worker_count}，模型 {self.config.model}"
        )
        category_by_topic_id: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_topic = {
                executor.submit(self._classify_one_topic, topic): topic
                for topic in topics
            }
            completed_count = 0
            total_count = len(topics)
            for future in as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    category = future.result()
                except Exception as exc:
                    logger.warning(f"AI 分类失败，保留关键词分类: {topic.title[:50]} | {exc}")
                else:
                    if category:
                        category_by_topic_id[topic.id] = category
                finally:
                    completed_count += 1
                    if progress_callback is not None:
                        progress_callback(completed_count, total_count)

        logger.info(f"AI 热榜主题分类完成：{len(category_by_topic_id)}/{len(topics)} 个趋势有效")
        return category_by_topic_id

    def _classify_one_topic(self, topic: HotrankTrendTopic) -> str:
        request_kwargs = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(topic),
                },
            ],
            "timeout": self.config.timeout_seconds,
            "response_format": {"type": "json_object"},
        }
        if self.config.max_completion_tokens > 0:
            request_kwargs["max_completion_tokens"] = self.config.max_completion_tokens
        if self.config.reasoning_effort:
            request_kwargs["reasoning_effort"] = self.config.reasoning_effort

        try:
            response = self.client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            if "response_format" not in str(exc) and "reasoning_effort" not in str(exc):
                raise
            logger.warning(f"当前模型接口不支持部分参数，去掉后重试: {exc}")
            request_kwargs.pop("response_format", None)
            request_kwargs.pop("reasoning_effort", None)
            response = self.client.chat.completions.create(**request_kwargs)

        raw_text = (response.choices[0].message.content or "").strip()
        category = self._parse_category(raw_text)
        if not category:
            raise ValueError(f"模型返回无法解析为合法分类: {self._snippet(raw_text)}")
        return category

    def _system_prompt(self) -> str:
        categories = "、".join(STANDARD_CATEGORIES)
        template = self.config.system_prompt or DEFAULT_CLASSIFICATION_SYSTEM_PROMPT
        return template.replace("{categories}", categories)

    def _user_prompt(self, topic: HotrankTrendTopic) -> str:
        evidence_lines = []
        for evidence in topic.evidence[:MAX_EVIDENCE_IN_PROMPT]:
            summary = self._snippet(evidence.summary, MAX_SUMMARY_CHARS)
            evidence_lines.append(
                f"- {evidence.channel_name} 第{evidence.rank}名：{evidence.title}"
                f"；热度：{evidence.hot or '未知'}；摘要：{summary or '无'}"
            )
        evidence_text = "\n".join(evidence_lines) if evidence_lines else "无"
        template = self.config.user_prompt_template or DEFAULT_CLASSIFICATION_USER_PROMPT
        return (
            template
            .replace("{title}", topic.title)
            .replace("{current_category}", topic.category)
            .replace("{platform_count}", str(topic.platform_count))
            .replace("{evidence}", evidence_text)
        )

    def _parse_category(self, raw_text: str) -> str:
        data = self._load_json(raw_text)
        raw_category = str(data.get("category", "")).strip()
        raw_category = CATEGORY_ALIASES.get(raw_category, raw_category)
        if not raw_category:
            return ""
        if raw_category in STANDARD_CATEGORIES:
            return raw_category
        for category in sorted(STANDARD_CATEGORIES, key=len, reverse=True):
            if category and category in raw_category:
                return category
        return ""

    def _load_json(self, raw_text: str) -> dict:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            match = JSON_OBJECT_PATTERN.search(raw_text)
            if match is None:
                return {}
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        return parsed if isinstance(parsed, dict) else {}

    def _snippet(self, text: str | None, max_chars: int = 200) -> str:
        compact = " ".join(str(text or "").split())
        if len(compact) <= max_chars:
            return compact
        return compact[: max_chars - 3].rstrip() + "..."
