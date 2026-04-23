## 📊 数据处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                    教育热点搜集 Agent                         │
└─────────────────────────────────────────────────────────────┘

1️⃣  数据采集 (CrawlerManager)
    ├─ 小红书 (xiaohongshu) - MediaCrawler框架 
    ├─ 知乎 (zhihu) - MediaCrawler框架
    ├─ 微信公众号 (wechat) - 搜狗微信搜索
    └─ 通用资讯 (general) - 可扩展
    
    ↓ 输出: List[EducationHotspot] (无评分)

2️⃣  数据合并 (DataMerger)
    ├─ 统一字段格式
    ├─ 统计数据来源
    └─ 生成时间戳文件
    
    ↓ 输出: merged_data/merged_hotspots_YYYYMMDD_HHMMSS.json

3️⃣  AI智能评分 (ContentScorer)
    ├─ 热度 (20%) - 内容关注度和传播度
    ├─ 权威性 (25%) - 信息来源可靠性
    ├─ 内容质量 (25%) - 信息完整性与深度
    ├─ 家长实用性 (20%) - 对家长的参考价值
    └─ 时效性 (10%) - 内容新鲜程度
    
    ↓ 输出: List[EducationHotspot] (含评分)

4️⃣  保存评分数据 (DataMerger) ⭐
    ├─ 保留完整评分详情
    └─ 便于后续分析
    
    ↓ 输出: scored_data/scored_hotspots_YYYYMMDD_HHMMSS.json

5️⃣  Top N 筛选 (ContentScorer)
    ├─ 按综合评分降序排序
    └─ 选取前N条高分内容 (默认10条)
    
    ↓ 输出: List[EducationHotspot] (Top 10)

6️⃣  Markdown报告生成 (MarkdownGenerator)
    ├─ 统计概览信息
    ├─ 格式化热点详情
    ├─ 添加推荐理由
    └─ 生成分类标签
    
    ↓ 输出: output/教育热点日报_YYYYMMDD.md
```

## 🗂️ 数据结构

### EducationHotspot 模型

```python
class EducationHotspot(BaseModel):
    """教育热点内容数据模型"""
    
    # 必填字段
    title: str                      # 标题
    source: str                     # 来源平台 (wechat/zhihu/xiaohongshu等)
    publish_time: datetime          # 发布时间
    content_summary: str            # 内容摘要
    url: str                        # 原文链接
    
    # 可选字段
    author: Optional[str]           # 作者/发布者
    popularity: Optional[float]     # 热度指标（点赞、阅读等）
    cover_image: Optional[str]      # 封面图片链接
    image_list: List[str]           # 完整图片列表
    tags: List[str]                 # 标签列表
    
    # 评分字段（采集阶段为None，评分后填充）
    score: Optional[float]          # 综合评分 (0-10)
    score_details: Optional[dict]   # 详细评分维度
