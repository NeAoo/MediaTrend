# AITrend

<p align="center">
  <img src="docs/assets/aitrend-hero-web.png" alt="AITrend keyword and account based trend collection workflow" width="100%">
</p>

AITrend 是一个面向内容研究、教育行业观察和选题监控的趋势采集工具。它不是通用爬虫框架，而是把“关键词搜索”和“指定账号追踪”放进同一个可配置工作流里，采集后继续完成去重、AI 打分、Top N 筛选和 Markdown 报告生成。

如果你每天都要看固定公众号、小红书账号、知乎用户，同时又要监控一组关键词，AITrend 的目标是把这些动作合成一次稳定运行。

## 核心特点

- **关键词 + 账号双模式**：同一份 `config.yaml` 同时管理关键词搜索和固定账号抓取。
- **面向趋势报告**：采集不是终点，后续会合并、去重、AI 打分、筛选并输出 Markdown 日报。
- **多平台输入**：支持微信关键词、微信公众号账号、小红书关键词/账号、知乎关键词/账号、Google News 关键词、AI HOT 行业参考源。
- **配置优先迁移**：业务配置放在 `config.yaml`，密钥和机器差异放在 `.env`，仓库只保留可复用模板。
- **可先只采集**：`python main.py search` 不调用大模型，适合先验证登录和数据源。
- **适合个人和小团队**：不要求先搭分布式平台，不需要为了一个日报任务引入复杂调度系统。

## 支持的数据源

| source | 入口 | 输入类型 | 典型用途 |
| --- | --- | --- | --- |
| `wechat` | 搜狗微信 | 关键词 | 搜索公众号文章结果 |
| `wechat_mp` | 微信公众平台后台 | 公众号名称 | 追踪固定公众号账号 |
| `xiaohongshu` | TrendCrawlerRuntime | 关键词、账号主页 URL | 监控小红书话题和指定创作者 |
| `zhihu` | TrendCrawlerRuntime | 关键词、用户主页 URL | 监控知乎话题和指定用户 |
| `google_news` | Google News RSS | 关键词 | 通用新闻关键词补充 |
| `aihot` | AI HOT Public API | 精选池、关键词、分类 | 获取 AI 行业强参考内容 |

账号采集的边界要分清：

- 微信公众号账号：填公众号名称。
- 小红书账号：填账号主页 URL，不是昵称关键词。
- 知乎账号：填用户主页 URL，不是昵称关键词。

## 和常见采集框架的区别

