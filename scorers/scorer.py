"""
教育热点内容打分器
使用大模型对采集的内容进行综合评分。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from openai import OpenAI

from config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_COMPLETION_TOKENS,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_REASONING_EFFORT,
    LLM_TIMEOUT_SECONDS,
    SCORING_PARSE_FAILURE_SCORE,
    SCORING_SYSTEM_PROMPT_PATH,
    SCORING_USER_PROMPT_PATH,
    SCORE_WORKERS,
)
from models.hotspot import EducationHotspot


SCORING_TEMPLATE_FIELDS = {
    "title",
    "source",
    "author",
    "publish_time",
    "url",
    "popularity",
    "content",
}


def _read_prompt_file(path: str) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"评分 prompt 文件不存在: {prompt_path}")
    content = prompt_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"评分 prompt 文件为空: {prompt_path}")
    return content


def render_scoring_prompt(template: str, hotspot: EducationHotspot) -> str:
    """Render known placeholders without touching JSON braces in the prompt."""
    values: dict[str, Any] = {
        "title": hotspot.title,
        "source": hotspot.source,
        "author": hotspot.author or "未知",
        "publish_time": hotspot.publish_time.strftime("%Y-%m-%d %H:%M"),
        "url": hotspot.url or "无",
        "popularity": hotspot.popularity if hotspot.popularity is not None else "未知",
        "content": hotspot.content or "",
    }
    rendered = template
    for field_name in SCORING_TEMPLATE_FIELDS:
        rendered = rendered.replace("{" + field_name + "}", str(values[field_name]))
    return rendered


class ContentScorer:
    """内容打分器。"""

    def __init__(self):
        if not LLM_API_KEY:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
        )
        self.model = LLM_MODEL
        self.system_prompt = _read_prompt_file(SCORING_SYSTEM_PROMPT_PATH)
        self.user_prompt_template = _read_prompt_file(SCORING_USER_PROMPT_PATH)

    def score_batch(self, hotspots: List[EducationHotspot]) -> List[EducationHotspot]:
        if not hotspots:
            return []

        worker_count = min(SCORE_WORKERS, len(hotspots))
        logger.info(f"开始对 {len(hotspots)} 条内容进行单篇独立打分，并发线程数: {worker_count}")
        scored_hotspots: list[EducationHotspot | None] = [None] * len(hotspots)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_index = {
                executor.submit(self._score_single_item, hotspot, index + 1): index
                for index, hotspot in enumerate(hotspots)
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                hotspot = hotspots[index]
                try:
                    scored_hotspots[index] = future.result()
                except Exception as exc:
                    logger.error(f"第 {index + 1} 条打分失败: {exc}")
                    hotspot.score = SCORING_PARSE_FAILURE_SCORE
                    hotspot.score_details = {
                        "error": str(exc),
                        "scoring_failed": True,
                    }
                    scored_hotspots[index] = hotspot

        results = [hotspot for hotspot in scored_hotspots if hotspot is not None]
        logger.info(f"打分完成，共 {len(results)} 条内容")
        return results

    def _score_single_item(self, hotspot: EducationHotspot, item_number: int) -> EducationHotspot:
        logger.info(f"第{item_number}条开始评分: {hotspot.title[:30]}")
        prompt = render_scoring_prompt(self.user_prompt_template, hotspot)

        from openai.types.chat import ChatCompletionMessageParam

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        request_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "timeout": LLM_TIMEOUT_SECONDS,
        }
        if LLM_MAX_COMPLETION_TOKENS > 0:
            request_kwargs["max_completion_tokens"] = LLM_MAX_COMPLETION_TOKENS
        if LLM_REASONING_EFFORT:
            request_kwargs["reasoning_effort"] = LLM_REASONING_EFFORT

        try:
            response = self.client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            if "reasoning_effort" not in str(exc):
                raise
            logger.warning(f"当前模型接口不支持 reasoning_effort，去掉该参数后重试: {exc}")
            request_kwargs.pop("reasoning_effort", None)
            response = self.client.chat.completions.create(**request_kwargs)

        result_text = (response.choices[0].message.content or "").strip()
        if not result_text:
            usage = response.usage.model_dump() if response.usage else None
            logger.warning(
                f"第{item_number}条模型返回空内容；"
                f"finish_reason={response.choices[0].finish_reason}; usage={usage}"
            )
        score_info = self._parse_score(result_text)

        if score_info:
            hotspot.score = self._score_value(score_info, "overall", 5.0)
            hotspot.score_details = {
                "heat": self._score_value(score_info, "heat", 5.0),
                "authority": self._score_value(score_info, "authority", 5.0),
                "quality": self._score_value(score_info, "quality", 5.0),
                "resonance": self._score_value(
                    score_info,
                    "resonance",
                    self._score_value(score_info, "practicality", 5.0),
                ),
                "timeliness": self._score_value(score_info, "timeliness", 5.0),
                "reference_value": self._score_value(
                    score_info,
                    "reference_value",
                    self._score_value(score_info, "education_family_relevance", 5.0),
                ),
                "risk_control": self._score_value(score_info, "risk_control", 5.0),
                "reason": score_info.get("reason", ""),
                "best_angle": score_info.get("best_angle", ""),
                "risk_notes": score_info.get("risk_notes", []),
            }
            logger.info(f"第{item_number}条评分成功: {hotspot.score:.2f} | {hotspot.title[:30]}")
        else:
            hotspot.score = SCORING_PARSE_FAILURE_SCORE
            hotspot.score_details = {
                "error": "score_json_parse_failed",
                "scoring_failed": True,
                "raw_response_snippet": self._response_snippet(result_text),
            }
            logger.warning(
                f"第{item_number}条内容未解析到评分结果，"
                f"按 {SCORING_PARSE_FAILURE_SCORE:.1f} 分处理；"
                f"模型原始返回片段: {self._response_snippet(result_text)}"
            )

        return hotspot

    def _parse_score(self, result_text: str) -> Dict:
        data = self._load_json_result(result_text)
        if not data:
            return {}
        if isinstance(data.get("scores"), list) and data["scores"]:
            first_score = data["scores"][0]
            return first_score if isinstance(first_score, dict) else {}
        if isinstance(data.get("score"), dict):
            return data["score"]
        if "overall" in data:
            return data
        return {}

    def _load_json_result(self, result_text: str) -> Dict:
        try:
            return json.loads(result_text)
        except json.JSONDecodeError as exc:
            logger.warning(f"JSON 解析失败: {exc}")

        import re

        match = re.search(r"\{[\s\S]*\}", result_text)
        if not match:
            return {}

        try:
            return json.loads(match.group())
        except Exception as exc:
            logger.error(f"提取 JSON 失败: {exc}")
            return {}

    def _score_value(self, score_info: Dict, key: str, default: float) -> float:
        try:
            value = float(score_info.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(1.0, min(10.0, value))

    def _response_snippet(self, result_text: str, max_chars: int = 500) -> str:
        text = " ".join(str(result_text or "").split())
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def sort_by_score(self, hotspots: List[EducationHotspot]) -> List[EducationHotspot]:
        return sorted(hotspots, key=lambda x: x.score or 0, reverse=True)

    def select_top_n(self, hotspots: List[EducationHotspot], n: int = 10) -> List[EducationHotspot]:
        if n <= 0:
            logger.warning(f"选择数量 n={n} 无效，返回空列表")
            return []

        sorted_hotspots = self.sort_by_score(hotspots)
        if len(sorted_hotspots) <= n:
            logger.info(f"内容总数 {len(sorted_hotspots)} 条，不足或等于 {n} 条，全部入选")
            return sorted_hotspots

        cutoff_score = sorted_hotspots[n - 1].score or 0
        selected = [
            hotspot
            for hotspot in sorted_hotspots
            if (hotspot.score or 0) >= cutoff_score
        ]
        extra_count = len(selected) - n
        if extra_count > 0:
            logger.info(
                f"已选取至少前 {n} 条高分内容；第 {n} 名分数为 {cutoff_score:.2f}，"
                f"同分追加 {extra_count} 条，最终 {len(selected)} 条"
            )
        else:
            logger.info(f"已选取前 {n} 条高分内容，最高分: {selected[0].score if selected else 0:.2f}")
        return selected
