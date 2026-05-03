# AITrend

教育热点采集与分析工具。默认从微信公众平台后台、小红书、知乎采集内容，调用 OpenAI 兼容模型评分，最后生成本地 Markdown 报告。

默认推荐数据源：

- `wechat_mp`：微信公众平台后台，按固定公众号账号采集。
- `xiaohongshu`：通过内置 `MediaCrawler` 采集小红书搜索结果。
- `zhihu`：通过内置 `MediaCrawler` 采集知乎搜索结果。

`wechat` 是旧的搜狗微信搜索源，不属于默认迁移路径。longxia 自动上传默认关闭；正常运行的最终产物是 `output/` 下的 Markdown 文件。

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

## 配置分工

`.env` 只放密钥和机器差异，例如：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.4
LOG_LEVEL=INFO
LOG_FILE=./logs/agent.log
```

`config.yaml` 放业务配置，例如启用哪些源、公众号账号、关键词、数量、时间窗口和输出文件名。

从示例开始：

```bash
cp config.yaml.example config.yaml
```

常用配置形状：

```yaml
enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu

collection:
  initial_collect_count: 30
  time_range_hours:
    min: 0
    max: 24

selection:
  top_n: 10

wechat_mp:
  accounts:
    - 中国教育报
    - 人民教育
  max_articles_per_account: 10
  lookback_days: 7
  browser_mode: auto

xiaohongshu:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  login_type: qrcode

zhihu:
  keywords:
    - 教育改革
    - 中考
  max_results_per_keyword: 20
  login_type: qrcode

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
- 安装 `MediaCrawler` 依赖。
- 安装 Playwright Chromium。
- 检查 Node.js。知乎和 `MediaCrawler` 的部分签名逻辑需要 Node.js >= 16。
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
python main.py search --sources wechat_mp,xiaohongshu,zhihu
```

临时覆盖关键词或公众号账号：

```bash
python main.py search --sources xiaohongshu,zhihu --keywords 中考,高考
python main.py search --sources wechat_mp --keywords 中国教育报,人民教育
```

## 登录态

登录态是机器本地状态，不属于迁移配置。

- `wechat_mp` 默认 `browser_mode: auto`。有本机登录态时会复用；没有或失效时会打开可见浏览器扫码。
- `xiaohongshu` 和 `zhihu` 默认 `login_type: qrcode`，首次运行由 `MediaCrawler` 打开登录流程。
- Cookie 登录保留为高级选项，但不是推荐迁移方式。

运行态目录默认不进 Git：

```text
browser_data/
MediaCrawler/browser_data/
MediaCrawler/data/
raw_data/
merged_data/
scored_data/
output/
logs/
```

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
