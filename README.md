# AITrend

教育热点采集与分析工具。支持按关键词和明确账号采集多平台内容，调用 OpenAI 兼容模型评分，最后生成本地 Markdown 报告。

推荐数据源：

- `wechat`：搜狗微信关键词搜索，按 `wechat.keyword_search` 采集公众号文章搜索结果。
- `wechat_mp`：微信公众平台后台，按 `wechat.account_crawl` 固定公众号账号采集。
- `xiaohongshu`：通过 `TrendCrawlerRuntime` 支持关键词搜索和账号主页采集。
- `zhihu`：通过 `TrendCrawlerRuntime` 支持关键词搜索和用户主页采集。
- `google_news`：通过 Google News 做通用关键词搜索。

longxia 自动上传默认关闭；正常运行的最终产物是 `output/` 下的 Markdown 文件。

## 快速迁移

在新机器上：

```bash
git clone <repository_url>
cd AITrend

python -m venv .venv
source .venv/bin/activate

cp /old/AITrend/.env .env
cp /old/AITrend/config.yaml config.yaml

python scripts/bootstrap.py
python main.py run
```

新机器第一次运行会为 `wechat_mp`、`xiaohongshu`、`zhihu` 打开登录流程，按提示扫码即可。登录态保存在本机运行目录，不需要也不建议跨机器复制。

对外发布仓库不建议直接内嵌 `TrendCrawlerRuntime`。默认配置使用 `./third_party/TrendCrawlerRuntime`，可以手动 clone `TrendCrawlerRuntime` 到该目录，也可以把 `trend_crawler_runtime.dir` 指向你本机已有的 `TrendCrawlerRuntime` checkout。`TrendCrawlerRuntime` 使用内部使用说明，使用前请阅读它的 `LICENSE`。

## 配置分工

`.env` 只放密钥和机器差异，例如：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.4
SOGOU_WECHAT_COOKIE=
GOOGLE_NEWS_PROXY_URL=
LOG_LEVEL=INFO
LOG_FILE=./logs/agent.log
LOG_ROTATION=00:00
LOG_RETENTION=30 days
LOG_COMPRESSION=
```

`config.yaml` 放业务配置，例如启用哪些源、公众号账号、关键词、数量、时间窗口和输出文件名。

从示例开始：

```bash
cp config.yaml.example config.yaml
```

常用配置形状：

```yaml
enabled_sources:
  - wechat
  - wechat_mp
  - xiaohongshu
  - zhihu
  - google_news

collection:
  initial_collect_count: 30
  time_range_hours:
    min: 0
    max: 24

selection:
  top_n: 10

wechat:
  keyword_search:
    keywords:
      - 教育改革
      - 中考
    max_results_per_keyword: 8
    time_range_hours:
      min: 0
      max: 48
    use_playwright: true
    fetch_detail_page: false
  account_crawl:
    accounts:
      - 中国教育报
      - 人民教育
    max_results_per_account: 10
    time_range_hours:
      min: 0
      max: 168
    browser_mode: auto

xiaohongshu:
  keyword_search:
    keywords:
      - 教育改革
      - 中考
    max_results_per_keyword: 20
    time_range_hours:
      min: 0
      max: 48
  account_crawl:
    creator_urls: []
    max_results_per_account: 20
    time_range_hours:
      min: 0
      max: 168
  login_type: qrcode

zhihu:
  keyword_search:
    keywords:
      - 教育改革
      - 中考
    max_results_per_keyword: 20
    time_range_hours:
      min: 0
      max: 72
  account_crawl:
    creator_urls: []
    max_results_per_account: 20
    time_range_hours:
      min: 0
      max: 168
  login_type: qrcode

google_news:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  period: 7d
  language: zh-CN
  country: CN

output:
  dir: ./output
  filename_pattern: 教育热点日报_{date}.md
  longxia_candidate_export_enabled: false
```

## 环境准备

推荐使用：

```bash
python scripts/bootstrap.py
```

这个脚本会：

- 创建运行目录。
- 安装根项目依赖。
- 安装 `trend_crawler_runtime.dir` 指向的 `TrendCrawlerRuntime` 依赖。
- 安装 Playwright Chromium。
- 检查 Node.js。知乎和 `TrendCrawlerRuntime` 的部分签名逻辑需要 Node.js >= 16。
- 检查 `.env` 和 `config.yaml`。
- 校验配置。
- 报告本机登录态是否存在。

只检查不安装：

```bash
python scripts/bootstrap.py --check
```

## 运行方式

完整流程：采集、合并、评分、筛选、生成 Markdown。

```bash
python main.py run
```

只采集和合并，不调用大模型：

```bash
python main.py search
```

临时指定数据源：

```bash
python main.py search --sources wechat_mp
python main.py search --sources wechat,wechat_mp,xiaohongshu,zhihu,google_news
```

临时覆盖关键词或公众号账号：

```bash
python main.py search --sources xiaohongshu,zhihu --keywords 中考,高考
python main.py search --sources wechat,google_news --keywords 教育改革,中考
python main.py search --sources wechat_mp --keywords 中国教育报,人民教育
```

小红书和知乎账号主页采集：

```bash
python scripts/search_xiaohongshu_creator.py -c 'https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search'
python scripts/search_zhihu_creator.py -c 'https://www.zhihu.com/people/yd1234567'
```

同一个单源脚本也支持指定模式：

```bash
python scripts/search_xiaohongshu.py --mode accounts -c 'https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search'
python scripts/search_zhihu.py --mode both -k 教育改革,中考 -c 'https://www.zhihu.com/people/yd1234567'
```

## 登录态

登录态是机器本地状态，不属于迁移配置。

- `wechat_mp` 默认 `browser_mode: auto`。有本机登录态时会复用；没有或失效时会打开可见浏览器扫码。
- `xiaohongshu` 和 `zhihu` 默认 `login_type: qrcode`，首次运行由 `TrendCrawlerRuntime` 打开登录流程。
- Cookie 登录保留为高级选项，但不是推荐迁移方式。

账号采集只接受明确主页 URL 或 ID，不做昵称自动选择。小红书账号采集推荐从网页登录后的账号主页复制完整 URL，URL 中应包含 `xsec_token` 和 `xsec_source`。知乎账号采集使用 `https://www.zhihu.com/people/yd1234567` 这种用户主页 URL。

运行态目录默认不进 Git：

```text
browser_data/
third_party/TrendCrawlerRuntime/browser_data/
third_party/TrendCrawlerRuntime/data/
raw_data/
merged_data/
scored_data/
output/
logs/
```

日志默认写入 `logs/agent.log`，每天 00:00 自动轮转，历史日志保留 30 天。需要压缩历史日志时可把 `LOG_COMPRESSION` 设为 `zip`、`gz` 等 loguru 支持的格式。

## 输出文件

主要输出：

```text
output/
  教育热点日报_YYYYMMDD.md

merged_data/
  merged_hotspots_YYYYMMDD_HHMMSS.json

scored_data/
  merged_hotspots_YYYYMMDD_HHMMSS.json

raw_data/
  wechat_mp/
```

## 测试

```bash
python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_wechat_mp_browser_mode.py tests/test_bootstrap.py -q
```

## 注意事项

- `config.yaml` 和 `.env` 都被 Git 忽略，迁移时从旧机器复制即可。
- 首次新机器运行需要扫码登录，这是预期行为。
- 采集依赖目标平台页面和风控状态，请控制频率并遵守平台规则。
