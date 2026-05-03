# 教育热点搜集 Agent

智能教育热点采集与分析系统，自动从多平台采集教育类热点内容，通过AI大模型智能打分排序，生成家长友好的Markdown日报。

## 📁 项目结构

```
AITrend/
├── main.py                      # 主入口文件
├── config/
│   ├── __init__.py
│   └── settings.py              # 主项目配置文件
├── crawlers/                    # 爬虫模块
│   ├── __init__.py
│   ├── base.py                  # 爬虫基类
│   ├── manager.py               # 爬虫管理器
│   ├── wechat.py                # 微信公众号爬虫
│   ├── zhihu.py                 # 知乎爬虫（调用 MediaCrawler）
│   └── xiaohongshu.py           # 小红书爬虫（调用 MediaCrawler）
├── merger/                      # 数据合并模块
│   ├── __init__.py
│   └── data_merger.py           # 数据合并器
├── scorers/                     # 评分模块
│   ├── __init__.py
│   └── scorer.py                # 内容评分器
├── formatters/                  # 格式化输出模块
│   ├── __init__.py
│   └── markdown.py              # Markdown生成器
├── models/                      # 数据模型
│   ├── __init__.py
│   └── hotspot.py               # 热点数据模型
├── schedulers/                  # 调度模块
│   ├── __init__.py
│   ├── scheduler.py             # 定时调度器
│   └── monitor.py               # 监控模块
├── MediaCrawler/                # 第三方爬虫框架（小红书、知乎等）
│   ├── config/
│   │   └── base_config.py       # MediaCrawler 配置
│   └── ...
├── merged_data/                 # 采集后合并数据（无评分）
├── scored_data/                 # 评分后数据（含评分）⭐
├── output/                      # Markdown报告输出目录
├── logs/                        # 日志文件
├── requirements.txt             # 项目依赖包列表
├── .env                         # 环境变量配置
└── README.md                    # 项目说明文档
```

## ✨ 核心功能

- **多源数据采集**: 支持微信公众号、知乎、小红书等多个平台
- **智能去重**: 基于标题和URL的自动化去重机制
- **AI智能评分**: 使用大模型对内容进行多维度综合评分
- **Top N筛选**: 自动筛选高分优质内容
- **Markdown报告**: 生成格式精美、家长友好的日报文档
- **定时调度**: 支持每日自动执行，持续监控教育热点

## 🚀 快速开始

### 环境要求

- Python 3.10+ （推荐 3.11）
- OpenAI API Key 或其他兼容的大模型API
- Chrome 浏览器（版本 >= 144）

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository_url>
cd AITrend
```

#### 2. 创建虚拟环境

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

如果你要启用 `xiaohongshu` 或 `zhihu`，还需要额外安装 `MediaCrawler` 依赖：

```bash
pip install -r MediaCrawler/requirements.txt
```

#### 4. 配置环境变量

参考 `.env.example` 创建 `.env` 文件。第一次本地运行建议先保留：

```env
ENABLED_SOURCES=wechat
```

完整示例：

```env
# 大模型 API 配置
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.5

# 本地第一次运行建议先只开 wechat
ENABLED_SOURCES=wechat
WECHAT_SEARCH_KEYWORDS=教育改革,中考
WECHAT_MAX_RESULTS_PER_KEYWORD=8
WECHAT_MP_ACCOUNTS=中国教育报,人民教育
WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT=10
WECHAT_MP_LOOKBACK_DAYS=7
WECHAT_MP_HEADLESS=false
WECHAT_MP_SLOW_MO_MS=300
WECHAT_MP_ACTION_DELAY_SECONDS=1.5
WECHAT_MP_ARTICLE_DELAY_SECONDS=3
WECHAT_MP_PAGE_DELAY_SECONDS=4
WECHAT_MP_ACCOUNT_DELAY_SECONDS=8
WECHAT_MP_RAW_OUTPUT_DIR=./raw_data/wechat_mp
XIAOHONGSHU_SEARCH_KEYWORDS=教育改革,中考
XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD=20
ZHIHU_SEARCH_KEYWORDS=教育改革,中考
ZHIHU_MAX_RESULTS_PER_KEYWORD=20

# 输出目录
OUTPUT_DIR=./output

