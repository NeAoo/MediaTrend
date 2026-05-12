# AITrend

教育热点采集与分析工具。支持按关键词和明确账号采集多平台内容，调用 OpenAI 兼容模型评分，最后生成本地 Markdown 报告。

## 数据源

- `wechat`：搜狗微信关键词搜索，读取 `wechat.keyword_search`。
- `wechat_mp`：微信公众平台后台，按指定公众号账号抓取，读取 `wechat.account_crawl`。
- `xiaohongshu`：通过 `TrendCrawlerRuntime` 做小红书关键词搜索和账号主页抓取。
- `zhihu`：通过 `TrendCrawlerRuntime` 做知乎关键词搜索和用户主页抓取。
- `google_news`：通过 Google News RSS 做通用关键词搜索。

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

创建后再填写自己的密钥和采集配置：

```bash
$EDITOR .env
$EDITOR config.yaml
```

只采集不调用大模型：

```bash
python main.py search
```

完整流程会采集、合并、评分、筛选并生成 Markdown，需要在 `.env` 里填写 `LLM_API_KEY`：

```bash
python main.py run
```

## 配置文件

对外发布仓库只提交模板，不提交真实配置：

- `config.yaml.example`：可提交的中文配置模板。
- `config.yaml`：本机真实业务配置，已被 `.gitignore` 忽略。
- `.env.example`：可提交的环境变量模板。
- `.env`：本机密钥和机器差异配置，已被 `.gitignore` 忽略。

`config.yaml` 放业务配置，例如启用哪些源、公众号账号、关键词、数量、时间窗口和输出目录。

`.env` 只放密钥和本机环境，例如：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.4
SOGOU_WECHAT_COOKIE=
XIAOHONGSHU_COOKIE=
ZHIHU_COOKIE=
GOOGLE_NEWS_PROXY_URL=
LOG_LEVEL=INFO
```

## 依赖文件

根目录只保留一个主依赖入口：

- `requirements.txt`：AITrend 主程序依赖。
- `TrendCrawlerRuntime/requirements.txt`：TrendCrawlerRuntime 自己的依赖，只有小红书和知乎链路需要。

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

这样 clone 后可以直接找到小红书和知乎采集入口。`TrendCrawlerRuntime` 有自己的许可约束，使用或二次对外发布前请阅读 `TrendCrawlerRuntime/LICENSE`。

如果你想改成外置目录，可以把配置改为：

```yaml
trend_crawler_runtime:
  dir: ./third_party/TrendCrawlerRuntime
```

然后自行把兼容的 TrendCrawlerRuntime checkout 放到该目录。注意：小红书和知乎账号抓取依赖当前仓库对 creator 参数和输出文件的适配，不能随便换成未适配版本。

## 常用运行方式

临时指定数据源：

```bash
python main.py search --sources wechat_mp
python main.py search --sources wechat,google_news
python main.py search --sources xiaohongshu,zhihu
```

临时覆盖关键词或公众号账号：

```bash
python main.py search --sources wechat,google_news --keywords 教育改革,中考
python main.py search --sources wechat_mp --keywords 中国教育报,人民教育
python main.py search --sources xiaohongshu,zhihu --keywords 中考,高考
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

登录态是本机运行状态，不提交到 Git。

- `wechat_mp` 默认 `browser_mode: auto`。有登录态时走 headless，失效时自动打开可见浏览器扫码。
- `xiaohongshu` 和 `zhihu` 默认 `login_type: qrcode`，首次运行由 `TrendCrawlerRuntime` 打开登录流程。
- Cookie 登录保留为高级选项，只有把平台 `login_type` 改成 `cookie` 时才需要填写 `.env` 中的 Cookie。

账号采集的输入边界：

- 微信公众号账号：填公众号名称。
- 小红书账号：填账号主页 URL，不是昵称关键词。
- 知乎账号：填用户主页 URL，不是昵称关键词。

## 运行目录

这些目录是运行时产物，默认不进 Git：

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
