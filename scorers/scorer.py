"""
教育热点内容打分器
使用大模型对采集的内容进行综合评分
"""
from openai import OpenAI
from typing import List, Dict
from loguru import logger
import json

from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from models.hotspot import EducationHotspot


class ContentScorer:
    """内容打分器"""

    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL

    def score_batch(self, hotspots: List[EducationHotspot]) -> List[EducationHotspot]:
        """
        批量对热点内容进行打分

        Args:
            hotspots: 待打分的热点列表

        Returns:
            List[EducationHotspot]: 带评分的热点列表
        """
        logger.info(f"开始对 {len(hotspots)} 条内容进行打分...")

        scored_hotspots = []

        # 分批处理，避免单次请求过长
        batch_size = 5
        for i in range(0, len(hotspots), batch_size):
            batch = hotspots[i:i + batch_size]

            try:
                scored_batch = self._score_single_batch(batch)
                scored_hotspots.extend(scored_batch)

                logger.info(f"已完成第 {i//batch_size + 1} 批打分")

            except Exception as e:
                logger.error(f"第 {i//batch_size + 1} 批打分失败: {e}")
                # 失败的批次，给默认分数
                for hotspot in batch:
                    hotspot.score = 5.0
                    hotspot.score_details = {"error": str(e)}
                    scored_hotspots.append(hotspot)

        logger.info(f"打分完成，共 {len(scored_hotspots)} 条内容")
        return scored_hotspots

    def _score_single_batch(self, batch: List[EducationHotspot]) -> List[EducationHotspot]:
        """
        对单个批次的内容进行打分

        Args:
            batch: 一批热点内容

        Returns:
            List[EducationHotspot]: 带评分的热点列表
        """
        # 构建打分请求内容
        items_text = ""
        for i, hotspot in enumerate(batch, 1):
            items_text += f"""
第{i}条内容:
- 标题: {hotspot.title}
- 来源: {hotspot.source}
- 发布时间: {hotspot.publish_time.strftime('%Y-%m-%d %H:%M')}
- 摘要: {hotspot.content_summary[:200]}
- 热度指标: {hotspot.popularity or '未知'}
"""

        # 构建打分 Prompt
        prompt = f"""你是一位教育领域的内容评估专家，请对以下教育热点内容进行综合评分。

评分维度（每项1-10分）：
1. 热度：内容的关注度和传播度
2. 权威性：信息来源的可靠性和专业性
3. 内容质量：信息的完整性、准确性和深度
4. 家长实用性：对家长群体的实用价值和参考意义
5. 信息时效性：内容的新鲜程度和及时性

综合评分 = (热度×0.2 + 权威性×0.25 + 内容质量×0.25 + 家长实用性×0.2 + 时效性×0.1)

请严格按照以下JSON格式返回评分结果（只返回JSON，不要其他文字）：
{{
  "scores": [
    {{
      "item_index": 1,
      "heat": 8.5,
      "authority": 9.0,
      "quality": 8.0,
      "practicality": 9.5,
      "timeliness": 8.0,
      "overall": 8.65,
      "reason": "简要说明评分理由"
    }}
  ]zhg
}}

需要评分的内容：
{items_text}

请开始评分："""

        try:
            from openai.types.chat import ChatCompletionMessageParam
            
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": "你是专业的教育内容评估专家，擅长判断教育资讯的价值和质量。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # print("Messages=", messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()

            # print("result_text", result_text)
            # 解析 JSON 结果
            scores_data = self._parse_scores(result_text)

            # 将评分赋值给对应的热点（使用 item_index 匹配）
            for idx, hotspot in enumerate(batch, 1):
                key = f"item_{idx}"
                score_info = scores_data.get(key, {})
                
                logger.debug(f"第{idx}条 - 查找key: {key}, 找到数据: {bool(score_info)}, 可用keys: {list(scores_data.keys())}")
                
                if score_info:
                    hotspot.score = score_info.get("overall", 5.0)
                    hotspot.score_details = {
                        "heat": score_info.get("heat", 5.0),
                        "authority": score_info.get("authority", 5.0),
                        "quality": score_info.get("quality", 5.0),
                        "practicality": score_info.get("practicality", 5.0),
                        "timeliness": score_info.get("timeliness", 5.0)
                    }
                    logger.info(f"第{idx}条评分成功: {hotspot.score} | {hotspot.title[:30]}")
                else:
                    # 如果解析失败，给默认分数
                    hotspot.score = 5.0
                    hotspot.score_details = {"note": "解析失败，使用默认分数"}
                    logger.warning(f"第{idx}条内容未找到评分数据，key={key}")

            return batch

        except Exception as e:
            logger.error(f"API调用失败: {e}")
            raise

    def _parse_scores(self, result_text: str) -> Dict:
        """
        解析打分结果
        
        Args:
            result_text: API返回的文本
            
        Returns:
            Dict: 评分数据（格式: {"item_1": {...}, "item_2": {...}}）
        """
        try:
            # 尝试直接解析 JSON
            data = json.loads(result_text)
            
            # 转换为 item_X 格式的字典
            scores_dict = {}
            for item in data.get("scores", []):
                index = item.get("item_index", 0)
                key = f"item_{index}"
                scores_dict[key] = item
            
            return scores_dict
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            
            # 尝试从文本中提取 JSON
            import re
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, result_text)
            
            if match:
                try:
                    json_str = match.group()
                    data = json.loads(json_str)
                    
                    scores_dict = {}
                    for item in data.get("scores", []):
                        index = item.get("item_index", 0)
                        key = f"item_{index}"
                        scores_dict[key] = item
                    
                    return scores_dict
                except Exception as extract_error:
                    logger.error(f"提取JSON失败: {extract_error}")
            
            return {}

    def sort_by_score(self, hotspots: List[EducationHotspot]) -> List[EducationHotspot]:
        """
        按评分降序排序

        Args:
            hotspots: 带评分的热点列表

        Returns:
            List[EducationHotspot]: 排序后的列表
        """
        return sorted(hotspots, key=lambda x: x.score or 0, reverse=True)

    def select_top_n(self, hotspots: List[EducationHotspot], n: int = 10) -> List[EducationHotspot]:
        """
        选取前N个高分内容

        Args:
            hotspots: 已排序的热点列表
            n: 选取数量

        Returns:
            List[EducationHotspot]: Top N 热点
        """
        sorted_hotspots = self.sort_by_score(hotspots)
        top_n = sorted_hotspots[:n]

        logger.info(f"已选取前 {n} 条高分内容，最高分: {top_n[0].score if top_n else 0:.2f}")
        return top_n