# MediaCrawler Cookie 配置（可选，目前使用扫码登录）
XIAOHONGSHU_COOKIE=你的小红书Cookie
ZHIHU_COOKIE=你的知乎Cookie
```

> 💡 **如何获取 Cookie**：
> 1. 访问 https://www.xiaohongshu.com/ 或 https://www.zhihu.com/
> 2. 登录账号
> 3. 按 F12 打开开发者工具 → Application → Cookies
> 4. 复制所有 Cookie 字符串粘贴到 `.env` 文件

#### 5. 配置 Chrome / Playwright

只跑 `wechat` 时，不需要手动开 Chrome CDP。执行过下面命令即可：

```bash
playwright install chromium
```

如果你要跑 `MediaCrawler` 的 `xiaohongshu` / `zhihu`，它内部会使用自己的浏览器控制逻辑，第一次登录通常需要扫码。

#### 6. 配置数据源

优先在 `.env` 中配置，不建议直接改 `config/settings.py`。

```env
# 推荐第一步
ENABLED_SOURCES=wechat

# 之后按需开启
# ENABLED_SOURCES=wechat,xiaohongshu
# ENABLED_SOURCES=wechat,wechat_mp
# ENABLED_SOURCES=wechat,zhihu
# ENABLED_SOURCES=wechat,general
```

### 运行方式

#### 方式1: 单次执行

立即执行一次完整采集 + 打分任务：

```bash
python main.py run
```

如果你还没填 `LLM_API_KEY`，先跑只采集模式：

```bash
python main.py search
```

只跑指定来源：

```bash
python main.py search --sources wechat
python main.py search --sources wechat_mp
python main.py search --sources wechat,xiaohongshu,zhihu
python main.py search --sources all
```

临时覆盖本次运行关键词：

```bash
python main.py search --sources wechat --keywords 中考,高考
```

单源调试脚本：

```bash
python scripts/search_wechat.py
python scripts/search_wechat_mp.py --accounts 中国教育报,人民教育
python scripts/search_xiaohongshu.py
python scripts/search_zhihu.py
```

`wechat_mp` 是微信公众平台后台采集，按 `WECHAT_MP_ACCOUNTS` 中的固定公众号名称抓最近文章。首次运行会打开浏览器，需要你扫码登录公众号后台；登录态默认保存到 `./browser_data/wechat_mp_state.json`。

**执行流程**：
1. 从多个平台采集教育热点内容
2. 合并多源数据为统一JSON文件
3. 使用AI对内容进行智能评分
4. 筛选至少前N条高分内容；若第N名后续文章同分，则并列保留
5. 生成Markdown日报，并额外导出 longxia 可读取的人工候选 md

#### longxia 候选自动投放

`python main.py run` 默认会把最终入选的高分内容拆成 longxia 需要的候选文件：

```text
output/longxia_trend_candidates/YYYY-MM-DD/
  YYYY-MM-DD_01.md
  YYYY-MM-DD_02.md
  ...
  manifest.json
```

每个 md 对应一篇候选文章，只包含标题、账号、来源、发布时间、原文链接和正文；正文默认最多 `LONGXIA_CANDIDATE_CONTENT_MAX_CHARS=5000` 字。`manifest.json` 用于记录当天筛选到的候选列表，longxia 不会把它当作候选文章读取。Mac 本地每天 06:00 自动运行并上传到 longxia：

```bash
chmod +x scripts/install_macos_daily_longxia_job.sh
./scripts/install_macos_daily_longxia_job.sh
```

手动跑一次并上传：

```bash
scripts/run_daily_longxia_candidates.sh
```

卸载本机定时任务：

```bash
scripts/uninstall_macos_daily_longxia_job.sh
```

定时任务日志：

```text
logs/mac_daily_longxia_candidates.log
logs/launchd_longxia_candidates.out.log
logs/launchd_longxia_candidates.err.log
```

**输出示例**：
```
============================================================
教育热点搜集 Agent 启动
============================================================

第一步：开始采集教育热点...
✓ 成功采集: 中考英语核心考点:名词复数... (距今 1.3 小时)
✓ 成功采集: 26中考化学新趋势跨学科专项训练14题有答案... (距今 0.1 小时)

第二步：合并多源数据为统一JSON文件...
✅ 数据合并完成

第三步：开始对内容进行智能打分...
开始单篇独立打分，并发线程数: 5

