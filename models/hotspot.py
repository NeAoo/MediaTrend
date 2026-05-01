"""
教育热点数据模型
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List

CONTENT_MAX_LENGTH = 3000


class EducationHotspot(BaseModel):
    """教育热点内容数据模型"""
    
    title: str = Field(..., description="标题")
    source: str = Field(..., description="来源平台")
    publish_time: datetime = Field(..., description="发布时间")
    content: str = Field("", description="完整正文，最多3000字")
    url: str = Field(..., description="原文链接")

    author: Optional[str] = Field(None, description="作者/发布者")
    popularity: Optional[float] = Field(None, description="热度指标（点赞、阅读等）")
    cover_image: Optional[str] = Field(None, description="封面图片链接")
    image_list: Optional[List[str]] = Field(default_factory=list, description="完整图片列表")
    tags: list = Field(default_factory=list, description="标签列表")
    
    # 打分相关字段
    score: Optional[float] = Field(None, description="综合评分")
    score_details: Optional[dict] = Field(None, description="详细评分维度")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator("content", mode="before")
    @classmethod
    def truncate_content(cls, value) -> str:
        if value is None:
            return ""
        return str(value)[:CONTENT_MAX_LENGTH]


class CollectionResult(BaseModel):
    """采集结果封装"""
    
    success_count: int = Field(0, description="成功采集数量")
    failed_count: int = Field(0, description="失败数量")
    items: list[EducationHotspot] = Field(default_factory=list, description="采集到的热点列表")
    error_messages: list[str] = Field(default_factory=list, description="错误信息列表")
