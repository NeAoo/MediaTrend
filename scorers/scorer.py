"""
教育热点内容打分器
使用大模型对采集的内容进行综合评分。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import Dict, List

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
    SCORE_WORKERS,
)
from models.hotspot import EducationHotspot


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
        content = hotspot.content or ""
        prompt = f"""你是一位社会热点公众号选题评估专家，请对下面这一篇内容进行独立评分。

评分目标：
- 判断这篇内容是否值得进入“社会热点 / 公众号选题池”，核心目标是提升整体点击量和传播潜力。
- 只评价这一篇文章，不要和其他文章做相对比较。
- 正文最多 5000 字，必须基于标题、来源、作者/公众号、发布时间、URL、热度指标和正文综合判断。
- 如果内容只是资料下载、纯广告、旧闻搬运、无法核查、夸张承诺，应该明显降分。

评估逻辑：
- 当前第一目标是阅读量、打开率和传播性，不再把每篇内容筛成家长教育稿。
- 优先看当前社会热点事件、公共情绪点、争议点、反常识点、强故事性和可转成公众号长文的话题。
- 候选文章会被 “选题池” 当作“对标母稿”：标题结构、核心热词、冲突设置、叙事顺序、段落节奏和情绪推进越值得模仿，越应该高分。
- 不要因为话题无法自然连接到教育、孩子、家庭或智趣点读而降分；教育/家庭相关只作为弱备注，不进入核心判断。
- 如果内容非常短，不到两百字，没有核心观点，应该明显降分。
- 重点判断普通大众是否会点开、是否看得懂、是否愿意转发或评论。
- 来源可以来自公众号线索，但涉及政策、医疗、教育、公共事件、具体机构和人物时，事实必须可核查。
- 可以有爆款标题节奏和情绪张力，但不能低俗标题党、不能制造恐慌、不能夸大承诺。
- 更偏好：热点明确、冲突/悬念清楚、信息密度高、大众共鸣强、标题有点击点、结构可拆、二次创作空间大的内容。

评分维度（每项 1-10 分）：
1. heat：热点/打开潜力。是否新、是否有社会讨论度、标题和事件是否有点击欲。
2. authority：权威性/可核查性。来源是否可靠，事实是否明确，是否避免不可验证说法。
3. quality：内容质量。信息是否完整、准确、有深度，有没有明显水文、软广或重复空话。
4. resonance：大众共鸣/传播角度。是否有普遍情绪、强场景、冲突、反常识或讨论空间。
5. timeliness：时效性。是否适合今天/最近几天发布，是否处在事件发酵窗口。
6. reference_value：对标价值。是否适合作为后续仿写母稿，标题、开头、冲突、叙事节奏和结尾是否有可借鉴空间。
7. risk_control：风险控制。是否避开医疗/升学/提分绝对承诺、恐吓、未经证实个案、攻击具体机构等风险。

综合评分公式：
overall = heat×0.35 + timeliness×0.18 + resonance×0.18 + reference_value×0.14 + quality×0.08 + authority×0.04 + risk_control×0.03

请严格按照以下 JSON 格式返回评分结果，只返回 JSON，不要其他文字：
{{
  "heat": 8.5,
  "authority": 9.0,
  "quality": 8.0,
  "resonance": 9.5,
  "timeliness": 8.0,
  "reference_value": 8.5,
  "risk_control": 9.0,
  "overall": 8.53,
  "reason": "用1-2句话说明为什么值得或不值得进入候选池",
  "best_angle": "如果值得写，说明最适合对标原文的标题/冲突/叙事角度；不值得则写不建议",
  "risk_notes": ["需要注意的事实、合规或表达风险"]
}}

需要评分的内容：
- 标题: {hotspot.title}
- 来源平台: {hotspot.source}
- 作者/公众号: {hotspot.author or '未知'}
- 发布时间: {hotspot.publish_time.strftime('%Y-%m-%d %H:%M')}
- URL: {hotspot.url or '无'}
- 热度指标: {hotspot.popularity or '未知'}
- 正文: {content}

请开始评分："""

        from openai.types.chat import ChatCompletionMessageParam

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": "你是专业的社会热点选题评估专家，擅长判断内容的点击潜力、公共讨论价值、事实可靠性和传播风险。",
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