第四步：保存打分后的数据到 scored_data...
✅ 打分数据已保存

第五步：筛选至少前 10 条高分内容，同分并列保留...
筛选完成，最终选取 10 条优质内容

第六步：生成 Markdown 日报...
日报生成成功！

============================================================
今日成果:
   - 采集内容: 18 条
   - 最终入选: 10 条
   - 最高评分: 8.00
   - 输出文件: output/教育热点日报_20260423.md
============================================================
```

#### 方式2: 定时调度

启动定时任务，每天自动执行（默认每天8:00）：

```bash
python main.py start
```

修改执行时间，编辑 `config/settings.py`:

```python
SCHEDULE_TIME = "08:00"  # 改为其他时间，如 "20:00"
```

## 📝 输出文件说明

### 1. 合并数据文件

**目录**: `merged_data/`  
**格式**: `merged_hotspots_YYYYMMDD_HHMMSS.json`  
**内容**: 采集后的原始数据，**不包含评分**

### 2. 评分数据文件 ⭐

**目录**: `scored_data/`  
**格式**: `scored_hotspots_YYYYMMDD_HHMMSS.json`  
**内容**: 包含完整的AI评分结果和详细评分维度

### 3. Markdown日报

**目录**: `output/`  
**格式**: `教育热点日报_YYYYMMDD.md`  
**内容**: 格式精美的日报文档，包含：
- 📊 热点概览统计
- 🔥 Top 10 热点详情（含评分、推荐理由、图片预览）
- 💡 温馨提示
- 📌 数据来源说明

### 4. 日志文件

**目录**: `logs/`  
**格式**: `agent.log`  
**内容**: 详细的执行日志，支持日志切割和自动清理

实时查看日志：
```bash
tail -f logs/agent.log
```

## ⚙️ 配置说明

### 环境变量 (.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_API_KEY` | 大模型API密钥 | 空 |
| `LLM_BASE_URL` | API基础URL | `https://api.openai.com/v1` |
| `LLM_MODEL` | 使用的模型名称 | `gpt-4` |
| `OUTPUT_DIR` | 输出目录 | `./output` |

### 应用配置 (config/settings.py)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `INITIAL_COLLECT_COUNT` | 初始采集数量 | 30 |
| `TOP_N_SELECT_COUNT` | 最终筛选Top N | 10 |
| `WECHAT_SEARCH_KEYWORDS` | 搜狗公众号关键词搜索词 | 空 |
| `WECHAT_MAX_RESULTS_PER_KEYWORD` | 公众号每个关键词最多解析条数 | 8 |
| `WECHAT_MP_ACCOUNTS` | 微信公众平台后台固定公众号列表 | 空 |
| `WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT` | 后台模式每个公众号最多采集篇数 | 10 |
| `WECHAT_MP_LOOKBACK_DAYS` | 后台模式采集最近几天文章 | 7 |
| `WECHAT_MP_HEADLESS` | 后台模式是否无头运行；重新扫码时改为 `false` | `false` |
| `WECHAT_MP_SLOW_MO_MS` | Playwright 每个动作额外放慢毫秒数 | 300 |
| `WECHAT_MP_ACTION_DELAY_SECONDS` | 普通点击/输入后的等待秒数 | 1.5 |
| `WECHAT_MP_ARTICLE_DELAY_SECONDS` | 每解析一篇文章后的等待秒数 | 3 |
| `WECHAT_MP_PAGE_DELAY_SECONDS` | 翻页和搜索结果加载后的等待秒数 | 4 |
| `WECHAT_MP_ACCOUNT_DELAY_SECONDS` | 切换到下一个公众号前的等待秒数 | 8 |
| `WECHAT_MP_RAW_OUTPUT_DIR` | 后台模式按日期/公众号保存原始数据的目录 | `./raw_data/wechat_mp` |
| `WECHAT_MP_STORAGE_STATE` | 后台模式登录态保存路径 | `./browser_data/wechat_mp_state.json` |
| `XIAOHONGSHU_SEARCH_KEYWORDS` | 小红书搜索关键词 | 空 |
| `XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD` | 小红书每个关键词最多采集条数 | 20 |
| `ZHIHU_SEARCH_KEYWORDS` | 知乎搜索关键词 | 空 |
| `ZHIHU_MAX_RESULTS_PER_KEYWORD` | 知乎每个关键词最多采集条数 | 20 |
| `TIME_RANGE_MIN` | 最小时间范围(小时) | 0 |
| `TIME_RANGE_MAX` | 最大时间范围(小时) | 24 |
| `ENABLED_SOURCES` | 默认启用的数据源 | `wechat` |
| `SCHEDULE_TIME` | 定时执行时间 | `"08:00"` |
| `LOG_LEVEL` | 日志级别 | `"INFO"` |
| `LOG_FILE` | 日志文件路径 | `"./logs/agent.log"` |