AITrend 不试图替代通用采集框架、[Scrapy](https://docs.scrapy.org/) 或 [Crawlab](https://github.com/crawlab-team/crawlab)。它的价值在更靠近“每天要产出一份可读趋势报告”的业务层。

| 项目类型 | 主要强项 | AITrend 的区别 |
| --- | --- | --- |
| TrendCrawlerRuntime | 多平台自媒体公开内容采集，平台覆盖广 | AITrend 把 TrendCrawlerRuntime 作为小红书/知乎采集能力的一部分，并在外层补上关键词 + 指定账号配置、统一合并、AI 打分和报告输出 |
| Scrapy | 通用爬虫框架，适合开发自定义 spider | AITrend 是可运行应用，不要求用户从 spider、pipeline、item export 开始搭一套系统 |
| Crawlab | 分布式爬虫管理平台，适合管理多语言、多任务爬虫 | AITrend 更轻，重点是单仓库配置化运行和内容分析产物，不需要先部署管理平台 |
| 单一搜索脚本 | 快速抓某个平台某个关键词 | AITrend 把关键词监控和账号追踪放在同一矩阵里，并统一进入下游评分和日报 |

一句话：通用采集框架解决“怎么抓”，AITrend 更关注“每天该看哪些账号和关键词，抓完后如何变成可读的趋势判断”。

## 快速开始

```bash
git clone <repository_url>
cd AITrend

python -m venv .venv
source .venv/bin/activate

python scripts/bootstrap.py
```

`bootstrap.py` 会在首次运行时自动从模板创建本地文件：

- `.env.example` -> `.env`
- `config.yaml.example` -> `config.yaml`

创建后可以直接启动 Web 工作台配置；如果更习惯命令行，也可以手动编辑本地文件：

```bash
$EDITOR .env
$EDITOR config.yaml
```

默认模板启用 `google_news`，并内置两个教育关键词，第一次运行不需要平台登录；切到微信公众号、小红书、知乎账号采集时，再按页面提示补账号、链接或扫码登录。

## 本地 Web 工作台

AITrend 可以作为本机 Web 工具使用：页面负责编辑 `config.yaml`、配置打分模型、启动采集任务、查看每个来源/关键词/账号的进度和报告产物。

首次运行先安装前端依赖并构建静态页面：

```bash
cd web/frontend
npm install
npm run build
cd ../..
```

然后在项目根目录启动后端：

```bash
python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

注意：

- Web 工作台是本机工具，不带登录系统；请只绑定 `127.0.0.1`，不要直接暴露到公网或局域网。
- “来源配置”页保存后会直接写回根目录 `config.yaml`，命令行和 Web 任务都会使用这份默认配置。
- 任务运行中，Web 工作台会禁止重复启动任务，也会暂时禁止保存来源配置和打分 Prompt，避免中途改配置导致结果不可追溯。
- “模型配置”页会把正文打分模型和全网热榜分类模型分开保存；两者共用 `.env` 的 `LLM_API_KEY`，但 Base URL、Model、并发和 Prompt 路径分别写入 `config.yaml` 的 `scoring` 与 `hotrank.ai_classification`。
- “全网热榜”页只在点击“刷新热榜”后调用 CimiData `/api/v3/hotrank`，需要在 `.env` 配置 `CIMIDATA_APP_ID` 和 `CIMIDATA_APP_SECRET`；热榜刷新会显示拉取、AI 分类、保存进度，快照保存在 `web_jobs/hotrank/`。
- 关闭打分后可以只采集并合并 JSON，不需要填写 API Key。

开发模式可以分两个终端运行：

```bash
# 终端 1：后端
python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000 --reload

# 终端 2：前端
cd web/frontend
npm install
npm run dev
```

开发模式打开 `http://127.0.0.1:5173`。

只采集不调用大模型：

```bash
python main.py search
```

完整流程会采集、合并、评分、筛选并生成 Markdown，需要在 `.env` 里填写 `LLM_API_KEY`：

```bash
python main.py run
```

如果要把高分结果导出给下游内容生成项目，打开 `config.yaml`：

```yaml
output:
  material_export_enabled: true
  material_export_dir: ./output/materials
```

再次运行：

```bash
python main.py run
```

导出结构：

```text
output/materials/YYYY-MM-DD/
  manifest.json
  candidates/
    001.md
    001.json
```

`manifest.json` 是下游项目读取素材的入口；`candidates/*.md` 保存可直接注入生成 prompt 的正文和评分信息。

定时模式：

```bash
python main.py start
```

## 配置文件

仓库只提交模板，不提交真实配置：

- `config.yaml.example`：可提交的中文配置模板。
- `config.yaml`：本机真实业务配置，已被 `.gitignore` 忽略。
- `.env.example`：可提交的环境变量模板。
- `.env`：本机密钥和机器差异配置，已被 `.gitignore` 忽略。

`config.yaml` 放业务配置，例如启用哪些源、公众号账号、关键词、数量、时间窗口和输出目录。

`.env` 只放密钥和本机环境，例如：

```env
LLM_API_KEY=your_api_key
SOGOU_WECHAT_COOKIE=
XIAOHONGSHU_COOKIE=
ZHIHU_COOKIE=
GOOGLE_NEWS_PROXY_URL=
LOG_LEVEL=INFO
```

正文打分的 Base URL、Model、超时时间、并发数和 Prompt 路径都在 `config.yaml` 的 `scoring` 节里配置，也可以在 Web 工作台的“模型配置”页面修改。

全网热榜主题分类使用单独模型参数和单独 Prompt，配置在 `config.yaml` 的 `hotrank.ai_classification` 节；它只复用 `.env` 里的 `LLM_API_KEY`，不复用 `scoring.model`。

一个最小的微信公众号账号配置：

```yaml
enabled_sources:
  - wechat_mp

wechat:
  account_crawl:
    accounts:
      - 中国教育报
      - 人民教育
    max_results_per_account: 10
    expected_min_results: 3
    time_range_hours:
      min: 0
      max: 168
```

小红书和知乎如果要启用账号模式，需要填主页 URL：

```yaml
enabled_sources:
  - xiaohongshu
  - zhihu

xiaohongshu:
  account_crawl:
    creator_urls:
      - https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search

zhihu:
  account_crawl:
    creator_urls:
      - https://www.zhihu.com/people/URL_TOKEN
```

## 常用命令

临时指定数据源：

```bash
python main.py search --sources wechat_mp
python main.py search --sources wechat,google_news
python main.py search --sources xiaohongshu,zhihu
python main.py search --sources aihot
```

临时覆盖关键词或公众号账号：

```bash
python main.py search --sources wechat,google_news --keywords 教育改革,中考
python main.py search --sources wechat_mp --keywords 中国教育报,人民教育
python main.py search --sources xiaohongshu,zhihu --keywords 中考,高考
python main.py search --sources aihot --keywords OpenAI,Agent
```

单源脚本：

```bash
python scripts/search_wechat_mp.py -a 中国教育报,人民教育
python scripts/search_google_news.py -k 教育改革,中考
python scripts/search_aihot.py
python scripts/search_aihot.py -k OpenAI,Agent
python scripts/search_xiaohongshu.py --mode both -k 教育改革 -c 'https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search'
python scripts/search_zhihu.py --mode both -k 教育改革 -c 'https://www.zhihu.com/people/URL_TOKEN'
```

账号主页快捷脚本：

```bash
python scripts/search_xiaohongshu_creator.py -c 'https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search'
python scripts/search_zhihu_creator.py -c 'https://www.zhihu.com/people/URL_TOKEN'
```

## 依赖文件

根目录只保留一个主依赖入口：

- `requirements.txt`：AITrend 主程序依赖。
- `TrendCrawlerRuntime/requirements.txt`：TrendCrawlerRuntime 自己的依赖，只有小红书和知乎链路需要。
- `web/frontend/package.json`：Web 工作台前端依赖。建议使用 Node.js 20.19+ 或 22.12+。

不要手动安装多个根目录 requirements。统一运行：

```bash
python scripts/bootstrap.py
```

脚本会先安装根目录 `requirements.txt`，再根据 `config.yaml` 的 `trend_crawler_runtime.dir` 安装对应 `TrendCrawlerRuntime/requirements.txt`。

## TrendCrawlerRuntime

当前仓库保留 `./TrendCrawlerRuntime` 兼容拷贝，所以默认配置是：

```yaml
trend_crawler_runtime:
  dir: ./TrendCrawlerRuntime
```

这样 clone 后可以直接找到小红书和知乎采集入口。`TrendCrawlerRuntime` 是内部采集运行时，使用或对外发布前请阅读 `TrendCrawlerRuntime/LICENSE`。

如果你想改成外置目录，可以把配置改为：

```yaml
trend_crawler_runtime:
  dir: ./third_party/TrendCrawlerRuntime
```

然后自行把兼容的 TrendCrawlerRuntime checkout 放到该目录。注意：小红书和知乎账号抓取依赖当前仓库对 creator 参数和输出文件的适配，不能随便换成未适配版本。

## 登录态

登录态是本机运行状态，不提交到 Git。

- `wechat_mp` 默认 `browser_mode: auto`。有登录态时走 headless，失效时自动打开可见浏览器扫码。
- `xiaohongshu` 和 `zhihu` 默认 `login_type: qrcode`，首次运行由 `TrendCrawlerRuntime` 打开登录流程。
- Cookie 登录保留为高级选项，只有把平台 `login_type` 改成 `cookie` 时才需要填写 `.env` 中的 Cookie。

## 输出

运行后常见产物：

```text
raw_data/       # 各平台原始采集结果
merged_data/    # 多源合并后的统一 JSON
scored_data/    # AI 打分后的数据
output/         # Markdown 日报
logs/           # 运行日志
```

运行态目录默认不进 Git：

```text
browser_data/
TrendCrawlerRuntime/browser_data/
TrendCrawlerRuntime/data/
raw_data/
merged_data/
scored_data/
output/
logs/
```

## 测试

```bash
python -m pytest -q tests
```

## 合规提醒

请只采集合规可访问的数据，遵守目标平台的服务条款、频率限制和当地法律法规。AITrend 提供的是个人研究和内部分析工作流，不应被用于绕过权限、批量骚扰或侵害他人权益。