```

### 合并数据文件格式

#### 1. 采集后合并数据 (`merged_data/`)

**文件路径**: `merged_data/merged_hotspots_YYYYMMDD_HHMMSS.json`

**特点**: 
- ✅ 包含所有采集的原始数据
- ❌ 评分字段为 `null`（尚未评分）

```json
{
  "metadata": {
    "generated_at": "2026-04-23T00:43:27.445762",
    "total_count": 18,
    "source_statistics": {
      "zhihu": 18
    },
    "sources": ["zhihu"]
  },
  "hotspots": [
    {
      "title": "22考研数学一143分经验贴(针对27考研进行了更新)",
      "source": "zhihu",
      "publish_time": "2022-04-01T06:39:59",
      "content_summary": "27邂逅遗憾考研数学交流q群...",
      "url": "https://zhuanlan.zhihu.com/p/491196569",
      "author": "邂逅遗憾",
      "popularity": 19774.0,
      "cover_image": null,
      "image_list": [],
      "tags": ["教育", "知乎"],
      "score": null,              // ⚠️ 采集阶段为空
      "score_details": null       // ⚠️ 采集阶段为空
    }
  ]
}
```

#### 2. 评分后数据 (`scored_data/`) ⭐ 新增

**文件路径**: `scored_data/scored_hotspots_YYYYMMDD_HHMMSS.json`

**特点**: 
- ✅ 包含完整的AI评分结果
- ✅ 包含详细的评分维度分解

```json
{
  "metadata": {
    "generated_at": "2026-04-23T00:44:21.734424",
    "total_count": 18,
    "source_statistics": {
      "zhihu": 18
    },
    "sources": ["zhihu"]
  },
  "hotspots": [
    {
      "title": "22考研数学一143分经验贴(针对27考研进行了更新)",
      "source": "zhihu",
      "publish_time": "2022-04-01T06:39:59",
      "content_summary": "27邂逅遗憾考研数学交流q群...",
      "url": "https://zhuanlan.zhihu.com/p/491196569",
      "author": "邂逅遗憾",
      "popularity": 19774.0,
      "cover_image": null,
      "image_list": [],
      "tags": ["教育", "知乎"],
      "score": 7.25,              // ✅ AI综合评分
      "score_details": {          // ✅ 详细评分维度
        "heat": 7.8,              // 热度
        "authority": 5.5,         // 权威性
        "quality": 7.9,           // 内容质量
        "practicality": 8.6,      // 家长实用性
        "timeliness": 6.5         // 时效性
      }
    }
  ]
}
```

**评分计算公式**:
```
综合评分 = 热度×0.2 + 权威性×0.25 + 内容质量×0.25 + 家长实用性×0.2 + 时效性×0.1
```

---

### 📱 小红书原始数据字段

小红书平台通过 MediaCrawler 采集的原始 JSONL 数据包含以下字段：

```json
{
  "note_id": "69e6d699000000001a022885",      // 笔记唯一ID
  "type": "normal",                              // 笔记类型 (normal/video)
  "title": "湖北楚源教育·时政天天练（4.21）",     // 笔记标题
  "desc": "#湖北楚源教育时政天天练[话题]# ...",   // 笔记正文描述与话题标签
  "video_url": "",                               // 视频资源链接（视频笔记才有）
  "time": 1776735897000,                         // 发布时间（毫秒时间戳）
  "last_update_time": 1776735897000,             // 最后更新时间（毫秒时间戳）
  "user_id": "69cf12c90000000033019a3f",         // 发布作者用户ID
  "nickname": "湖北楚源教育｜天天练",              // 作者昵称
  "avatar": "https://sns-avatar-qc.xhscdn.com/...", // 作者头像图片链接
  "liked_count": "37",                           // 点赞数量
  "collected_count": "18",                       // 收藏数量
  "comment_count": "",                           // 评论数量
  "share_count": "1",                            // 分享数量
  "ip_location": "湖北",                         // 发布IP属地
  "image_list": "http://...,http://...",         // 配图链接集合（多图逗号分隔）
  "tag_list": "湖北楚源教育时政天天练,湖北楚源教育,时政,...", // 话题标签列表（逗号分隔）
  "last_modify_ts": 1776874508037,               // 爬虫采集时间（毫秒时间戳）
  "note_url": "https://www.xiaohongshu.com/...", // 笔记网页原生链接
  "source_keyword": "学习方法",                   // 采集检索源关键词
  "xsec_token": "ABdXvbvuNzqidIrLwVZT0Zl4..."    // 页面鉴权访问令牌
}
```

**字段说明表**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `note_id` | string | 笔记唯一标识 | `"69e6d699000000001a022885"` |
| `type` | string | 内容类型 | `"normal"` (图文) / `"video"` (视频) |
| `title` | string | 笔记标题 | `"考研数学复习指南"` |
| `desc` | string | 正文描述，包含话题标签 | `"#考研[话题]# #数学[话题]#"` |
| `video_url` | string | 视频链接（仅视频笔记） | `"https://..."` |
| `time` | number | 发布时间（毫秒时间戳） | `1776735897000` |
| `last_update_time` | number | 最后更新时间（毫秒时间戳） | `1776735897000` |
| `user_id` | string | 作者用户ID | `"69cf12c90000000033019a3f"` |
| `nickname` | string | 作者昵称 | `"教育博主"` |
| `avatar` | string | 作者头像URL | `"https://..."` |
| `liked_count` | string | 点赞数 | `"1234"` 或 `"1.2万"` |
| `collected_count` | string | 收藏数 | `"567"` |
| `comment_count` | string | 评论数 | `"89"` |
| `share_count` | string | 分享数 | `"45"` |
| `ip_location` | string | IP属地 | `"北京"` |
| `image_list` | string | 图片URL列表（逗号分隔） | `"url1,url2,url3"` |
| `tag_list` | string | 标签列表（逗号分隔） | `"考研,教育,学习"` |
| `last_modify_ts` | number | 爬虫采集时间（毫秒时间戳） | `1776874508037` |
| `note_url` | string | 笔记完整URL | `"https://www.xiaohongshu.com/..."` |
| `source_keyword` | string | 搜索关键词 | `"学习方法"` |
| `xsec_token` | string | 访问令牌 | `"ABdXvbvuNzq..."` |

**映射到 EducationHotspot**:
- `title` → `title`
- `nickname` → `author`
- `time` (转换为datetime) → `publish_time`
- `desc` → `content_summary`
- `note_url` → `url`
- `liked_count` (解析为数字) → `popularity`
- `image_list` (分割为数组) → `image_list`
- `tag_list` (分割为数组) → `tags`

---

### 📚 知乎原始数据字段

知乎平台通过 MediaCrawler 采集的原始 JSONL 数据包含以下字段：

```json
{
  "content_id": "491196569",                      // 回答内容唯一ID
  "content_type": "article",                      // 内容类型 (article/answer)
  "content_text": "27邂逅遗憾考研数学交流q群...",  // 回答正文文本内容
  "content_url": "https://zhuanlan.zhihu.com/p/491196569", // 回答网页链接
  "question_id": "123456789",                     // 所属问题ID
  "title": "22考研数学一143分经验贴",              // 问题标题
  "desc": "问题详细描述补充内容",                  // 问题详细描述
  "created_time": 1648795199,                     // 发布时间（秒时间戳）
  "updated_time": 1648795199,                     // 最后编辑时间（秒时间戳）
  "voteup_count": 1234,                           // 赞同（点赞）数量
  "comment_count": 89,                            // 评论数量
  "source_keyword": "考研",                        // 采集检索源关键词
  "user_id": "user_abc123",                       // 回答作者用户ID
  "user_link": "https://www.zhihu.com/people/...", // 作者个人主页链接
  "user_nickname": "邂逅遗憾",                     // 作者昵称
  "user_avatar": "https://picx.zhimg.com/...",    // 作者头像图片链接
  "user_url_token": "abc123def456",                // 作者主页URL唯一标识
  "last_modify_ts": 1776874508037                 // 爬虫采集时间（毫秒时间戳）
}
```

**字段说明表**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `content_id` | string | 内容唯一ID | `"491196569"` |
| `content_type` | string | 内容类型 | `"article"` (文章) / `"answer"` (回答) |
| `content_text` | string | 正文文本内容 | `"考研数学经验分享..."` |
| `content_url` | string | 内容网页链接 | `"https://zhuanlan.zhihu.com/p/..."` |
| `question_id` | string | 所属问题ID | `"123456789"` |
| `title` | string | 问题标题 | `"考研数学如何复习？"` |
| `desc` | string | 问题详细描述 | `"我想了解考研数学的复习方法..."` |
| `created_time` | number | 发布时间（秒时间戳） | `1648795199` |
| `updated_time` | number | 最后编辑时间（秒时间戳） | `1648795199` |
| `voteup_count` | number | 赞同数 | `1234` |
| `comment_count` | number | 评论数 | `89` |
| `source_keyword` | string | 搜索关键词 | `"考研"` |
| `user_id` | string | 作者用户ID | `"user_abc123"` |
| `user_link` | string | 作者主页链接 | `"https://www.zhihu.com/people/..."` |
| `user_nickname` | string | 作者昵称 | `"邂逅遗憾"` |
| `user_avatar` | string | 作者头像URL | `"https://picx.zhimg.com/..."` |
| `user_url_token` | string | 作者URL标识 | `"abc123def456"` |
| `last_modify_ts` | number | 爬虫采集时间（毫秒时间戳） | `1776874508037` |

**映射到 EducationHotspot**:
- `title` → `title`
- `user_nickname` → `author`
- `created_time` (转换为datetime) → `publish_time`
- `content_text` → `content_summary`
- `content_url` → `url`
- `voteup_count + comment_count * 2` → `popularity` (热度计算)
- 默认标签 → `tags: ["教育", "知乎"]`
- 知乎通常无图片 → `cover_image: null`, `image_list: []`

---

### 🔄 数据转换流程

```
原始数据 (JSONL)
    ↓
平台特定处理器 (XHSDataProcessor / ZhihuCrawler.parse_item)
    ↓
字段映射与清洗
    ↓
EducationHotspot 标准模型
    ↓
DataMerger 合并为统一 JSON
    ↓
ContentScorer AI 智能评分
    ↓
MarkdownGenerator 生成报告
```