## 📊 评分体系详解

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 🔥 热度 | 20% | 内容的关注度、点赞数、阅读量等传播指标 |
| 👑 权威性 | 25% | 信息来源的可靠性、专业性、官方认证等 |
| 📚 内容质量 | 25% | 信息的完整性、准确性、深度和逻辑性 |
| 💡 家长实用性 | 20% | 对家长群体的实用价值和参考意义 |
| ⏰ 时效性 | 10% | 内容的新鲜程度和及时性 |

### 评分等级

- **8.5-10.0**: ⭐⭐⭐ 强烈推荐，极具价值
- **7.5-8.5**: ⭐⭐ 值得关注，优质内容
- **6.0-7.5**: ⭐ 具有参考价值，可作了解
- **<6.0**: 一般性内容，建议结合其他信息源

### AI 打分机制

系统使用 OpenAI 兼容的 API 格式，对每篇内容进行独立智能评分。

**评分流程**：
1. 每篇文章单独发送给大模型，正文最多保留 5000 字
2. 默认用 `SCORE_WORKERS=5` 并发评分，可在 `.env` 调整
3. 大模型根据5个维度进行评分并返回JSON格式结果
4. 系统解析评分结果并赋值给对应的热点对象
5. 单篇解析失败时只影响这一篇，并按 `SCORING_PARSE_FAILURE_SCORE` 给低分；如果全部解析失败，默认随机抽取 `TOP_N_SELECT_COUNT` 篇继续上传候选

**综合评分计算公式**：
```
综合评分 = 热度×0.2 + 权威性×0.25 + 内容质量×0.25 + 家长实用性×0.2 + 时效性×0.1
```

## 🔧 高级用法

### 自定义数据源

继承 `BaseCrawler` 类实现新的数据源：

```python
from crawlers.base import BaseCrawler
from models.hotspot import EducationHotspot

class MyCustomCrawler(BaseCrawler):
    def crawl(self, keywords: list, count: int) -> list[EducationHotspot]:
        # 实现采集逻辑
        pass
```

然后在 `config/settings.py` 中启用：

```python
ENABLED_SOURCES = ["zhihu", "my_custom"]
```

### 调整评分权重

编辑 `scorers/scorer.py` 中的权重配置：

```python
WEIGHTS = {
    "heat": 0.2,        # 热度权重
    "authority": 0.25,  # 权威性权重
    "quality": 0.25,    # 内容质量权重
    "practicality": 0.2,# 实用性权重
    "timeliness": 0.1   # 时效性权重
}
```

## ❓ 常见问题

### Q: 为什么采集数量不足？

A: 可能原因：
1. 关键词搜索结果较少
2. 时间范围设置过窄
3. 某些平台需要登录状态

解决方案：
- 增加关键词数量
- 扩大时间范围（修改 `TIME_RANGE_MAX`）
- 配置有效的Cookie

### Q: 如何更换大模型提供商？

A: 修改 `.env` 文件中的配置：

```env
LLM_BASE_URL=https://your-api-provider.com/v1
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key
```

### Q: 定时任务没有执行？

A: 检查：
1. 程序是否正常运行（`python main.py start`）
2. 查看日志文件 `logs/agent.log`
3. 确认系统时间是否正确

### Q: 如何查看历史日报？

A: 所有生成的日报都保存在 `output/` 目录下，文件名包含日期：

```bash
ls output/
# 教育热点日报_20260420.md
# 教育热点日报_20260421.md
# 教育热点日报_20260422.md
# 教育热点日报_20260423.md
```

## 📄 许可证

本项目仅供学习和研究使用。

---

**最后更新**: 2026-04-24  
**版本**: v1.0.0
