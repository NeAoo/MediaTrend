# 教育热点搜集 Agent 流程说明
智能教育热点采集与分析系统，自动从多平台采集教育类热点内容，通过AI大模型智能打分排序，生成家长友好的Markdown日报。

## 📁 项目结构

```
AITrend/
├── main.py                  # 主入口文件
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置文件
├── crawlers/                # 爬虫模块
│   ├── __init__.py
│   ├── base.py              # 爬虫基类
│   ├── manager.py           # 爬虫管理器
│   ├── wechat.py            # 微信公众号爬虫
│   ├── zhihu.py             # 知乎爬虫
│   └── xiaohongshu.py       # 小红书爬虫
├── processors/              # 数据处理模块
│   ├── __init__.py
│   └── data_merger.py       # 数据合并器
├── scorers/                 # 评分模块
│   ├── __init__.py
│   └── scorer.py            # 内容评分器
├── formatters/              # 格式化输出模块
│   ├── __init__.py
│   └── markdown.py          # Markdown生成器
├── models/                  # 数据模型
│   ├── __init__.py
│   └── hotspot.py           # 热点数据模型
├── merged_data/             # 采集后合并数据（无评分）
├── scored_data/             # 评分后数据（含评分）⭐
├── output/                  # Markdown报告输出
├── logs/                    # 日志文件
├── requirements.txt         # 依赖包列表
├── .env                     # 环境变量配置
└── README.md                # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.14
- OpenAI API Key 

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd AITrend
```

2. **创建虚拟环境**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3.1 **安装主项目依赖**
```bash
pip install -r requirements.txt
```

3.2 **配置 MediaCrawler 子环境**

由于本项目集成了修改版的 MediaCrawler，需要单独配置其环境：
```bash 
cd MediaCrawler 
```
## 📋 前置依赖

### 🚀 uv 安装（推荐）

在进行下一步操作之前，请确保电脑上已经安装了 uv：

- **安装地址**：[uv 官方安装指南](https://docs.astral.sh/uv/getting-started/installation)
- **验证安装**：终端输入命令 `uv --version`，如果正常显示版本号，证明已经安装成功
- **推荐理由**：uv 是目前最强的 Python 包管理工具，速度快、依赖解析准确

### 🟢 Node.js 安装

项目依赖 Node.js，请前往官网下载安装：

- **下载地址**：https://nodejs.org/en/download/
- **版本要求**：>= 16.0.0

### 📦 Python 包安装

```shell
# 进入项目目录
```

### 🌐 浏览器驱动安装（可选）

> 如果使用默认的 CDP 模式（连接已有 Chrome 浏览器），**无需安装浏览器驱动**。仅在使用标准 Playwright 模式时需要安装。

```shell
# 仅在标准 Playwright 模式下需要安装浏览器驱动
uv run playwright install
```

### 🌍 Chrome 浏览器配置（推荐）

项目默认使用 CDP 模式连接用户已有的 Chrome 浏览器，可以复用浏览器已有的登录状态、Cookie、扩展等，**大幅降低平台风控检测风险**。

使用前需要：

1. **安装最新版 Chrome 浏览器**（版本 >= 144），[下载地址](https://www.google.com/chrome/)
2. **开启远程调试功能**：在 Chrome 地址栏输入 `chrome://inspect/#remote-debugging`，勾选 **"Allow remote debugging for this browser instance"**
3. 页面显示 `Server running at: 127.0.0.1:9222` 表示已就绪

> 💡 **提示**：运行爬虫后，Chrome 浏览器会弹出确认对话框，点击"接受"即可。程序会等待用户确认，60秒内操作完成即可。
>
> 如果不想使用 CDP 模式，可以在 `config/base_config.py` 中设置 `ENABLE_CDP_MODE = False` 切换为标准 Playwright 模式。

#返回主目录
```bash
cd ..
```

4. **配置环境变量**

参考 `.env.example` 创建 `.env` 文件：
```bash
# 大模型 API 配置
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.4

# 输出目录
OUTPUT_DIR=./output
```

5. **配置数据源**

编辑 `config/settings.py`:
```python
# 启用的数据源
ENABLED_SOURCES = [
    "zhihu",       # 知乎
    "wechat",      # 微信公众号
    # "xiaohongshu", # 小红书
]

# 搜索关键词
KEYWORDS = [
    "学习方法",
    "考研",
    "家庭教育",
]

# 采集数量
INITIAL_COLLECT_COUNT = 30  # 初始采集数量
TOP_N_SELECT_COUNT = 10     # 最终筛选Top N
```

### 运行方式

#### 方式1: 单次执行

立即执行一次采集任务：

```bash
python main.py run
```

**输出示例**:
```
(base) (.venv) PS D:\AITrend> python main.py run                                                                    
2026-04-23 22:45:11 | INFO     | ============================================================
2026-04-23 22:45:11 | INFO     | 教育热点搜集 Agent 启动
2026-04-23 22:45:11 | INFO     | ============================================================
2026-04-23 22:45:11 | INFO     | 
第一步：开始采集教育热点...
2026-04-23 22:45:11 | INFO     | 已加载采集器: wechat
2026-04-23 22:45:11 | INFO     | 已加载采集器: xiaohongshu
2026-04-23 22:45:11 | INFO     | 搜索关键词: 教育改革, 中考
2026-04-23 22:45:11 | INFO     | 采集时间范围: 0-48 小时
2026-04-23 22:45:11 | INFO     | 搜索关键词: 教育改革, 中考
2026-04-23 22:45:11 | INFO     | 开始从 wechat 采集...
2026-04-23 22:45:11 | INFO     | 准备搜索 2 个关键词
2026-04-23 22:45:11 | INFO     | 时间范围: 0-48 小时
2026-04-23 22:45:11 | INFO     | 正在搜索公众号关键词: 教育改革
2026-04-23 22:45:11 | INFO     | 使用 Playwright 浏览器搜索：教育改革
2026-04-23 22:45:15 | INFO     | 找到 9 个搜索结果
2026-04-23 22:45:16 | INFO     | 成功解析 8 篇文章
2026-04-23 22:45:20 | INFO     | 正在搜索公众号关键词: 中考
2026-04-23 22:45:20 | INFO     | 使用 Playwright 浏览器搜索：中考
2026-04-23 22:45:24 | INFO     | 找到 10 个搜索结果
2026-04-23 22:45:24 | INFO     | 成功解析 8 篇文章
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 中考英语核心考点:名词复数... (距今 1.3 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 26中考化学新趋势跨学科专项训练14题有答案... (距今 0.1 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 中考道法·答题方法:做法类、措施类这么答,比别人多拿几分(含... (距今 0.7 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 中考550分左右,选普高还是职校?... (距今 1.4 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 2026常熟中考零模数学+英语试卷+答案(2026.4.22... (距今 0.4 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开... (距今 0.1 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 中考化学131个“题眼”,吃透考试稳了 #必考考点 #家长收... (距今 0.3 小时)
2026-04-23 22:45:25 | INFO     | ✓ 成功采集: 中考语文考前必背知识清单,想拿高分背这一份就够了!... (距今 0.8 小时)
2026-04-23 22:45:25 | INFO     | 关键词 '中考' 已找到 8 篇，继续下一个
2026-04-23 22:45:29 | INFO     | 公众号采集完成: 成功8, 失败0
2026-04-23 22:45:29 | INFO     | 已按时间倒序排列，最新文章: 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开...
2026-04-23 22:45:29 | INFO     | ✅ 微信原始数据已保存: raw_data\wechat\wechat_raw_20260423_224529.json
2026-04-23 22:45:29 | INFO     | wechat 采集到 8 条内容
2026-04-23 22:45:29 | INFO     | 开始从 xiaohongshu 采集...
2026-04-23 22:45:29 | INFO     | 📱 开始从小红书采集教育热点...
2026-04-23 22:45:29 | INFO     |    关键词: 教育改革, 中考
2026-04-23 22:45:29 | INFO     |    时间范围: 最近 48 小时
2026-04-23 22:45:29 | INFO     | 🔑 传递给 MediaCrawler 的关键词: 教育改革,中考
2026-04-23 22:45:29 | INFO     | ⏰ 时间范围: 48 小时
2026-04-23 22:45:29 | INFO     | 📊 每个关键词爬取数量: 20
2026-04-23 22:45:29 | INFO     | 执行 MediaCrawler: uv run main.py --platform xhs --lt qrcode --type search
2026-04-23 22:45:29 | INFO     | 超时时间: 900 秒 (15.0 分钟)

2026-04-23 22:45:32 MediaCrawler INFO (core.py:75) - [XiaoHongShuCrawler] Launching browser using CDP mode
2026-04-23 22:45:37 MediaCrawler INFO (cdp_browser.py:220) - [CDPBrowserManager] Detected browser: Google Chrome (Unknown Version)
2026-04-23 22:45:37 MediaCrawler INFO (cdp_browser.py:223) - [CDPBrowserManager] Browser path: C:\Program Files\Google\Chrome\Application\chrome.exe
2026-04-23 22:45:37 MediaCrawler INFO (cdp_browser.py:263) - [CDPBrowserManager] User data directory: D:\AITrend\MediaCrawler\browser_data\cdp_xhs_user_data_dir
2026-04-23 22:45:37 MediaCrawler INFO (browser_launcher.py:163) - [BrowserLauncher] Launching browser: C:\Program Files\Google\Chrome\Application\chrome.exe
2026-04-23 22:45:37 MediaCrawler INFO (browser_launcher.py:164) - [BrowserLauncher] Debug port: 9222
2026-04-23 22:45:37 MediaCrawler INFO (browser_launcher.py:165) - [BrowserLauncher] Headless mode: False
2026-04-23 22:45:37 MediaCrawler INFO (browser_launcher.py:195) - [BrowserLauncher] Waiting for browser to be ready on port 9222...
2026-04-23 22:45:38 MediaCrawler INFO (browser_launcher.py:204) - [BrowserLauncher] Browser is ready on port 9222
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:237) - [CDPBrowserManager] CDP port 9222 is accessible
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:87) - [CDPBrowserManager] SIGINT handler already exists, skipping registration to avoid override
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:92) - [CDPBrowserManager] SIGTERM handler already exists, skipping registration to avoid override
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:95) - [CDPBrowserManager] Cleanup handlers registered
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:301) - [CDPBrowserManager] Got browser WebSocket URL: ws://localhost:9222/devtools/browser/789552ac-dc24-4509-847d-8739acf38c41
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:333) - [CDPBrowserManager] Connecting to browser via CDP: ws://localhost:9222/devtools/browser/789552ac-dc24-4509-847d-8739acf38c41
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:337) - [CDPBrowserManager] Successfully connected to browser
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:338) - [CDPBrowserManager] Browser contexts count: 1
2026-04-23 22:45:39 MediaCrawler INFO (cdp_browser.py:363) - [CDPBrowserManager] Using existing browser context
2026-04-23 22:45:39 MediaCrawler INFO (core.py:442) - [XiaoHongShuCrawler] CDP browser info: {'version': '147.0.7727.102', 'contexts_count': 1, 'debug_port': 9222, 'is_connected': True}
2026-04-23 22:45:43 MediaCrawler INFO (core.py:362) - [XiaoHongShuCrawler.create_xhs_client] Begin create Xiaohongshu API client ...
2026-04-23 22:45:43 MediaCrawler INFO (client.py:250) - [XiaoHongShuClient.pong] Begin to check login state...
2026-04-23 22:45:44 MediaCrawler INFO (client.py:261) - [XiaoHongShuClient.pong] Login state result: True
2026-04-23 22:45:44 MediaCrawler INFO (core.py:131) - [XiaoHongShuCrawler.search] Begin search Xiaohongshu keywords
2026-04-23 22:45:44 MediaCrawler INFO (core.py:138) - [XiaoHongShuCrawler.search] Current search keyword: ['教育改革'
2026-04-23 22:45:44 MediaCrawler INFO (core.py:148) - [XiaoHongShuCrawler.search] search Xiaohongshu keyword: ['教育改革', page: 1
2026-04-23 22:45:44 MediaCrawler INFO (core.py:157) - [XiaoHongShuCrawler.search] Search notes response: {'has_more': True, 'items': [{'id': '69ea2cc0000000001901e004', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '思政热点:2026年全国教育大会“八大任务”', 'user': {'nickname': 'A陈老师课题成果奖研究-慧启', 'xsec_token': 'AB7z-RGXgTFtHs3h_nN7HA0HpAjfAcfiDhyfTAfhCRFAY=', 'nick_name': 'A陈老师课题成果奖研究-慧启', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/675fc169bdd67700013d84d6.jpg?imageView2/2/w/80/format/jpg', 'user_id': '63e456fe00000000260043fd'}, 'interact_info': {'comment_count': '0', 'shared_count': '1', 'liked': False, 'liked_count': '2', 'collected': False, 'collected_count': '3'}, 'cover': {'height': 1632, 'width': 1224}, 'image_list': [{'height': 1632, 'width': 1224}, {'height': 1527, 'width': 1080}, {'width': 1080, 'height': 1527}, {'height': 1527, 'width': 1080}, {'height': 1527, 'width': 1080}], 'corner_tag_info': [{'type': 'publish_time', 'text': '16分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngq89fTwMnHoFKhME59Hv6s='}, {'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniy5qBBI5XjiBaoKJ4mZ_IU=', 'id': '69ea22c0000000001f030c06', 'model_type': 'note', 'note_card': {'user': {'nick_name': '小司（备考）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31m9tee7olj205pvkvkcjlqmo68i1g50?imageView2/2/w/80/format/jpg', 'user_id': '67f4fd19000000000e02ead8', 'nickname': '小司（备考）', 'xsec_token': 'ABWjKgmPGmSylTcpdQNoglX-J7FpK99cxodpDpQqM1tK8='}, 'interact_info': {'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '1', 'shared_count': '0'}, 'cover': {'height': 1620, 'width': 1080}, 'image_list': [{'height': 1620, 'width': 1080}], 'corner_tag_info': [{'type': 'publish_time', 'text': '59分钟前'}], 'type': 'normal', 'display_title': '河北会计继教重大改革！学分新规+截止时间'}}, {'id': '69ea19a4000000001e00dfa0', 'model_type': 'note', 'note_card': {'display_title': '六育协同“AI+课程”教学课题，太好立项了', 'user': {'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/64f82103b403790001c3321f.jpg?imageView2/2/w/80/format/jpg', 'user_id': '63dca6cd0000000027035c33', 'nickname': '老根课题申报写作咨询（知慧圈）', 'xsec_token': 'AB5stAR9t2cQIBjsuTcijj8-11VC4s9EVfq2LfzAttFA0=', 'nick_name': '老根课题申报写作咨询（知慧圈）'}, 'interact_info': {'liked': False, 'liked_count': '1', 'collected': False, 'collected_count': '3', 'comment_count': '0', 'shared_count': '0'}, 'cover': {'height': 4490, 'width': 3175}, 'image_list': [{'height': 4490, 'width': 3175}, {'height': 2560, 'width': 1812}, {'height': 2560, 'width': 1812}, {'height': 2560, 'width': 1812}, {'height': 2560, 'width': 1812}, {'height': 2560, 'width': 1812}, {'height': 2560, 'width': 1812}], 'corner_tag_info': [{'text': '1小时前', 'type': 'publish_time'}], 'type': 'normal'}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngODBnEh6FKJQF5LNSylBtY='}, {'id': '69ea12280000000020003802', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '333day6', 'user': {'user_id': '69db45870000000032035e9a', 'nickname': '蒋文文', 'xsec_token': 'ABND1Fz1HV8UEqF2e0o6vW4oUUM644g39LBlyKKpfoPwg=', 'nick_name': '蒋文文', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31usv6nq3iq6g5qer8m3smnkqb4af0a0?imageView2/2/w/80/format/jpg'}, 'interact_info': {'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0', 'shared_count': '0', 'liked': False}, 'cover': {'height': 3060, 'width': 4080}, 'image_list': [{'height': 3060, 'width': 4080}, {'height': 1440, 'width': 1080}, {'height': 3060, 'width': 4080}, {'height': 3060, 'width': 4080}], 'corner_tag_info': [{'type': 'publish_time', 'text': '2小时前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniewdorUYbC9RiYud8VGsW8='}, {'id': '69ea112a000000002301fc7c', 'model_type': 'note', 'note_card': {'corner_tag_info': [{'type': 'publish_time', 'text': '2小时前'}], 'type': 'normal', 'display_title': '“优秀传统文化+思政教学改革”课题绝了', 'user': {'user_id': '63e3872500000000260123c8', 'nickname': '岁穗', 'xsec_token': 'ABiAe-8n9xGBnDlaZgEcU1xT1nFgI_5j1455ac_Cv2gVw=', 'nick_name': '岁穗', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31r0a36hc7o6g5ov3gsipi8u86ju0isg?imageView2/2/w/80/format/jpg'}, 'interact_info': {'comment_count': '0', 'shared_count': '0', 'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0'}, 'cover': {'height': 2560, 'width': 1810}, 'image_list': [{'height': 2560, 'width': 1810}, {'width': 1810, 'height': 2560}, {'height': 2560, 'width': 1810}, {'height': 2560, 'width': 1810}, {'height': 2560, 'width': 1810}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnoKnAZl47cjLuJEn5FWSHRI='}, {'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnonqn8EoZ55eBfCssWyILkE=', 'id': '69ea0a50000000001b022187', 'model_type': 'note', 'note_card': {'cover': {'height': 2892, 'width': 2169}, 'image_list': [{'height': 2892, 'width': 2169}, {'height': 2892, 'width': 2169}, {'height': 2892, 'width': 2169}, {'height': 2892, 'width': 2169}, {'width': 2169, 'height': 2892}, {'height': 2892, 'width': 2169}], 'corner_tag_info': [{'type': 'publish_time', 'text': '2小时前'}], 'type': 'normal', 'display_title': '人工智能赋能英语课程教学课题，直接立项', 'user': {'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31o5p9ulamm6g5p58p4jamp91vmsvpoo?imageView2/2/w/80/format/jpg', 'user_id': '64a8c926000000002a036521', 'nickname': '课题申报陈老师', 'xsec_token': 'ABwrl75yLRbcHRU7CD8hWKEWdkWbVjEi3MtfgZ2lJImck=', 'nick_name': '课题申报陈老师'}, 'interact_info': {'comment_count': '0', 'shared_count': '0', 'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '1'}}}, {'model_type': 'hot_query', 'hot_query': {'title': '大家都在搜', 'source': 2, 'word_request_id': '7640f1a7-0c46-4f0d-af55-a64cb48e9f68#1776955544566', 'queries': [{'id': '教育改革10大政策', 'name': '教育改革10大政策', 'search_word': '教育改革10大政策', 'cover': ''}, {'id': '今年教育改革政策有哪些', 'name': '今年教育改革政策有哪些', 'search_word': '今年教育改革政策有哪些', 'cover': ''}, {'id': '教育改革最新政策', 'name': '教育改革最新政策', 'search_word': '教育改革最新政策', 'cover': 'http://sns-na-i6.xhscdn.com/spectrum/1040g34o31ivvt1cv0u105ogo9t9ocmdqrf53ee0?imageView2/1/h/132/w/480/format/jpg&ap=5&sc=HOT_QRY&sign=f652a4307148aa245affd49ff25c204d&t=69ea3098&origin=0'}, {'id': '中小学教育改革', 'name': '中小学教育改革', 'search_word': '中小学教育改革', 'cover': 'http://sns-na-i6.xhscdn.com/spectrum/1040g0k031f9fn99r6m005pdgnr0jft3jdant748?imageView2/1/h/132/w/480/format/jpg&ap=5&sc=HOT_QRY&sign=945c1c7add3587a56074e6cf977458e6&t=69ea3098&origin=0'}]}, 'xsec_token': 'ABv2uTIv1I-XbjFJQpXNupmXQiw77qyxsg8EVbxDN8d7mhmGM23eO-_edBd9wix39yBOEF-G3Pect1smo-EXyIsoCrPabgds4twBIus-jXK1M=', 'id': '7640f1a7-0c46-4f0d-af55-a64cb48e9f68#1776955544566'}, {'id': '69ea050b0000000020013003', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': 'kc教育学打卡第七天（第三期）', 'user': {'nick_name': '璟璟璟（被拉比点过赞版）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31u14tcqrne0g5omv76h7osqj45ikud8?imageView2/2/w/80/format/jpg', 'user_id': '62df39a2000000001f007353', 'nickname': '璟璟璟（被拉比点过赞版）', 'xsec_token': 'ABbrrjIIU5zrf75PH8NciPWg2EvGt6WYhkmYb-ue0_iO0='}, 'interact_info': {'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0', 'shared_count': '0'}, 'cover': {'height': 1640, 'width': 2360}, 'image_list': [{'height': 1640, 'width': 2360}, {'height': 1640, 'width': 2360}, {'height': 1640, 'width': 2360}, {'height': 3024, 'width': 4032}, {'height': 3024, 'width': 4032}, {'width': 4032, 'height': 3024}], 'corner_tag_info': [{'type': 'publish_time', 'text': '3小时前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniHQ3rAzSoFuaTUUXW1AM74='}, {'id': '69ea04f6000000002003905f', 'model_type': 'note', 'note_card': {'interact_info': {'shared_count': '1', 'liked': False, 'liked_count': '5', 'collected': False, 'collected_count': '3', 'comment_count': '0'}, 'cover': {'height': 2400, 'width': 1440}, 'image_list': [{'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}, {'width': 1440, 'height': 2400}, {'height': 2400, 'width': 1440}], 'corner_tag_info': [{'type': 'publish_time', 'text': '3小时前'}], 'type': 'normal', 'display_title': '贾老师26年教育热点时政阶段性盘点总结', 'user': {'nick_name': '贾老师教育学', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31o3bt9a56m605oj96eh40ik5ihiiqfg?imageView2/2/w/80/format/jpg', 'user_id': '626933a20000000010004a85', 'nickname': '贾老师教育学', 'xsec_token': 'ABPsUVBxP91nXqJhdHZw-uNMGh4fp4XqTrpAhSVIFNOxQ='}}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngntKOoPja630rjLVzVPd0anQ='}, {'model_type': 'note', 'note_card': {'cover': {'height': 2560, 'width': 1856}, 'image_list': [{'height': 2560, 'width': 1856}], 'corner_tag_info': [{'type': 'publish_time', 'text': '5小时前'}], 'type': 'normal', 'user': {'user_id': '5d6a1b0c0000000001006c62', 'nickname': '几片茉莉', 'xsec_token': 'ABlrGXBC1vZCJjggv4NO79EMuLfD-nr_GGhmzrHc5seeY=', 'nick_name': '几片茉莉', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31v5vo1nf2s605nba3c608r3217k6d1g?imageView2/2/w/80/format/jpg'}, 'interact_info': {'collected_count': '3', 'comment_count': '0', 'shared_count': '0', 'liked': False, 'liked_count': '1', 'collected': False}}, 'xsec_token': 'ABdxuakkykQQRfchaFNorE1tJKHmLJlZRd49SvNvximkA=', 'id': '69e9ea1a0000000012012806'}, {'id': '69e9e7a1000000001f031800', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '教育局最新通知，26届考生太幸运了！', 'user': {'nick_name': '拾光谢老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31krhlo7a306g5p2ko39k5egbpdfm720?imageView2/2/w/80/format/jpg', 'user_id': '6454c0d3000000001002ba0b', 'nickname': '拾光谢老师', 'xsec_token': 'ABdUe_L06l_uApLfhTgq2VKjVKyDuQTyVQFD_HWGnIczI='}, 'interact_info': {'shared_count': '1', 'liked': False, 'liked_count': '4', 'collected': False, 'collected_count': '5', 'comment_count': '2'}, 'cover': {'height': 4608, 'width': 3451}, 'image_list': [{'height': 4608, 'width': 3451}], 'corner_tag_info': [{'type': 'publish_time', 'text': '5小时前'}]}, 'xsec_token': 'ABdxuakkykQQRfchaFNorE1tc-c978TmmwelZFLKGg7vY='}, {'xsec_token': 'ABdxuakkykQQ2026-04-23 22:45:44 MediaCrawler INFO (core.py:293) - [get_note_detail_async_task] Begin get note detail, note_id: 69ea2cc0000000001901e004
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea2cc0000000001901e004', 'type': 'normal', 'title': '思政热点:2026年全国教育大会“八大任务”', 'desc': '#记录吧就现在[话题]#\n2026全国教育大会重磅发布「八大任务」✨，堪称未来5年教育改革的全景路线图！ 划重点👇\n💡 一号工程·立德树人\u200b\n✔ 告别填鸭说教→升级「社会实践大课堂」+「AI育人课堂」\n✔ 身心健康成硬指标❗心理健康纳入评价体系\n✔ 加速构建中国原创教材体系📚\n🏫 民生刚需·资源布局\u200b\n✔ 动态应对「人口潮汐」：城市扩学位/乡村小班制\n✔ 县域高中振兴🚀：掐尖招生退散！减负落地小学取消期中考\n🎓 高教突围·龙头引领\u200b\n✔ 双一流扩容至200所！主攻理工农医+AI🔬\n✔ 资源倾斜中西部/人口大省📍破解高考地域差\n✔ 高校分类改革：拒绝千校一面！\n⚡ 科教融合·三位一体\u200b\n✔ 建交叉学科中心💻（AI+医疗/量子材料）\n✔ 打通实验室→生产线转化链🔗\n✔ 破解「有人没活干」结构性失业👔\n🔧 职教崛起·多元赛道\u200b\n✔ 普职融通双向流动↔打破升学独木桥\n✔ 新增低空经济/具身智能🔋等新专业\n✔ 「集群培养」毕业即上岗💼\n🤖 AI赋能·重塑教育\u200b\n✔ 全学段必修AI课📱从小培养数字素养\n✔ 破除唯分数❌强基计划扩容+体美纳入考核\n👩🏫 强师筑基·减负提质\u200b\n✔ 弘扬教育家精神✨提升职业荣誉感\n✔ 砍掉非教学负担📉盘活退休名师银龄讲学\n🌍 开放共赢·全球视野\u200b\n✔ 从引进来到输出中国教育方案🇨🇳\n✔ 筑牢安全防线🔒守护意识形态阵地\n💎八大任务环环相扣！从顶层设计到落地生根，勾勒中国教育高质量发展新图景🌟 备考党/家长/教育从业者速码住！\n#热点[话题]# #学科思政[话题]# #教育热点[话题]# #思政[话题]# #教育现代化[话题]# #思政热点[话题]# #教育大会[话题]#   #记录吧就现在[话题]#', 'video_url': '', 'time': 1776954560000, 'last_update_time': 1776954561000, 'user_id': '63e456fe00000000260043fd', 'nickname': 'A陈老师课题成果奖研究-慧启', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/675fc169bdd67700013d84d6.jpg', 'liked_count': '2', 'collected_count': '3', 'comment_count': '', 'share_count': '1', 'ip_location': '山东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/8029d328e2cd4339da3cb7c637f79dab/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/701e5014ff9e0492c021565d1c811a14/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/9626b40a5fda5ea114c1c1f6ec91b3b0/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/343a4f786960506b661cf0173d1ee3be/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/5aebf94c940c0a1ef88ce97dad00d901/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_dft_wlteh_webp_3', 'tag_list': '记录吧就现在,热点,学科思政,教育热点,思政,教育现代化,思政热点,教育大会', 'last_modify_ts': 1776955588541, 'note_url': 'https://www.xiaohongshu.com/explore/69ea2cc0000000001901e004?xsec_token=AB-Kw1pgh4a9ki1JHIdRngngq89fTwMnHoFKhME59Hv6s=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngq89fTwMnHoFKhME59Hv6s='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea22c0000000001f030c06', 'type': 'normal', 'title': '河北会计继教重大改革！学分新规+截止时间', 'desc': '河北会计继续教育迎来重大改革，新规重点、时间节点一次性整理清楚，会计人员务必收藏！\n\t\n2026 年度河北会计继续教育已于4月7日正式开启，关键时间牢记：缴费截止2027年3月15日，全部课程学习、考试收尾截止2027年3月25日，逾期未完成，将直接影响会计档案记录、职称报考与资格审核。\n\t\n学分要求迎来全新调整，常规年度统一要求修满90学分，专业科目60学分、公需科目30学分，河北公需课需在人社部门平台学习。\n\t\n补学往年继教学分标准大幅上调，逐年递增：2025年不低于90学分、2024年100学分、2023年110学分、2022年120学分、2021年需达130学分，和往年标准差异极大，切勿按旧规学习。\n\t\n所有学员需在规定时限内完成课程学习、线上考试、学分同步及课程评价，单课完成后按页面提示操作，才算有效获取学分。学分对接完成后，所属地财政部门会在3个工 作日内审核登记学分。\n\t\n新规变化多、学分要求更高，建议尽早完成学习，避免后期扎堆延误，影响个人财会相关业务办理！\n\t\n#河北会计继续教育 #会计继续教育补学 #会计人须知 #中级会计 #初级会计', 'video_url': '', 'time': 1776952000000, 'last_update_time': 1776952038000, 'user_id': '67f4fd19000000000e02ead8', 'nickname': '小司（备考）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31m9tee7olj205pvkvkcjlqmo68i1g50', 'liked_count': '', 'collected_count': '', 'comment_count': '1', 'share_count': '', 'ip_location': '广东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/8e2930f3f97cd02204ab7871a329eb6b/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_dft_wlteh_webp_3', 'tag_list': '', 'last_modify_ts': 1776955588543, 'note_url': 'https://www.xiaohongshu.com/explore/69ea22c0000000001f030c06?xsec_token=AB-Kw1pgh4a9ki1JHIdRngniy5qBBI5XjiBaoKJ4mZ_IU=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniy5qBBI5XjiBaoKJ4mZ_IU='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea19a4000000001e00dfa0', 'type': 'normal', 'title': '六育协同“AI+课程”教学课题，太好立项了', 'desc': '今天给大家分享一份人工智能赋能教育教学改革课题申报书范文，课题名称：六育协同“ＡI＋课程”教学的探索与实践研究\n本文章立足新时代全面育人与教育数字化转型，聚焦六育协同 + AI + 课程深度融合，以初中为试点，针对融合形式化、设计碎片化、师资不足、评价缺失等问题，构建教学模式、学科方案与多元评价体系，探索可落地的实践路径，丰富理论并为教育高质量发展提供示范。\n分享给大家这篇宝藏课题申报书范文，供大家参考学习！\n#课题申报书[话题]##教育课题[话题]# #教学课程[话题]##课题怎么写[话题]##六育协同[话题]##课题范文[话题]# #课题范文分享[话题]# #课题怎么写[话题]# #课题申报[话题]#', 'video_url': '', 'time': 1776949668000, 'last_update_time': 1776949669000, 'user_id': '63dca6cd0000000027035c33', 'nickname': '老根课题申报写作咨询（知慧圈）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/64f82103b403790001c3321f.jpg', 'liked_count': '1', 'collected_count': '3', 'comment_count': '', 'share_count': '', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/086a87500fc12fa023e6f1b7ec2ec994/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/8f9d1afc032c1c694fa080a54cd48c93/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/0f4fa2907c253e171f3e6870bf256e21/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/5c733c52e3fa123a6b5b1376669c3de6/notes_pre_post/1040g3k831va9rvmu2g005ouskr6pun1jilkn1o8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/eca2396e67f8e86498bfeb074a22fbce/notes_pre_post/1040g3k831va9rvk7ig005ouskr6pun1jt8i1l80!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/4b3caa9b8821276e883c07b438c198fd/notes_pre_post/1040g3k831va9rvidii005ouskr6pun1jrevdeug!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/e11c826a3f1a1f1ed6c6cfddb5480475/notes_pre_post/1040g3k831va9rvfpjq005ouskr6pun1jp9ra11o!nd_dft_wlteh_webp_3', 'tag_list': '课题申报书,教育课题,教学课程,课题怎么写,六育协同,课题范文,课题范文分享,课题申报', 'last_modify_ts': 1776955588546, 'note_url': 'https://www.xiaohongshu.com/explore/69ea19a4000000001e00dfa0?xsec_token=AB-Kw1pgh4a9ki1JHIdRngngODBnEh6FKJQF5LNSylBtY=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngODBnEh6FKJQF5LNSylBtY='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea12280000000020003802', 'type': 'normal', 'title': '333day6', 'desc': '洋务派教育改革的两个重要例子 京师同文馆（论述题）和福建船政学堂（特点） 分别从它们的简介 发展特点和意义来展开介绍 教育思想主 要是讲了张之洞和他的“中体西用” 首提冯桂芬 张理论化  张《劝学篇》:简介 内容 简评和历史作用与局限  外国近代教育过渡从文艺复兴开始 夹带宗教改革 总的特点有5方面 人文教育3人物 宗教改革有3支:路德 加尔文 英国国教#凯程打卡[话题]# #333教育学综合[话题]# @教育学徐影', 'video_url': '', 'time': 1776947752000, 'last_update_time': 1776947752000, 'user_id': '69db45870000000032035e9a', 'nickname': '蒋文文', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31usv6nq3iq6g5qer8m3smnkqb4af0a0', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '湖北', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/b83bbf75134b3e59d57a17813adfd396/notes_pre_post/1040g3k031va8nlboii605qer8m3smnkqjd1orn0!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/b6a222149a12551c9788330a77b6ab76/notes_pre_post/1040g3k031va8nlboii505qer8m3smnkqk35dl28!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/fb011852fa9eaaf6ad760b4caf9e140c/notes_pre_post/1040g3k031va8nlboii105qer8m3smnkq2qggsc0!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/e781840d5befa3b1e61f152cb969c3b9/notes_pre_post/1040g3k031va8nlboii5g5qer8m3smnkqokb8d6o!nd_dft_wgth_webp_3', 'tag_list': '凯程打卡,333教育学综合', 'last_modify_ts': 1776955588548, 'note_url': 'https://www.xiaohongshu.com/explore/69ea12280000000020003802?xsec_token=AB-Kw1pgh4a9ki1JHIdRngniewdorUYbC9RiYud8VGsW8=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniewdorUYbC9RiYud8VGsW8='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea112a000000002301fc7c', 'type': 'normal', 'title': '“优秀传统文化+思政教学改革”课题绝了', 'desc': '今天给大家分享一份超有料的课题申报书范文，课题名称：优秀传统文化对高职思想政治教育教学改革的影响 研究\n本文章聚焦优秀传统文化对高职思政教育教学改革的影响，立足高职育人痛点，分析传统文化融入的契合性与多维影响，调研现存问题，构建 “内容 — 方法 — 师资 — 评价 — 保障” 的融合路径，创新三位一体融合理念与闭环模式，为高职思政改革提供理论与实践支撑。\n分享给大家这篇宝藏课题申报书范文，供大家参考学习！\n#课题立项[话题]# #课题研究[话题]# #思政[话题]# #传统文化[话题]# #思政教学[话题]# #高职[话题]# #教育课题[话题]# #教师课题[话题]# #教师评职称[话题]# #课题研究[话题]#', 'video_url': '', 'time': 1776947498000, 'last_update_time': 1776947498000, 'user_id': '63e3872500000000260123c8', 'nickname': '岁穗', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31r0a36hc7o6g5ov3gsipi8u86ju0isg', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/9f9f7c8b49fc89f7087fc5a656891043/1040g2sg31v91a7b1jq9g5ov3gsipi8u8j6eevj0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/4a0867432fca4e56034577defbf31ea7/1040g2sg31v91a7b1jqd05ov3gsipi8u8ev9m75g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/9f5d6ffe5a48df47f988da16d6a48447/1040g2sg31v91a7b1jq905ov3gsipi8u8j5l8v00!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/6545b58630b4292360ffedeee924f520/1040g2sg31v91a7b1jq805ov3gsipi8u80bo7m20!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/b9bc28835970b80ce1d5f26c12d9992c/1040g2sg31v91a7b1jqa05ov3gsipi8u86sb0h7g!nd_dft_wlteh_webp_3', 'tag_list': '课题立项,课题研究,思政,传统文化,思政教学,高职,教育课题,教师课题,教师评职称', 'last_modify_ts': 1776955588550, 'note_url': 'https://www.xiaohongshu.com/explore/69ea112a000000002301fc7c?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnoKnAZl47cjLuJEn5FWSHRI=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnoKnAZl47cjLuJEn5FWSHRI='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea0a50000000001b022187', 'type': 'normal', 'title': '人工智能赋能英语课程教学课题，直接立项', 'desc': '今天给大家分享一份人工智能赋能教育教学改革课题申报书范文，课题名称：人工智能赋能下英语视听说课程混合式教学新范式的理论构建与逻辑框架研究\n本文章聚焦教育数字化转型背景，针对高校英语视听说教学场景单一、评价滞后、技术应用浅层等痛点，融合人工智能与混合式教学，构建 “人机协同、双线融合” 的教学新范式，梳理目标、内容、流程、技术、评价五维逻辑框架，经调研与实践验证，形成可推广的教改方案，弥补理论与实践脱节问题。\n分享给大家这篇宝藏课题申报书范文，供大家参考学习！\n#课题申报书[话题]##教育课题[话题]##ai[话题]##英语课题[话题]##英语[话题]##教学课题[话题]#  #课题[话题]##课题研究[话题]##课题立项[话题]##人工智能#混合式教学#课题分享#课题范文#课题范文分享', 'video_url': '', 'time': 1776945744000, 'last_update_time': 1776945745000, 'user_id': '64a8c926000000002a036521', 'nickname': '课题申报陈老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31o5p9ulamm6g5p58p4jamp91vmsvpoo', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/bf09d1616e23c8c9978362e911ac69f0/notes_pre_post/1040g3k031va7vsfb2g6g5p58p4jamp91imse5i0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/54e1981ac4dec5e01bba766025dfa05b/notes_pre_post/1040g3k031va7vsliig4g5p58p4jamp91fvgf13o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/411c788cca4f38901fcbbb848c9bd5f4/notes_pre_post/1040g3k831va7vsja2id05p58p4jamp91lo6t29g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/4972f1adb4753cf9525e8da2f0dcd956/notes_pre_post/1040g3k031va7vsliig5g5p58p4jamp913tnhrdo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/48baa19a760f69ea981d0708e7bc1ee2/notes_pre_post/1040g3k831va7vsja2ibg5p58p4jamp91o3fp370!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/5cee4d123fdf1e5e503730f0dcfbc847/notes_pre_post/1040g3k031va7vsliig6g5p58p4jamp91cemae7g!nd_dft_wlteh_webp_3', 'tag_list': '课题申报书,教育课题,ai,英语课题,英语,教学课题,课题,课题研究,课题立项', 'last_modify_ts': 1776955588553, 'note_url': 'https://www.xiaohongshu.com/explore/69ea0a50000000001b022187?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnonqn8EoZ55eBfCssWyILkE=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnonqn8EoZ55eBfCssWyILkE='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea050b0000000020013003', 'type': 'normal', 'title': 'kc教育学打卡第七天（第三期）', 'desc': '今天学习了法国的教育改革，比英国的少多了！法国的进程多数是跟着英国来的，并且法国的法案多数都没有实施，但是法国仍然很难记，好好学习法国！加油！#凯程333[话题]# #333教育学[话题]# #凯程教育学[话题]#', 'video_url': '', 'time': 1776944395000, 'last_update_time': 1776944395000, 'user_id': '62df39a2000000001f007353', 'nickname': '璟璟璟（被拉比点过赞版）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31u14tcqrne0g5omv76h7osqj45ikud8', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '湖南', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232245/9a73b15818066c9fe69f6597442f0343/notes_pre_post/1040g3k831va789skjq705omv76h7osqjoem13bo!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/1732e72e198d7eec241ae33dbe027e73/notes_pre_post/1040g3k831va789skjq7g5omv76h7osqj815aovo!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/475b919b3f0c565c4a5553e8421c1b56/notes_pre_post/1040g3k831va789skjq805omv76h7osqjo88fki0!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/515a40a8b7e411ba910252c73d49afe5/note_pre_post_uhdr/1040g3r831va78m7g2g705omv76h7osqj4hgoje0!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/ac1bee9ec08b27e236f70454181f971f/note_pre_post_uhdr/1040g3r831va78m7g2g7g5omv76h7osqj6m7aqig!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232245/31630d25a6e0593e350c7bc1926a8855/note_pre_post_uhdr/1040g3r831va78m7g2g805omv76h7osqjee682i0!nd_dft_wgth_webp_3', 'tag_list': '凯程333,333教育学,凯程教育学', 'last_modify_ts': 1776955588555, 'note_url': 'https://www.xiaohongshu.com/explore/69ea050b0000000020013003?xsec_token=AB-Kw1pgh4a9ki1JHIdRngniHQ3rAzSoFuaTUUXW1AM74=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniHQ3rAzSoFuaTUUXW1AM74='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea04f6000000002003905f', 'type': 'normal', 'title': '贾老师26年教育热点时政阶段性盘点总结', 'desc': '2026年教育政策聚焦规范管理、人工智能、职业教育、考试公平和战略规划五大领域，通过系统治理、数字化转型和类型化改革，推动教育回归育人本位，解决“急难愁盼”问题，面向未来布新局。#贾老师教育学考研辅导[话题]# #教育学考研[话题]# #教育热点[话题]# #教育时政[话题]# #教育博士[话题]# #333教育学考研[话题]# #311教育学考研[话题]#', 'video_url': '', 'time': 1776944374000, 'last_update_time': 1776944374000, 'user_id': '626933a20000000010004a85', 'nickname': '贾老师教育学', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31o3bt9a56m605oj96eh40ik5ihiiqfg', 'liked_count': '5', 'collected_count': '3', 'comment_count': '', 'share_count': '1', 'ip_location': '吉林', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/acf4ca2c5cb522a0561325d24443f5bb/1040g2sg31va7afa22ql05oj96eh40ik5ahbo08g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/18e95177c6411d9cd9ad2fe53e95110c/1040g2sg31va7afa22qf05oj96eh40ik5jj00cno!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/82d470b27076e7a1a5ad27033ff3c3a0/1040g2sg31va7afa22qg05oj96eh40ik5kn4ckgg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/f555f47e78cb23337ca4120b5a62b40a/1040g2sg31va7afa22qh05oj96eh40ik5i9do0o8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/3951cea2c086e74a99dd276d84f32a6d/1040g2sg31va7afa22qig5oj96eh40ik58op3dj0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/c0e34dc598504f391f07f1c78c2da213/1040g2sg31va7afa22qi05oj96eh40ik54t5bhng!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/35ae89ba28a6a60e8a1999aec6eee80b/1040g2sg31va7afa22qj05oj96eh40ik5hb83ito!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/c41ab43b6540f9eef4f89a1535399d74/1040g2sg31va7afa22qk05oj96eh40ik5q9dajm8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/360bd4800071a6e709df0711a9b7c328/1040g2sg31va7afa22qkg5oj96eh40ik59lqk8m8!nd_dft_wlteh_webp_3', 'tag_list': '贾老师教育学考研辅导,教育学考研,教育热点,教育时政,教育博士,333教育学考研,311教育学考研', 'last_modify_ts': 1776955588557, 'note_url': 'https://www.xiaohongshu.com/explore/69ea04f6000000002003905f?xsec_token=AB-Kw1pgh4a9ki1JHIdRngntKOoPja630rjLVzVPd0anQ=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngntKOoPja630rjLVzVPd0anQ='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9ea1a0000000012012806', 'type': 'normal', 'title': '教育类中文核心期刊（北大核心、CSSCI、AMI\n今天小枫给大家整理了3本教育类中文核心期刊，发表教育理论、教育课程改革的文章。一起来看看吧，有论文方面 问题可以问哦\n---\n\t\n[一R]《教育研究》\n\t\n期刊简介：是教育理论界的权威期刊，注重理论性和学术性，关注教育领域的重大理论问题和实践问题，涵盖教育学原理、教育史、比较教育、教育经济与管理\n\t\n主要栏目：教育基本理论、教师教育、高考综合改革、热点聚焦、课程与教学、新思想指引教育、拔尖创新人才培养\n\t\n期刊级别：北大核心、CSSCI、AMI权威\n\t\n影响', 'desc': '教育类中文核心期刊（北大核心、CSSCI、AMI\n今天小枫给大家整理了3本教育类中文核心期刊，发表教育理论、教育课程改革的文章。一起来看看吧，有论文方面问题可以问哦\n---\n\t\n[一R]《教育研究》\n\t\n期刊简介：是教育理论界的权威期刊，注重理论性和学术性，关注教育领域的重 大理论问题和实践问题，涵盖教育学原理、教育史、比较教育、教育经济与管理\n\t\n主要栏目：教育基本理论、教师教育、高考综合改革、热点聚焦、课程与教学、新思想指引教育、拔尖创新人才培养\n\t\n期刊级别：北大核心、CSSCI、AMI权威\n\t\n影响因子：8.626\n\t\n发文量：年发文量162篇，其中高等教育、职业教育、教育强国、义务教务、基础教育文章占比比较多\n---\n\t\n[二R]《课程・教材・教法》\n\t\n期刊简介：聚焦于课程、教材和教学方法的研究，是我国基础教育领域的重要刊物。它紧密围绕基础教育课程改革的实际，深入探讨课程设计、教材编写、教学方法创新\n\t\n主要栏目：学科研究、“语文独立设科120周年”笔谈、课程研究、教学理论与方法、教材研究、统 编教材、教师教育、学术纵横\n\t\n期刊级别：北大核心、CSSCI、AMI核心\n\t\n影响因子：4.06\n\t\n发文量：年发文量285篇，其中核心素养、课程改革、课程标准、学科核心素养、教材建设文章占比比较多\n---\n\t\n[三R]《中国教育学刊》\n\t\n期刊简介：以基础教育研究为主，兼顾职业教育、高等教育等领域，关注教育热点难点问题，注 重理论联系实际，倡导学术创新。它既刊登教育理论研究成果，也发表教育实践经验总结\n\t\n主要栏目：广告图片_广告·书评、广告图片_作品欣赏、广告图片_课题风采、课程与教学、教育治理研究、热点问题研究、学习贯彻全国教育大会精神——推进教育强国建设研究、中小学校党组织领导的校长负\n\t\n期刊级别：CSSCI、AMI核心\n\t\n影响因子：4.661\n\t\n发文量：年发文量1060篇，其中核心素养、基础教育、立德树人、教师专业发展、义务教育文章占比比较多\n\ufeff#教育类核心[话题]# #教育期刊[话题]# #艺术类期刊[话题]# #学术专著[话题]# #教师评职称[话题]# #北大核心[话题]# #期刊投稿[话题]#', 'video_url': '', 'time': 1776937498000, 'last_update_time': 1776937499000, 'user_id': '5d6a1b0c0000000001006c62', 'nickname': '几片茉莉', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31v5vo1nf2s605nba3c608r3217k6d1g', 'liked_count': '1', 'collected_count': '3', 'comment_count': '', 'share_count': '', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/b2f8a58d2298c347c15c9f36b99a0258/notes_pre_post/1040g3k031v9mjfiqhm505nba3c608r32i8e7q8o!nd_dft_wlteh_webp_3', 'tag_list': '教育类核心,教育期刊,艺术类期刊,学术专著,教师评职称,北大核心,期刊投稿', 'last_modify_ts': 1776955588559, 'note_url': 'https://www.xiaohongshu.com/explore/69e9ea1a0000000012012806?xsec_token=ABdxuakkykQQRfchaFNorE1tJKHmLJlZRd49SvNvximkA=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1tJKHmLJlZRd49SvNvximkA='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9e7a1000000001f031800', 'type': 'normal', 'title': '教育局最新通知，26届考生太幸运了！', 'desc': '教育部刚发布两条重磅通知，2026年中考迎来多项重大改革，关键信息已经明确。我整理出 7 条核心内容，初 三家长务必提前吃透，不然等到 6 月考试再懂就晚了。\n第一条，考试形式全面调整。今年中考正式实行两考合一，毕业考试和升学考试合并进行，孩子不用再分心准备两场考试，压力直接减半。而且全省统一命题覆盖率持续提升，命题方向明确要求不考偏题、不怪题、不抠难题，重心全部放在基础知识和核心能力上，只要基础打牢，分数就不会 差。\n第二条，普高录取比例大幅上调。上面明确要求扩增高中学位，今年多地普高录取率将从原来的 50% 左右，大幅提升至 70% 以上。以前成绩中等的孩子想上高中难上加难，现在机会大大增加。\n第三条，计分科目做减法，不少地方生物、地理不再计入总分，只按等级考查，大部分地区道法、历史还改成开卷，总分整体下调，孩子压力能小一些。\n第四条，体育分值继续上调，物理化学实验操作分值加大，综合素质评价也正式纳入录取参考，光靠文化课成绩，已经不够用了。\n第五条，录取方式更加多元，除了统招，还会增加特长生、特色班、项目式培养等多种通道，偏科、有特长的孩子也能找到适合自己的升学路径。\n第六条， 2026 年中考作文七大方向基本清晰，分别围绕家国情怀、传统文化、劳动实践、绿色环保、科技创新、青春成长、责任担当。别再让孩子瞎准备范文了。已经帮大家总结好了，看这本《中考作文预测》就够了，拿来可以直接用。作文分值占比高，直接影响总分排名。\n第七条，今年历史和道法的开卷考要注意，开卷不是更容易，而是会更难，带课本几乎找不到完整的答案，而这本《开卷速查》把初中所有的知识点都总结好了，并且还有答题的模版，所以只需要带它就够了。（这两本书放我橱窗里了）。家长直接给孩子就行了，考完他会感谢你！（不是开卷考的地区也可以用来总复习）\n最后祝愿所有 2026 届中考生金榜题名、超常发挥，考上心仪的高中！#教育[话题]# #家庭教育[话题]#   #中考[话题]# #初三[话题]# #家长必读[话题]# #初三家长必看[话题]#', 'video_url': '', 'time': 1776936865000, 'last_update_time': 1776936865000, 'user_id': '6454c0d3000000001002ba0b', 'nickname': '拾光谢老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31krhlo7a306g5p2ko39k5egbpdfm720', 'liked_count': '4', 'collected_count': '5', 'comment_count': '2', 'share_count': '1', 'ip_location': '湖南', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/4bc426f7482007d9eea764eb089fc51a/notes_pre_post/1040g3k831va3o4d4iqkg5p2ko39k5egb2g49umo!nd_dft_wlteh_webp_3', 'tag_list': '教育,家庭教育,中考,初三,家长必读,初三家长必看', 'last_modify_ts': 1776955588561, 'note_url': 'https://www.xiaohongshu.com/explore/69e9e7a1000000001f031800?xsec_token=ABdxuakkykQQRfchaFNorE1tc-c978TmmwelZFLKGg7vY=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1tc-c978TmmwelZFLKGg7vY='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9d9d30000000020000800', 'type': 'normal', 'title': '教育界每一天都在改稻为桑。', 'desc': '每一次教研每一次改革每一次公开课\n都不合天时不合地利不合人意\n大单元群文阅读AI出题AI点评赛课教师\n一拍屁股就是一次轰轰烈烈的改稻为桑\n“我就不明白了，这改稻为桑上利国家，下利你们，为什么就是推行不下去”', 'video_url': '', 'time': 1776933331000, 'last_update_time': 1776933331000, 'user_id': '63d62e58000000002702a30a', 'nickname': '待那个山月', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/63e4f725905230158dfd4a0c.jpg', 'liked_count': '224', 'collected_count': '12', 'comment_count': '15', 'share_count': '31', 'ip_location': '贵州', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/0a507a6b131dbaf0057ace88d73d89d7/1040g00831va1vae42i6g5oum5pc9t8oabp7afvg!nd_dft_wlteh_webp_3', 'tag_list': '', 'last_modify_ts': 1776955588563, 'note_url': 'https://www.xiaohongshu.com/explore/69e9d9d30000000020000800?xsec_token=ABdxuakkykQQRfchaFNorE1p4001rPSurwEWvll5H5bXY=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1p4001rPSurwEWvll5H5bXY='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9c6b5000000001a02d83a', 'type': 'normal', 'title': '上海市浦东教育发展研究院主办·月刊集刊\n当前少量版面可发\n基本信息\n主办/主管：上海市浦东教育发展研究院\n刊号：ISSN/CN无（集刊）\n出版周期：月刊 ，每月定期出刊\n审稿周期：初审1个月内，整体1-3个月\n主要栏目\n专题聚焦｜教学探索｜改革热点｜管理视界\n德育探索｜课堂教学｜学前教育｜人物故事\n覆盖幼儿园·中小学全学段，适配各学科教研成果\n期刊优势\n✅ 知网全文收录，浦东地区认可度高\n✅ 立足基础教育改革，贴合一线教学实践\n✅ 理论+实操兼顾，教师/教研员/管理者均可投\n✅ 不收版面费，性价比拉满\n适合', 'desc': '上海市浦东教育发展研究院主办·月刊集刊\n当前少量版面可发\n基本信息\n主办/主管：上海市浦东教育发展研究院\n刊号：ISSN/CN无（集刊）\n出版周期：月刊，每月定期出刊\n审稿周期：初审1个月内，整体1-3个月\n主要栏目\n专题聚焦｜教学探索｜改革热点｜管理视界\n德育探索｜课堂教 学｜学前教育｜人物故事\n覆盖幼儿园·中小学全学段，适配各学科教研成果\n期刊优势\n✅ 知网全文收录，浦东地区认可度高\n✅ 立足基础教育改革，贴合一线教学实践\n✅ 理论+实操兼顾，教师/教研员/管理者均可投\n✅ 不收版面费，性价比拉满\n适合评职称、教学成果发表、教研经验交流\n中小学教师发论文稳妥之选\n#期刊[话题]# #评职称[ 话题]# #浦东教育[话题]# #教师评职称[话题]# #期刊投稿[话题]#  #中小学教师[话题]# #教育期刊[话题]# #知网收录[话题]#', 'video_url': '', 'time': 1776928437000, 'last_update_time': 1776928438000, 'user_id': '69dc94c9000000003302a807', 'nickname': '云边有个编辑部', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31v25a7262i405qesij4sta07sq7bp90', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '四川', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/da9be19e141fb92678671c4de933113a/notes_pre_post/1040g3k031v9m540m2a4g5qesij4sta07ro7b9k8!nd_dft_wlteh_webp_3', 'tag_list': '期刊,评职称,浦东教育,教师评职称,期刊投稿,中小学教师,教育期刊,知网收录', 'last_modify_ts': 1776955588565, 'note_url': 'https://www.xiaohongshu.com/explore/69e9c6b5000000001a02d83a?xsec_token=ABdxuakkykQQRfchaFNorE1jPzybfNF5-hN4MC9DBX3LM=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1jPzybfNF5-hN4MC9DBX3LM='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9c1040000000011020003', 'type': 'normal', 'title': '中国职业技术教育学会旅游职业教改研究项目', 'desc': '关于开展中国职业技术教育学会智慧文旅职业教育专业委员会2026年度旅游职业教育改革研究项目申请工作的通知[庆祝R][庆祝R]\n\t\n⏰截止日期：2026年5月21日\n\t\n[微笑R]研究方向\n文化和旅游深度融合发展人才培养、职业教育教学关键要素改革、职业教育数字化与国际化。\n\t\n[微笑R]经费资助\n项目分为重点项目和一般项目两类，分别给予5000元和2000元的资助。项目资助经费由专委会自筹。\n\t\n#高校教师[话题]# #中国职业技术教育学会[话题]# #旅游职业教育[话题]# #教育教学改革研究项目[话题]# #教育教改项目[话题]# #职业教育教改项目[话题]# #智慧文旅职业教育专业委员会[话题]# #职业教育[话题]# #职业教育数字化[话题]# #文化和旅游[话题]#', 'video_url': '', 'time': 1776926980000, 'last_update_time': 1776926981000, 'user_id': '69a289ff000000001c036caa', 'nickname': '宇浩商务咨询', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/dcf88562-fbf2-3e46-9cc9-f663662e2ee6', 'liked_count': '1', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/bdb23dce032f3bab285d2a75017795c0/spectrum/1040g0k031v9uskv4hu005qd2h7vn6r5aug2kq58!nd_dft_wlteh_webp_3', 'tag_list': '高校教师,中国职业技术教育学会,旅游职业教育,教育教学改革研究项目,教育教改项目,职业教育教改项目,智慧文旅职业教育专业委员会,职业教育,职业教育数字化,文化和旅游', 'last_modify_ts': 1776955588567, 'note_url': 'https://www.xiaohongshu.com/explore/69e9c1040000000011020003?xsec_token=ABdxuakkykQQRfchaFNorE1hdDa-a7IaDvTpjSjyY2fNQ=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1hdDa-a7IaDvTpjSjyY2fNQ='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9b980000000001a02472f', 'type': 'normal', 'title': '物流教育改革成果官宣｜解锁专业人才培养新', 'desc': '聚焦现代物流行业痛点，深耕课堂教学改革，历经多轮实践打磨，我们的成果报告正式发布啦！以“德技 并修、产教融合、数字赋能”为核心，打破传统教学壁垒，为现代物流管理专业人才培养注入新活力，干货拉满，建议物流教育人、行业从业者收藏！\n🔍 三大核心抓手，破解物流教学痛点\n摒弃“重理论、轻实践”“重技能、轻素养”的传统模式，构建三位一体的教学改革体系，让培养的人才适配行业发展、贴合岗位需求👇\n🏆 德技并修：立德为先 ，技强为基\n将思政教育与专业技能深度融合，既锤炼学生仓储管理、运输调度、供应链规划等核心技能，更培育诚信经营、责任担当、精益求精的职业素养，让物流学子“技有所长、德有所养”，成长为德才兼备的行业从业者。\n🤝 产教融合：校企同心，共育人才\n联动头部物流企业、行业协会，搭建协同育人平台，将企业真实项目、岗位真实需 求引入课堂，实现“课堂即岗位、教学即实践”。企业导师全程参与教学，学生沉浸式体验物流全流程，毕业后快速适配岗位，实现“学用无缝衔接”。\n💻 数字赋能：紧跟趋势，创新升级\n顺应数字物流、智慧供应链发展趋势，将大数据、物联网、人工智能等数字技术融入教学全过程，升级智慧物流实训场景，培养学生数字化操作、智能化管控能力 ，破解传统物流人才“懂技能、不懂数字”的短板，适配行业转型升级需求。\n📈 改革见成效，成果超亮眼🌟\n经过多轮实践探索，教学改革取得实打实的成效，用实力彰显创新价值：\n✔️ 教学质量提升：打造省级精品课程、优质实训基地，课堂教学满意度达98%以上\n✔️ 技能成果丰硕：学生在全国、省级物流技能竞赛中斩获奖项40余项，培育行业技术能手8名\n✔️ 就业质量领跑：毕业生就业率达95%以上，多数入职京东物流、顺丰速运等头部企业，岗位适配度高\n✔️ 示范效应凸显：改革模式已推广至省内外20余所院校，成为物流专业教学改革标杆\n📢 初心致远，聚力前行\n现代物流是实体经济的血脉，人才是行业发展的核心动力。此次成果报告的发布，是对过往教学改革实践的总结，更 是对未来人才培养的展望。#教学成果奖[话题]# #人才培养[话题]# #课题申报[话题]# #教学成果[话题]##物流[话题]# #高校教育[话题]#@小红书创作助手 @薯队长', 'video_url': '', 'time': 1776925056000, 'last_update_time': 1776925057000, 'user_id': '65a0acd1000000001f0132b8', 'nickname': '老陈讲教学成果奖课题-字节咨询', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/65dee4fdffb01b00013beb9d.jpg', 'liked_count': '1', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '山东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/21ff2d37f9d6265b5544a54c603de356/notes_pre_post/1040g3k031v9u4c78jq6g5pd0lj8nqcloea926ng!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/81c399bd0aedce20cd182f1d1e1736e2/notes_pre_post/1040g3k031v9u4c78jq5g5pd0lj8nqclo933o948!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/5b78c4b03e0fd1103704e2948b274eab/notes_pre_post/1040g3k031v9u4c78jq205pd0lj8nqcloo2ql628!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/7fc5b0a10026926a16b9b9a029d60743/notes_pre_post/1040g3k031v9u4c78jq2g5pd0lj8nqclohtjs7p8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/322e6600a2f6f4fd0fc7a900e70cd7a8/notes_pre_post/1040g3k031v9u4c78jq005pd0lj8nqcloqshod58!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/a2591a072864184410b6fbc46f75699d/notes_pre_post/1040g3k031v9u4c78jq4g5pd0lj8nqclotnb4rlo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/f4b56cf356766204e11d4b2bac01581d/notes_pre_post/1040g3k031v9u4c78jq605pd0lj8nqcloim5cabo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/63a3b8ecce2ae6984232b9a4aef020dd/notes_pre_post/1040g3k031v9u4c78jq405pd0lj8nqclo1cb9lbg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/1f98b4b0b759ab2ea4d8f72dccc050f8/notes_pre_post/1040g3k031v9u4c78jq505pd0lj8nqclojefb2c8!nd_dft_wlteh_webp_3', 'tag_list': '教学成果奖,人才培养,课题申报,教学成果,物流,高校教育', 'last_modify_ts': 1776955588570, 'note_url': 'https://www.xiaohongshu.com/explore/69e9b980000000001a02472f?xsec_token=ABdxuakkykQQRfchaFNorE1mgM6GDkYwrDKaSgoKjhE7o=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1mgM6GDkYwrDKaSgoKjhE7o='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9a343000000002300500d', 'type': 'normal', 'title': '广东省2026年教育评价改革主题征文', 'desc': '#广东省教育评价改革征文[话题]# #广东省教育评价改革主题征文[话题]# #广东省教育评价改革主题征文活动[话题]# #教育评价改革[话题]# #教育评价改革典型案例[话题]# #教育评价改革主题征文[话题]# #五育并举[话题]# #五育融合[话题]#', 'video_url': '', 'time': 1776919363000, 'last_update_time': 1776919364000, 'user_id': '60e6de08000000000101f9d0', 'nickname': '清风', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31mg3vqhn586g5o76ro40bueg4go4ulo', 'liked_count': '4', 'collected_count': '10', 'comment_count': '', 'share_count': '4', 'ip_location': '安徽', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/5b3a8eb459b47f1ac292946819b396e1/1040g2sg31v9r9o4ejqkg5o76ro40bueg01fk18g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/5be398326957a3f23a0ca8ab9241b983/1040g2sg31v9r9o4ejqhg5o76ro40buegntkf4vo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/51f66008f575bab9069974d236191779/1040g2sg31v9r9o4ejqgg5o76ro40buegku62u0g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/9ce2e20dfbb4d31d8bd0cd683c13bb66/1040g2sg31v9r9o4ejqig5o76ro40bueg1lgtsh0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/9d2af696a5f0b0883c3d4e50c182375f/1040g2sg31v9r9o4ejqh05o76ro40buegoto0ru0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/e3d57115295ce49f9d38a387dc914977/1040g2sg31v9r9o4ejqi05o76ro40buegd7odbh0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/863ac681c76451cb71221cca530a58e1/1040g2sg31v9r9o4ejqj05o76ro40buegb197658!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/ba8a5efc0495996d5e55ae0c015c320a/1040g2sg31v9r9o4ejqfg5o76ro40buegesbc9lo!nd_dft_wlteh_webp_3', 'tag_list': '广东省教育评价改革征文,广东省教育评价改革主题征文,广东省教育评价改革主题征文活动,教育评价改革,教育评价改革典型案例,教育评价改革主题征文,五育并举,五育融合', 'last_modify_ts': 1776955588573, 'note_url': 'https://www.xiaohongshu.com/explore/69e9a343000000002300500d?xsec_token=ABdxuakkykQQRfchaFNorE1pLRka-GIuO4UvCw4F6MClU=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1pLRka-GIuO4UvCw4F6MClU='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9a3360000000023011c1f', 'type': 'normal', 'title': '《基础教育》', 'desc': '该刊关注基础教育改革与发展中的重点、难点和热点问题，展示基础教育领域最新研究成果，揭示基础教育改革与发展的理论脉络与实践走向，服务于国内外教育理论工作者、教育行政管理者、基础教育学校领导者与教师，以及关注基础教育理论进展和实践研究的各界人士。', 'video_url': '', 'time': 1776919350000, 'last_update_time': 1776919350000, 'user_id': '67c65a35000000000a03cfcf', 'nickname': '登科文献规划', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/a97f5abd-400a-32bd-9a34-3be337678f44', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '广东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/7d79ae02e060b3133a87353080eceb51/spectrum/1040g34o31v9rcrgvk0805pu6b8qinjufi7tn7tg!nd_dft_wlteh_webp_3', 'tag_list': '', 'last_modify_ts': 1776955588575, 'note_url': 'https://www.xiaohongshu.com/explore/69e9a3360000000023011c1f?xsec_token=ABdxuakkykQQRfchaFNorE1gWAQFru8RApHLzF9fnhybg=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1gWAQFru8RApHLzF9fnhybg='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e96178000000001a02e205', 'type': 'normal', 'title': '山东教育评价改革成果征集全攻略🔥', 'desc': '山东的教育工作者们看过来📢\n深化新时代教育评价改革典型案例和研究成果征集启动！\n省级学会+学术年会推 广+《年度观察》书稿收录，这份攻略助你拿下👇\n\t\n📌 征集主题（6大方向）\n1️⃣ 党委政府评价改革：联系学校、调研教育、述职述教，纠正片面升学率倾向\n2️⃣ 学校评价改革：幼儿园/中小学/中职/高校分类评价，质量监测结果应用\n3️⃣ 教师评价改革：教学述评、实绩考核、长周期科研评价、职称评审、发展性评价\n4️⃣ 学生评价改革：增值评价、综合素质评价档案、过程性+结果性考评、考试招生、拔尖创新人才评价\n5️⃣ 用人评价改革：品德+能力导向用人机制，破除学历门槛，人岗相适\n6️⃣ 改革保障实施：“十不得一严禁”、评价队伍专业化、AI赋能教育评价、政策宣传\n\t\n📌 征集类型\n🔹 典型案例：本地本校实践≥1年，取得实际成效\n🔹 研究成果：学术论文、研究报 告、专著、政策建议（可未发表）\n\t\n📌 谁可以参加？\n各级教育工作领导小组、教育行政部门、各级各类学校、教育科研机构、企事业单位及教育工作者\n⚠️ 山东省教育评价学会会员单位：每单位至少报1篇\n⚠️ 首批教育评价研究基地：至少报1篇研究成果\n\t\n📌 案例内容要求\n✅ 真实性：基于真实实践，数据详实\n✅ 创新性：体现山东特色，突破传统模式\n✅ 实效性：成效显著，可复制推广\n✅ 典型性：聚焦重点难点，示范引领\n📌 冲奖攻略（拿小本本记✍️）\n🔑 选题要“小”而“实”：聚焦一个具体评价改革点（如“小学数学增值评价校本实践”“教师教学述评制度落地案例”）\n🔑 结构清晰：背景（为什么改）→做法（怎么改）→成效（数据/案例说话）\n🔑 数据支撑：前后对比、 量表结果、师生反馈、升学/质量变化等\n🔑 体现山东特色：结合本地政策（如“十不得一严禁”落实、乡村教育评价等）\n🔑 可复制性：写清楚操作流程和关键步骤，让其他学校能照着做\n🔑 研究成果如论文，建议3000-5000字，附摘要关键词\n🔑 实证材料：政策文件、会议记录、评价工具、照片等打包提交#山东教师[话题]#   #山东省教师评职称[话题]#   #山东省教育评价改革典型案例[话题]#   #教育评价改革[话题]#   #教育评价改革案例[话题]#   #教育评价[话题]#', 'video_url': '', 'time': 1776902520000, 'last_update_time': 1776902520000, 'user_id': '68df92c4000000003202a1f0', 'nickname': '开原市在逃保镖', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31umkjtlt2o6g5q6vib2cl8fgh8tvg1g', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '安徽', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/27926178d0848aa6dd48a0e330a63486/1040g00831v9j6gi2ia0g5q6vib2cl8fg2mju71g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/f739f24a9282d086df7854ca6515f6c2/1040g00831v9j6gi2ia105q6vib2cl8fgas0tb70!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/fa92f0f31b292c2ea517732385f2c4fe/1040g00831v9j6gi2ia1g5q6vib2cl8fgnkb3mfo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/ccb1eff55ad5e8fa5031ae9ec54eacbc/1040g00831v9j6gi2ia205q6vib2cl8fg09ejb50!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/2b053f72a3922f1a456c674e4885a067/1040g00831v9j6gi2ia2g5q6vib2cl8fg9dagmp0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/e34a2ad7883c20c5f22d169128c1b2da/1040g00831v9j6gi2ia305q6vib2cl8fgocl1dg8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/5ab330488f43356450494195bd51c724/1040g00831v9j6gi2ia3g5q6vib2cl8fgscadg0o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/1dd9c6cce85634f0a27569013f1df982/1040g00831v9j6gi2ia405q6vib2cl8fgn1s31bg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/dd31041c9f0208f2db211a0d316ab36e/1040g00831v9j6gi2ia4g5q6vib2cl8fgbl9fahg!nd_dft_wlteh_webp_3', 'tag_list': '山东教师,山东省教师评职称,山东省教育评价改革典型案例,教育评价改革,教育评价改革案例,教育评价,教育评价,教育评价改革案例,教育评价改革,山东省教育评价改革典型案例,山东省教师评职称,山东教师,教育评价,教育评价改革案例,教育评价改革,山东省教育评价改革典型案例,山东省教师评职称,山东教师', 'last_modify_ts': 1776955588577, 'note_url': 'https://www.xiaohongshu.com/explore/69e96178000000001a02e205?xsec_token=ABdxuakkykQQRfchaFNorE1m-UzcaTfcA1FSxuEzs4FlE=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1m-UzcaTfcA1FSxuEzs4FlE='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e8c1f8000000001f004a5d', 'type': 'normal', 'title': '分享！人工智能+职业教改课题申报范文', 'desc': '教育部人工智能+’职业教育教学改革创新研究课题范文来了！\n高职老师速码AI + 职教教学改革干货\n人智协同视域下，打造师生 - AI 三元互动教学模式，开发课程 AI 助教，破解高风险专业课教学痛点，全流程可落地的教学范式，职教数字化改革直接参考！\n#教育部课题[话题]# #人工智能课题[话题]# #职业教育[话题]# #教育改革课题[话题]# #AI赋能教育[话题]# #课题申报[话题]# #课题立项[话题]# #教育课题[话题]# #职业教育教学课题[话题]# #评职称[话题]#', 'video_url': '', 'time': 1776861688000, 'last_update_time': 1776861688000, 'user_id': '69c0d456000000003303b911', 'nickname': '吃饱就写课题', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31ub4culkia3g5qe0qhbcve8h0k0fmh0', 'liked_count': '15', 'collected_count': '40', 'comment_count': '1', 'share_count': '7', 'ip_location': '江西', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/cff3f6a22fec320e56bf02775a8c6b7c/1040g00831v8ocs58jq605qe0qhbcve8hg49v6hg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/c19b9f96e98e7c85a9a4cf86f2614a3e/1040g00831v8ocs58jq4g5qe0qhbcve8hhjso9to!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/bee0e997292cd7a5fffcb371e1d4e34e/1040g00831v8ocs58jq5g5qe0qhbcve8hlnj4jrg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/39420124c66ccfe80fce3497914bf23d/1040g00831v8ocs58jq305qe0qhbcve8hdgudoq0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/4ea70a790c4830f178d93f91d2cb498a/1040g00831v8ocs58jq1g5qe0qhbcve8h0ut5j2g!nd_dft_wlteh_webp_3', 'tag_list': '教育部课题,人工智能课题,职业教育,教育改革课题,AI赋能教育,课题申报,课题立项,教育课题,职业教育教学课题,评职称', 'last_modify_ts': 1776955588578, 'note_url': 'https://www.xiaohongshu.com/explore/69e8c1f8000000001f004a5d?xsec_token=ABmk4aAslOFz7CfZFRgbwGS1VMIy9hV20oOvhxunLM7YU=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABmk4aAslOFz7CfZFRgbwGS1VMIy9hV20oOvhxunLM7YU='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e82bcc000000002200dd5f', 'type': 'normal', 'title': '教育部重磅发布AI+教育行动计划！普通家庭', 'desc': '#AI教育[话题]# #教育改革[话题]# #智慧教育[话题]# #家庭教育[话题]# #AI带娃[话题]#', 'video_url': '', 'time': 1776828644000, 'last_update_time': 1776823244000, 'user_id': '622497c2000000001000b631', 'nickname': '烽哥说AI教育', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31uvdodle34705oh4iv141dhh4tpfpvg', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '', 'ip_location': '安徽', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/632eeda6da1e1f88cf05c2fa91dedd91/notes_pre_post/1040g3k031v8cildahm005oh4iv141dhh6m2qffo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/cbf9bd9ddfc6753019bf74b45e8bd5cd/notes_pre_post/1040g3k031v8cildahm0g5oh4iv141dhhd4h103g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/96d4f1fe5010502292772342a836669e/notes_pre_post/1040g3k031v8cildahm105oh4iv141dhhnbk3ub0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/49b717dd8effd622477cf66d5c2c200d/notes_pre_post/1040g3k031v8cildahm1g5oh4iv141dhhf2ssca8!nd_dft_wlteh_webp_3', 'tag_list': 'AI教育,教育改革,智慧教育,家庭教育,AI带娃', 'last_modify_ts': 1776955588580, 'note_url': 'https://www.xiaohongshu.com/explore/69e82bcc000000002200dd5f?xsec_token=ABmk4aAslOFz7CfZFRgbwGSynj-uxl8DLy8oseELUX64s=&xsec_source=pc_search', 'source_keyword': "[' 教育改革'", 'xsec_token': 'ABmk4aAslOFz7CfZFRgbwGSynj-uxl8DLy8oseELUX64s='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e820c7000000001a028ac3', 'type': 'normal', 'title': '教育部最新文件，不读高中照样上本科！！！', 'desc': '2026中考成绩不好≠完了！\n如果你是初三家长，还在因为孩子成绩不理想而焦虑得睡不着觉，甚至感觉 天都要塌了，那这篇笔记你一定要看完。\n\t\n✅今年2月，教育部出手了，专门印发了《关于深化职业教育教学关键要素改革的意见》，职业教育直接进入了“大洗牌”时代。\n政策红利已经砸脸上了，我给大家划几个重点，看完你就知道，这条路到底有多香👇\n\t\n🔥 一、专业大洗牌：新增的全是“高薪风口”！\n现在的职校专业，早不是你以为的“脏乱差”了。\n· 增新：国家直接瞄准低空经济、人工智能、高端装备、民生紧缺领域增设大量新专业。\n· 升级：老牌专业全面智能化，比如以前的汽车维修，现在叫“新能源智能网联汽车”。\n\t\n📈 二、升学通道全打通：中职生也能直接读“硕士”！\n这才是最硬核的！初中成绩不好，不代表孩子智商不行，只是不适合“死记硬背”的文化课。\n现在是真正的“文化素质+职业技能”评价时代。\n· 职教高考扩容：今年国家层面明确要完善职教高考制度，而且今年两会代表还建议：“打通中职、专科、本科到研究生的上升通道”！\n👉一句话：孩子读了中职，不仅能上大学，还能上职业本科。甚至未来还能考专硕、学硕！\n\t\n💰 三、技能人才薪资反超：凭本事吃饭更有底气\n\t\n别再迷信“只 有大学生才能拿高薪”的鬼话了。\n现在技术行业拿高薪的大有人在，很多热门专业薪资丰富。\n高级技师、技能大师年薪30万到50万，远远超过普通本科白领。网友调侃说：现在“学好技能，不比上大学差”已经成了家长和学生的共识。\n\t\n最后想对家长说：\n如果你家孩子：\n✅ 动手能力强，但坐不住不爱背书\n✅ 成绩虽然不高，但不想早早出 去打工\n✅ 想升学，但担心普高压力太大\n\t\n2026年，请一定关注一下“3+4”中本贯通、职教高考班和五年制大专。\n不挤独木桥，可能才是对孩子人生最负责的选择。\n#2026中考 #中职升学 #职业教育 #初三家长 #中考分流 #职教高考 #中本贯通 #孩子教育', 'video_url': '', 'time': 1776820423000, 'last_update_time': 1776820424000, 'user_id': '69cdc5e100000000320196b3', 'nickname': '中职升学规划熊老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31ueklfn92q505qedongsj5ljof10890', 'liked_count': '4', 'collected_count': '3', 'comment_count': '', 'share_count': '', 'ip_location': '四川', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/b5f3fc5ba7336cb6e8708382099a4ce5/notes_pre_post/1040g3k031v8c6qgl2i6g5qedongsj5ljrjoheeo!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/e70c0cfdf1f18a27b481d12ecd88560b/notes_pre_post/1040g3k031v8c6qi03q5g5qedongsj5ljiuqvelo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/c9251f9060e7dc04afe6f7706cbbae0b/notes_pre_post/1040g3k031v8c6qi03q405qedongsj5ljcctesqg!nd_dft_wlteh_webp_3', 'tag_list': '', 'last_modify_ts': 1776955588582, 'note_url': 'https://www.xiaohongshu.com/explore/69e820c7000000001a028ac3?xsec_token=ABmk4aAslOFz7CfZFRgbwGSy9NhrnlVI2G8jNGVrs9UKg=&xsec_source=pc_search', 'source_keyword': "['教育改革'", 'xsec_token': 'ABmk4aAslOFz7CfZFRgbwGSy9NhrnlVI2G8jNGVrs9UKg='}
2026-04-23 22:46:28 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:46:28 MediaCrawler INFO (core.py:178) - [XiaoHongShuCrawler.search] Note details: [{'image_list': [{'width': 1224, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8029d328e2cd4339da3cb7c637f79dab/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_dft_wlteh_webp_3', 'trace_id': '', 'file_id': '', 'height': 1632, 'info_list': [{'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/3ca1f80c8c5bf03fe9c7a4d048b75c40/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_prv_wlteh_webp_3', 'image_scene': 'WB_PRV'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8029d328e2cd4339da3cb7c637f79dab/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_dft_wlteh_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/3ca1f80c8c5bf03fe9c7a4d048b75c40/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_prv_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/8029d328e2cd4339da3cb7c637f79dab/notes_pre_post/1040g3k831vac6b5o1m705ov4arv9ggvtvai89eg!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False}, {'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/31f64e08c83da492f2e9e99eaa11b5ac/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_prv_wlteh_webp_3', 'live_photo': False, 'file_id': '', 'width': 1080, 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/31f64e08c83da492f2e9e99eaa11b5ac/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/701e5014ff9e0492c021565d1c811a14/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_dft_wlteh_webp_3'}], 'height': 1527, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/701e5014ff9e0492c021565d1c811a14/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_dft_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/701e5014ff9e0492c021565d1c811a14/notes_pre_post/1040g3k831vac6b5o1m7g5ov4arv9ggvtk92dqp8!nd_dft_wlteh_webp_3', 'stream': {}}, {'file_id': '', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/9626b40a5fda5ea114c1c1f6ec91b3b0/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_dft_wlteh_webp_3', 'live_photo': False, 'height': 1527, 'width': 1080, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/9626b40a5fda5ea114c1c1f6ec91b3b0/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_dft_wlteh_webp_3', 'trace_id': '', 'info_list': [{'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/9dfc744c1a48ad54c38018e45382de69/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_prv_wlteh_webp_3', 'image_scene': 'WB_PRV'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/9626b40a5fda5ea114c1c1f6ec91b3b0/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_dft_wlteh_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/9dfc744c1a48ad54c38018e45382de69/notes_pre_post/1040g3k831vac6b5o1m805ov4arv9ggvtp4grbeg!nd_prv_wlteh_webp_3', 'stream': {}}, {'height': 1527, 'width': 1080, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/343a4f786960506b661cf0173d1ee3be/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_dft_wlteh_webp_3', 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/cb037955680e894dfafe96c993247bc1/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/343a4f786960506b661cf0173d1ee3be/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_dft_wlteh_webp_3'}], 'file_id': '', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/cb037955680e894dfafe96c993247bc1/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_prv_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/343a4f786960506b661cf0173d1ee3be/notes_pre_post/1040g3k831vac6b5o1m8g5ov4arv9ggvtkghoi2o!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False}, {'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/5aebf94c940c0a1ef88ce97dad00d901/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_dft_wlteh_webp_3', 'live_photo': False, 'file_id': '', 'height': 1527, 'width': 1080, 'trace_id': '', 'info_list': [{'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/f280d0dbecab2c1c6f63443ab274d7d8/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_prv_wlteh_webp_3', 'image_scene': 'WB_PRV'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/5aebf94c940c0a1ef88ce97dad00d901/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_dft_wlteh_webp_3'}], 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/5aebf94c940c0a1ef88ce97dad00d901/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_dft_wlteh_webp_3', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/f280d0dbecab2c1c6f63443ab274d7d8/notes_pre_post/1040g3k831vac6b5o1m905ov4arv9ggvtmj5oj4o!nd_prv_wlteh_webp_3', 'stream': {}}], 'ip_location': '山东', 'share_info': {'un_share': False}, 'type': 'normal', 'interact_info': {'comment_count': '', 'share_count': '1', 'followed': False, 'relation': 'none', 'liked': False, 'liked_count': '2', 'collected': False, 'collected_count': '3'}, 'desc': '#记录吧就现在[话题]#\n2026全国教育大会重磅发布「八大任务」✨，堪称未来5年教育改革的全景路线图！划重点👇\n💡 一号工程·立德树人\u200b\n✔ 告别填鸭说教→升级「社会实践大课 堂」+「AI育人课堂」\n✔ 身心健康成硬指标❗心理健康纳入评价体系\n✔ 加速构建中国原创教材体系📚\n🏫 民生刚需·资源布局\u200b\n✔ 动态应对「人口潮汐」：城市扩学位/乡村小班制\n✔ 县域高中振兴🚀：掐尖招生退散！减负落地小学取消期中考\n🎓 高教突围·龙头引领\u200b\n✔ 双一流扩容至200所！主攻理工农医+AI🔬\n✔ 资源倾斜中西部/人口大省📍破解高考地域差\n✔ 高校分类改革：拒绝千校一面！\n⚡ 科教融合·三位一体\u200b\n✔ 建交叉学科中心💻（AI+医疗/量子材料）\n✔ 打通实验室→生产线转化链🔗\n✔ 破解「有人没活干」结构性失业👔\n🔧 职教崛起·多元赛道\u200b\n✔ 普职融通双向流动↔打破升学独木桥\n✔ 新增低空经济/具身智能🔋等新专业\n✔ 「集群培养」毕业即上岗💼\n🤖 AI赋能·重塑教育\u200b\n✔ 全学段必修AI课📱从小培养数字素养\n✔ 破除唯分数❌强基计划扩容+体美纳入考核\n👩🏫 强师筑基·减负提质\u200b\n✔ 弘扬教育家精神✨提升职业荣誉感\n✔ 砍掉非教学负担📉盘活退休名师银龄讲学\n🌍 开放共赢·全球视野\u200b\n✔ 从引进来到输出中国教育方案🇨🇳\n✔ 筑牢安全防线🔒守护意识形态阵地\n💎八大任务环环相扣！从顶层设计到落地生根，勾勒中国教育高质量发展新图景🌟 备考党/家长/教育从业者速码住！\n#热点[话题]# #学科思政[话题]# #教育热点[话题]# #思政[话题]# #教育现代化[话题]# #思政热点[话题]# #教育大会[话题]#   #记录吧就现在[话题]#', 'user': {'user_id': '63e456fe00000000260043fd', 'nickname': 'A陈老师课题成果奖研究-慧启', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/675fc169bdd67700013d84d6.jpg', 'xsec_token': 'AB1K9ESwllwuKyJ33zwEg5ghZboqAznFgQB6678F8DwyU='}, 'tag_list': [{'id': '644a15b7000000002901d04c', 'name': '记录吧就现在', 'type': 'topic'}, {'id': '5c46829d000000000e009c0a', 'name': '热 点', 'type': 'topic'}, {'id': '5cd275a9000000000e00126f', 'name': '学科思政', 'type': 'topic'}, {'type': 'topic', 'id': '5d9f4c21000000000103e6cf', 'name': '教育热点'}, {'id': '5e65e4e500000000010055da', 'name': '思政', 'type': 'topic'}, {'id': '6176c822000000000101e790', 'name': '教育现代化', 'type': 'topic'}, {'name': '思政热点', 'type': 'topic', 'id': '6104233d0000000001002f1f'}, {'type': 'topic', 'id': '5de653d70000000001001608', 'name': '教育大会'}], 'at_user_list': [], 'time': 1776954560000, 'last_update_time': 1776954561000, 'note_id': '69ea2cc0000000001901e004', 'title': '思政热点:2026年全国教育大会“ 八大任务”', 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngq89fTwMnHoFKhME59Hv6s=', 'xsec_source': None}, {'time': 1776952000000, 'ip_location': '广东', 'note_id': '69ea22c0000000001f030c06', 'desc': '河北会计继续教育迎来重大改革，新规重点、时间节点一次性整理清楚，会计人员务必收藏！\n\t\n2026年度河北会计继续教育已 于4月7日正式开启，关键时间牢记：缴费截止2027年3月15日，全部课程学习、考试收尾截止2027年3月25日，逾期未完成，将直接影响会计档案记录、职称报考与资格审核。\n\t\n学分要求迎来全新调整，常规年度统一要求修满90学分，专业科目60学分、公需科目30学分，河北公需课需在人社部门平台学习。\n\t\n补学往年继教学分标准大幅上调，逐年递增：2025年不低于90学分、2024年100学分、2023年110学分、2022年120学分、2021年需达130学分，和往年标准差异极大，切勿按旧规学习。\n\t\n所有学员需在规定时限内完成课程学习、线上考试、学分同步及课程评价，单课完成后按页面提示操作，才算有效获取学分。学分对接完成后，所属地财政部门会在3个工作日内审核登记学分。\n\t\n新规变化多、学分要求更高，建议尽早完成学习，避免后期扎堆延误，影响个人财会相关业务办理！\n\t\n#河北会计继续教育 #会计继续教育补学 #会计人须知 #中级会计 #初级会计', 'tag_list': [], 'interact_info': {'liked': False, 'liked_count': '', 'collected': False, 'collected_count': '', 'comment_count': '1', 'share_count': '', 'followed': False, 'relation': 'none'}, 'image_list': [{'file_id': '', 'height': 1620, 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/7b27e45aa4d9decf85a1e2db14c74dfe/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_prv_wlteh_webp_3'}, {'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8e2930f3f97cd02204ab7871a329eb6b/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_dft_wlteh_webp_3', 'image_scene': 'WB_DFT'}], 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/8e2930f3f97cd02204ab7871a329eb6b/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_dft_wlteh_webp_3', 'stream': {}, 'width': 1080, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8e2930f3f97cd02204ab7871a329eb6b/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_dft_wlteh_webp_3', 'trace_id': '', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/7b27e45aa4d9decf85a1e2db14c74dfe/1040g2sg31vaav7vmiqk05pvkvkcjlqmoifhvok0!nd_prv_wlteh_webp_3', 'live_photo': False}], 'at_user_list': [], 'last_update_time': 1776952038000, 'share_info': {'un_share': False}, 'type': 'normal', 'title': '河北会计继教重大改革！学分新规+截止时间', 'user': {'user_id': '67f4fd19000000000e02ead8', 'nickname': '小司（备考）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31m9tee7olj205pvkvkcjlqmo68i1g50', 'xsec_token': 'ABvgwCq4xqWjmc3noTHgRwOTpYGIl_9ylUd1a9B4ayxBA='}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngniy5qBBI5XjiBaoKJ4mZ_IU=', 'xsec_source': None}, {'desc': '今天给大家分享一份人工智能赋能教育教学改革课题申报书范文，课题名称：六育协同“ＡI＋课程”教学的探索与实践研究\n本文章立足新时代全面育人与教育数字化转型，聚焦六育协同 + AI + 课程深度融合，以初中为试点，针对融合形式化、设计碎片化、师资不足、评价缺失等问题，构建教学模式、学科方案与多元评价体系，探索可落地的实践路径，丰富理论并为教育高质量发展提供示范。\n分享给大家这 篇宝藏课题申报书范文，供大家参考学习！\n#课题申报书[话题]##教育课题[话题]# #教学课程[话题]##课题怎么写[话题]##六育协同[话题]##课题范文[话题]# #课题范文分享[话题]# #课题怎么写[话题]# #课题申报[话题]#', 'tag_list': [{'id': '615f25e30000000001001e20', 'name': '课题申报书', 'type': 'topic'}, {'id': '618a572f0000000001003f82', 'name': '教育课题', 'type': 'topic'}, {'id': '629154a00000000001005023', 'name': '教学课程', 'type': 'topic'}, {'id': '627c67d8000000000101f32f', 'name': '课题怎么写', 'type': 'topic'}, {'id': '69e8650d000000000301c604', 'name': '六育协同', 'type': 'topic'}, {'id': '6496b14f000000001d013c08', 'name': '课题范文', 'type': 'topic'}, {'id': '6833c94f0000000012019620', 'name': '课题范文分享', 'type': 'topic'}, {'id': '5e68e5a2000000000100aec7', 'name': '课题申报', 'type': 'topic'}], 'time': 1776949668000, 'last_update_time': 1776949669000, 'ip_location': '江西', 'at_user_list': [], 'share_info': {'un_share': False}, 'note_id': '69ea19a4000000001e00dfa0', 'type': 'normal', 'title': '六育协同“AI+课程”教学课题，太好立项了', 'user': {'user_id': '63dca6cd0000000027035c33', 'nickname': '老根课题申报写作咨询（知慧圈）', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/64f82103b403790001c3321f.jpg', 'xsec_token': 'ABOB44GasmPOTWY95iMeV7f6xKfo1GgEcwB5DPEgy1_RI='}, 'interact_info': {'comment_count': '', 'share_count': '', 'followed': False, 'relation': 'none', 'liked': False, 'liked_count': '1', 'collected': False, 'collected_count': '3'}, 'image_list': [{'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/086a87500fc12fa023e6f1b7ec2ec994/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False, 'height': 4490, 'width': 3175, 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/039331e9598686e3e35f37d0fac8178f/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_prv_wlteh_webp_3', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/039331e9598686e3e35f37d0fac8178f/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/086a87500fc12fa023e6f1b7ec2ec994/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_dft_wlteh_webp_3'}], 'file_id': '', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/086a87500fc12fa023e6f1b7ec2ec994/notes_pre_post/1040g3k831va9rvag2gs05ouskr6pun1je5msrc8!nd_dft_wlteh_webp_3', 'trace_id': ''}, {'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8f9d1afc032c1c694fa080a54cd48c93/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_dft_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/8f9d1afc032c1c694fa080a54cd48c93/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_dft_wlteh_webp_3', 'file_id': '', 'height': 2560, 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/b4f07ae121c03311a6261500d4225e5e/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/8f9d1afc032c1c694fa080a54cd48c93/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_dft_wlteh_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/b4f07ae121c03311a6261500d4225e5e/notes_pre_post/1040g3k831va9rvcojq005ouskr6pun1jfprjrh8!nd_prv_wlteh_webp_3', 'stream': {}, 'live_photo': False, 'width': 1812, 'trace_id': ''}, {'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232245/4d54aa663d13e343ea90a18d3b36922d/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_prv_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232245/0f4fa2907c253e171f3e6870bf256e21/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False, 'width': 1812, 'info_list': [{'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/4d54aa663d13e343ea90a18d3b36922d/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_prv_wlteh_webp_3', 'image_scene': 'WB_PRV'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/0f4fa2907c253e171f3e6870bf256e21/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_dft_wlteh_webp_3'}], 'url': 'http://sns-webpic-qc.xhscdn.com/202604232245/0f4fa2907c253e171f3e6870bf256e21/notes_pre_post/1040g3k831va9rvps3q005ouskr6pun1j71l205o!nd_dft_wlteh_webp_3', 'trace_id': '', 'file_id': '', 'height': 2560}, {'stream': {}, 'live_photo': False, 'file_id': '', 'height': 2560, 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http:2026-04-23 22:46:28 MediaCrawler INFO (core.py:328) - [XiaoHongShuCrawler.batch_get_note_comments] Crawling comment mode is not enabled
2026-04-23 22:46:30 MediaCrawler INFO (core.py:183) - [XiaoHongShuCrawler.search] Sleeping for 2 seconds after page 1
2026-04-23 22:46:30 MediaCrawler INFO (core.py:138) - [XiaoHongShuCrawler.search] Current search keyword:  '中考']
2026-04-23 22:46:30 MediaCrawler INFO (core.py:148) - [XiaoHongShuCrawler.search] search Xiaohongshu keyword:  '中考'], page: 1
2026-04-23 22:46:31 MediaCrawler INFO (core.py:157) - [XiaoHongShuCrawler.search] Search notes response: {'has_more': True, 'items': [{'id': '69ea301e0000000020007007', 'model_type': 'note', 'note_card': {'type': 'normal', 'user': {'nick_name': '镇江数学化学于老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/61dc552f000000001000cc52.jpg?imageView2/2/w/80/format/jpg', 'user_id': '61dc552f000000001000cc52', 'nickname': '镇江数学化学于老师', 'xsec_token': 'ABUF1VcmaVO0JhdzFOSnvnlGZTDEM33Hd2sKvrnNux-7c='}, 'interact_info': {'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0', 'shared_count': '0'}, 'cover': {'height': 1600, 'width': 1200}, 'image_list': [{'height': 1600, 'width': 1200}, {'height': 2436, 'width': 3256}, {'width': 3268, 'height': 2400}, {'height': 2436, 'width': 3296}, {'height': 3448, 'width': 2324}, {'height': 3292, 'width': 2264}, {'height': 3476, 'width': 2324}, {'height': 3420, 'width': 2360}], 'corner_tag_info': [{'type': 'publish_time', 'text': '2分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnha0DPLYhDfWJxKneJvE_ZQ='}, {'id': '69ea2efb000000001a0346aa', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '家有中考生', 'user': {'user_id': '5aee649011be1016a851ccfc', 'nickname': '夏天夏天', 'xsec_token': 'ABxI_MqwUNajwkXYCVYCNi76Mhhtr1hA-JhCVJU87tOV4=', 'nick_name': '夏天夏天', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/5aee649011be1016a851ccfc.jpg?imageView2/2/w/80/format/jpg'}, 'interact_info': {'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0', 'shared_count': '0', 'liked': False}, 'cover': {'height': 2400, 'width': 1440}, 'image_list': [{'height': 2400, 'width': 1440}, {'height': 2400, 'width': 1440}], 'corner_tag_info': [{'type': 'publish_time', 'text': '7分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngMmJSjkeC3LDS8u1A1sPvM='}, {'id': '69ea2e83000000001e00cef6', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '中考', 'user': {'xsec_token': 'ABgFjc4mwR7ju_l1YiUi2BY0aEjMbQfkMIxnmZShaxuSg=', 'nick_name': '喵喵～是小苗呀', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31bncjf8h0m005oro6om7rke7bfngsk0?imageView2/2/w/80/format/jpg', 'user_id': '6378362c000000001f01d1c7', 'nickname': '喵喵～是小苗呀'}, 'interact_info': {'shared_count': '0', 'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0'}, 'cover': {'height': 1932, 'width': 1179}, 'image_list': [{'height': 1932, 'width': 1179}], 'corner_tag_info': [{'type': 'publish_time', 'text': '9分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnqW3O3rizSIn7Pz8xh2mSJk='}, {'id': '69ea276a000000001f031803', 'model_type': 'note', 'note_card': {'interact_info': {'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '1', 'comment_count': '0', 'shared_count': '1'}, 'cover': {'height': 1660, 'width': 1242}, 'image_list': [{'height': 1660, 'width': 1242}, {'height': 1660, 'width': 1242}, {'height': 1660, 'width': 1242}], 'corner_tag_info': [{'text': '39分钟前', 'type': 'publish_time'}], 'type': 'normal', 'display_title': '', 'user': {'nick_name': '青岛百事通教育丨乐学', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/68f0b6c018ec0e0001999d1a.jpg?imageView2/2/w/80/format/jpg', 'user_id': '6826f4dc000000000d00a224', 'nickname': '青岛百事通教育丨乐学', 'xsec_token': 'ABNKIJkICBJP_3oZfJE_yzrVj4ivoaWliIcaCz3f7Bi-c='}}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnlBqL3jItQJ_FcejHH49GJM='}, {'id': '69ea2617000000001901e004', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '仰卧起坐平时47 8 9个体育中考前还要练么', 'user': {'nick_name': 'Ek🍁', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31qaqolv4n26g5ptoar33i7pabg1ion0?imageView2/2/w/80/format/jpg', 'user_id': '67b856c6000000000e011f2a', 'nickname': 'Ek🍁', 'xsec_token': 'ABfK6lNvkva9JgZwMDTDXFScG3OEYPjnri9rHJq_fWJd4='}, 'interact_info': {'liked_count': '1', 'collected': False, 'collected_count': '0', 'comment_count': '9', 'shared_count': '0', 'liked': False}, 'cover': {'height': 1600, 'width': 1200}, 'image_list': [{'width': 1200, 'height': 1600}], 'corner_tag_info': [{'type': 'publish_time', 'text': '45分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnmwTOkFkIr71I5PJZOE0MOs='}, {'id': '69ea25f90000000022026018', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '别自我感动了！26中考不是靠刷题能赢的', 'user': {'nick_name': '中大小咪', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31u3nebonia005q1f1d5jjt79h1fujfg?imageView2/2/w/80/format/jpg', 'user_id': '682f0b4b000000000e01f4e9', 'nickname': '中大小咪', 'xsec_token': 'ABZELkkKcYJ_f_vNQuKcPIcT4J747iSGmj4bQIQcqCFeA='}, 'interact_info': {'shared_count': '2', 'liked': False, 'liked_count': '1', 'collected': False, 'collected_count': '2', 'comment_count': '0'}, 'cover': {'height': 1660, 'width': 1242}, 'image_list': [{'height': 1660, 'width': 1242}, {'height': 1660, 'width': 1242}], 'corner_tag_info': [{'type': 'publish_time', 'text': '46分钟前'}]}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnhjkzY4_4mLuXtTrIDF8AI0='}, {'id': '38e307c0-4992-4a7c-a595-7a53283b5e0b#1776955590947', 'model_type': 'rec_query', 'rec_query': {'title': '相关搜索', 'source': 1, 'word_request_id': '38e307c0-4992-4a7c-a595-7a53283b5e0b#1776955590947', 'queries': [{'id': '中考崩溃期文案', 'name': '中考崩溃期文案', 'search_word': '中考崩溃期文案'}, {'id': '中考各科满分多少', 'name': '中考各科满分多少', 'search_word': '中考各科满分多少'}, {'id': '中考意味着什么', 'name': '中考意味着什么', 'search_word': '中考意味着什么'}, {'id': '中考很难吗', 'name': '中考很难吗', 'search_word': '中考很难吗'}]}, 'xsec_token': 'ABm8po3Ee8QfwCxClM29kz6suoo6VUMczz-hyYsYqhY5YHiP4yEfk_un13uBXXw5MoiHFyjgfpx4LBYAsLxupvxrEG0b9KJaIgewR5hTb62Ts='}, {'id': '69ea24930000000023014b6b', 'model_type': 'note', 'note_card': {'interact_info': {'liked_count': '1', 'collected': False, 'collected_count': '0', 'comment_count': '1', 'shared_count': '0', 'liked': False}, 'cover': {'height': 2560, 'width': 1476}, 'image_list': [{'height': 2560, 'width': 1476}, {'height': 1443, 'width': 1256}], 'corner_tag_info': [{'type': 'publish_time', 'text': '52分钟前'}], 'type': 'normal', 'display_title': '来自2019年的中考毕业生有话说', 'user': {'xsec_token': 'ABPb_qgPDHz36rqimubN-g64bVdUNkcVQeLiUYh_6woa8=', 'nick_name': 'momo', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo30ttr2fael0605ongsinlb3shbcp5540?imageView2/2/w/80/format/jpg', 'user_id': '62f0e4af0000000015018f91', 'nickname': 'momo'}}, 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnvAsqN_0iN5sQiRdaLkZIWo='}, {'id': '69e9918a000000002102f018', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '必背历史小论文，中考答题直接套用', 'user': {'xsec_token': 'ABljAeAeXtlAvi7bh3jadjyUNCNZ6PXvwMBCz2r174NLw=', 'nick_name': '梦梦老师爱分享-拔尖', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/fbbe1aea-1d7b-313f-9e52-a8de11bb68b8?imageView2/2/w/80/format/jpg', 'user_id': '691fc64000000000320154f0', 'nickname': '梦梦老师爱分享-拔尖'}, 'interact_info': {'liked': False, 'liked_count': '1', 'collected': False, 'collected_count': '0', 'comment_count': '1', 'shared_count': '0'}, 'cover': {'height': 2834, 'width': 2154}, 'image_list': [{'height': 2834, 'width': 2154}, {'height': 2834, 'width': 2154}, {'height': 2834, 'width': 2154}, {'width': 2154, 'height': 2834}, {'height': 2834, 'width': 2154}, {'height': 2834, 'width': 2154}, {'height': 2834, 'width': 2154}, {'height': 2834, 'width': 2154}], 'corner_tag_info': [{'type': 'publish_time', 'text': '26分钟前'}]}, 'xsec_token': 'ABdxuakkykQQRfchaFNorE1iNrt40WcnNF3_DowIkW_xw='}, {'id': '69e8caa1000000001a020158', 'model_type': 'note', 'note_card': {'display_title': '', 'user': {'xsec_token': 'AB8h4sr5tZ1PsurKF1wkggEl2soR5SKxEg2PWHtEcpH_0=', 'nick_name': '青岛乐妈升学择校', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo311ntqqvk0ekg5o1cuog09akcno8b098?imageView2/2/w/80/format/jpg', 'user_id': '602cf620000000000100aa8c', 'nickname': '青岛乐妈升学择校'}, 'interact_info': {'shared_count': '0', 'liked': False, 'liked_count': '0', 'collected': False, 'collected_count': '0', 'comment_count': '0'}, 'cover': {'height': 1660, 'width': 1242}, 'image_list': [{'height': 1660, 'width': 1242}, {'height': 1660, 'width': 1242}], 'corner_tag_info': [{'text': '27分钟前', 'type': 'publish_time'}], 'type': 'normal'}, 'xsec_token': 'ABmk4aAslOFz7CfZFRgbwGSw2D4eKbYLZTzNGTY_evYDM='}, {'id': '69e790540000000022025d43', 'model_type': 'note', 'note_card': {'type': 'normal', 'display_title': '南京市浦口区中考新政', 'user': {'nick_name': '初高物理张', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31us8fg69ig605nv9o4ogbnh0nl88nbo?imageView2/2/w/80/format/jpg', 'user_id': '5fe9c131000000000101de20', 'nickname': '初高物理张', 'xsec_token': 'AB-O-SlVPkMl7GmINZOREItqUCX08DjQVftwzcSk8i1tQ='}, 'interact_info': {'collected': False, 'collected_count': '1', 'comment_count': '12', 'shared_count': '5', 'liked': False, 'liked_count': '3'}, 'cover': {'height': 1600, 'width': 1200}, 'image_list': [{'height': 1600, 'width': 1200}], 'corner_tag_info': [{'type': 'publish_time', 'text': '1天前'}]}, 'xsec_token': 'ABLeb7HcP31mDZHFFx1h4uPE1dH87spBqMPZdDiO7dAb8='}, {'id': '69e723b70000000022025277', 'model_2026-04-23 22:46:31 MediaCrawler INFO (core.py:293) - [get_note_detail_async_task] Begin get note detail, note_id: 69ea301e0000000020007007
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea301e0000000020007007', 'type': 'normal', 'title': '镇江三中初三数学零模试卷。 #镇江数学中考[话题]#  #零模试卷[话题]# #2026中考[话题]#', 'desc': '镇江三中初三数学零模试卷。 #镇江数学中考[话题]#  #零模试卷[话题]# #2026中考[话题]#', 'video_url': '', 'time': 1776955422000, 'last_update_time': 1776955423000, 'user_id': '61dc552f000000001000cc52', 'nickname': '镇江数学化学于老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/61dc552f000000001000cc52.jpg', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '江苏', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/6d373b6a720229637e1b62a782d0c592/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/ee32239028e72726b2f3483a56254c05/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/4757f0a427f868a6b7cf619edc00542c/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/f8e1b74ff940cd53fefa2f2ba475ee64/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_dft_wgth_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/687e82f76878deee84b9c1aa726304df/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/563ec663216f53b4ae38e58d75e617f2/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/f17e75a5b9123d2e1119c4cb26c8cf1c/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/b9453a004bf41ca0b3025399b7c8920a/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_dft_wlteh_webp_3', 'tag_list': '镇江数学中考,零模试卷,2026中考', 'last_modify_ts': 1776955634540, 'note_url': 'https://www.xiaohongshu.com/explore/69ea301e0000000020007007?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnha0DPLYhDfWJxKneJvE_ZQ=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnha0DPLYhDfWJxKneJvE_ZQ='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea2efb000000001a0346aa', 'type': 'normal', 'title': '家有中考生', 'desc': '中考阶段，孩子需从起跑线抓起，建立学科信心。理科基础一旦落后难补，化学尤其重要，关系高一选科。初三第一次期中考试是关键，考得好能保持优势，考差了可能长期落后。#中考[话题]# #升学规划[话题]# #家长[话题]# #备战中考[话题]# #中考加油[话题]# #初中[话题]#', 'video_url': '', 'time': 1776955131000, 'last_update_time': 1776955131000, 'user_id': '5aee649011be1016a851ccfc', 'nickname': '夏天夏天', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/5aee649011be1016a851ccfc.jpg', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '安徽', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/16d6a0af13265489e9f1f30ff669642e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/36988ef6973738b29619c1534f36ae27/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_dft_wlteh_webp_3', 'tag_list': '中考,升学规划,家长,备战中考,中考加油,初中', 'last_modify_ts': 1776955634542, 'note_url': 'https://www.xiaohongshu.com/explore/69ea2efb000000001a0346aa?xsec_token=AB-Kw1pgh4a9ki1JHIdRngngMmJSjkeC3LDS8u1A1sPvM=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngngMmJSjkeC3LDS8u1A1sPvM='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea2e83000000001e00cef6', 'type': 'normal', 'title': '中考', 'desc': '#中考[话题]# #中考志愿填报[话题]# #报志愿[话题]# #职高[话题]# #公办中专[话题]# #公办[话题]# #小红书[话题]# #报考[话题]# #中专[话题]# #中职生[话题]#', 'video_url': '', 'time': 1776955011000, 'last_update_time': 1776955011000, 'user_id': '6378362c000000001f01d1c7', 'nickname': '喵喵～是小苗呀', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31bncjf8h0m005oro6om7rke7bfngsk0', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '山东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/90a8695ba42055092fe5f24fc0d81fb3/notes_pre_post/1040g3k831vacc61o2g705oro6om7rke7r13i8to!nd_dft_wlteh_webp_3', 'tag_list': '中考,中考志愿填报,报志愿,职高,公办中专,公办,小红书,报考,中专,中职生', 'last_modify_ts': 1776955634544, 'note_url': 'https://www.xiaohongshu.com/explore/69ea2e83000000001e00cef6?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnqW3O3rizSIn7Pz8xh2mSJk=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnqW3O3rizSIn7Pz8xh2mSJk='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea276a000000001f031803', 'type': 'normal', 'title': '会乐器的孩子青岛中考如何加分?\n#青岛转学[话题]# #青岛小学转学[话题]# #转学青岛[话题]# #美术中考[话题]# #春季招生[话题]# #音乐艺考[话题]# #艺术教育[话题]# #多元升学途径[话题]# #中考成绩[话题]#', 'desc': '会乐器的孩子青岛中考如何加分?\n#青岛转学[话题]# #青岛小学转学[话题]# #转学青岛[话题]# #美术中考[话题]# #春季招生[话题]# #音乐艺考[话题]# #艺术教育[话题]# #多元升学途径[话题]# #中考成绩[话题]#', 'video_url': '', 'time': 1776953194000, 'last_update_time': 1776953195000, 'user_id': '6826f4dc000000000d00a224', 'nickname': '青岛百事通教育丨乐学', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/68f0b6c018ec0e0001999d1a.jpg', 'liked_count': '', 'collected_count': '1', 'comment_count': '', 'share_count': '1', 'ip_location': '山东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/05ba7773309b3e551f87ed4e289f2736/spectrum/1040g0k031vabhc69jm005q16uje398h4vpaiqd0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/93173e854c19ef069eafc71afb2d7be9/spectrum/1040g0k031vabhg0jk0005q16uje398h4e1s5op8!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/6d1d3164fd7fc33431cee39e78f16610/spectrum/1040g0k031vabhg0jk00g5q16uje398h4350k978!nd_dft_wlteh_webp_3', 'tag_list': '青岛转学,青岛小学转学,转学青岛,美术中考,春季招生,音乐艺考,艺术教育,多元升学途径,中考成绩', 'last_modify_ts': 1776955634545, 'note_url': 'https://www.xiaohongshu.com/explore/69ea276a000000001f031803?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnlBqL3jItQJ_FcejHH49GJM=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnlBqL3jItQJ_FcejHH49GJM='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea2617000000001901e004', 'type': 'normal', 'title': '仰卧起坐平时47 8 9个体育中考前还要练么', 'desc': '#体育中考[话题]#', 'video_url': '', 'time': 1776952855000, 'last_update_time': 1776952893000, 'user_id': '67b856c6000000000e011f2a', 'nickname': 'Ek🍁', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31qaqolv4n26g5ptoar33i7pabg1ion0', 'liked_count': '1', 'collected_count': '', 'comment_count': '9', 'share_count': '', 'ip_location': '天津', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/03999d0d0b375bed3b997f6d42c076b8/1040g2sg31vabbbl640jg5ptoar33i7pag3d6dug!nd_dft_wlteh_webp_3', 'tag_list': '体育中考', 'last_modify_ts': 1776955634548, 'note_url': 'https://www.xiaohongshu.com/explore/69ea2617000000001901e004?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnmwTOkFkIr71I5PJZOE0MOs=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnmwTOkFkIr71I5PJZOE0MOs='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea25f90000000022026018', 'type': 'normal', 'title': '别自我感动了！26中考不是靠刷题能赢的', 'desc': '#学霸秘籍[话题]# #家长收藏孩子受益[话题]# #辣妈育儿经[话题]# #中考[话题]##升学规划[话题]# #学习 规划[话题]# #备战中考[话题]##中考复习[话题]##提高孩子学习成绩[话题]##家有初中生[话题]#', 'video_url': '', 'time': 1776952825000, 'last_update_time': 1776952825000, 'user_id': '682f0b4b000000000e01f4e9', 'nickname': '中大小咪', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31u3nebonia005q1f1d5jjt79h1fujfg', 'liked_count': '1', 'collected_count': '2', 'comment_count': '', 'share_count': '2', 'ip_location': '广东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/9f8c9ca295f769ce34618a3c4e1da37a/1040g00831vabb2hoiq005q1f1d5jjt79i2m3a18!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/5c50df5ae9f5bb023c6af80bea20c9bd/1040g00831vabb2hoiq0g5q1f1d5jjt79j0q5roo!nd_dft_wlteh_webp_3', 'tag_list': '学霸秘籍,家长收藏孩子受益,辣妈育儿经,中考,升学规划,学习规划,备战中考,中考复习,提高孩子学习成绩,家有初中生', 'last_modify_ts': 1776955634550, 'note_url': 'https://www.xiaohongshu.com/explore/69ea25f90000000022026018?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnhjkzY4_4mLuXtTrIDF8AI0=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnhjkzY4_4mLuXtTrIDF8AI0='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69ea24930000000023014b6b', 'type': 'normal', 'title': '来自2019年的中考毕业生有话说', 'desc': '刷到一条短视频说上海中考生。\n我就是上海中考考不上高中，最后去了中职校的一员。从中专，大专，最后专升本考到了本科，细看这一路，我花了6年时间。\n2019年的时候，中考满分还是630分，我考了491.5。当时中职校的班主任老师问我说怎么过了分数线没考上，老师并不了解中考，虽然划定的普高线是450，但我所在区的普高还是超了划定的分数线。郊区教育资源少，学生竞争也大。\n我现在回想初中四年，依然是我不想回去的四年。当时在班级里我就是一个处于成绩中下游、也没什么存在感的小透明，环境所致，自己的性格也很内向，同学的软性霸凌、老师的变相体罚我也一一承受。\n我早已离开了那个环境，现在想起那些时光，还是为自己感到难过、心疼。在那种环境里，我没了内在驱动力，所有的力气都用在了应付环境、忍受委屈、保护自己那颗小小的心。\n#上海中考[话题]# #上海三校生[话题]# #上海专升本[话题]# #上海学生[话题]#', 'video_url': '', 'time': 1776952467000, 'last_update_time': 1776952467000, 'user_id': '62f0e4af0000000015018f91', 'nickname': 'momo', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo30ttr2fael0605ongsinlb3shbcp5540', 'liked_count': '1', 'collected_count': '', 'comment_count': '1', 'share_count': '', 'ip_location': '上海', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/7e373f8245660216238830c3ed7c2206/1040g2sg31vaa0fmh3qkg5ongsinlb3shn5t6ch0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/adfb70e31ccde0b9b47316d91dab3efb/1040g2sg31vaa0fmh3qk05ongsinlb3sh42ncha0!nd_dft_wlteh_webp_3', 'tag_list': '上海中考,上海三校生,上海专升本,上海学生', 'last_modify_ts': 1776955634552, 'note_url': 'https://www.xiaohongshu.com/explore/69ea24930000000023014b6b?xsec_token=AB-Kw1pgh4a9ki1JHIdRngnvAsqN_0iN5sQiRdaLkZIWo=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnvAsqN_0iN5sQiRdaLkZIWo='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e9918a000000002102f018', 'type': 'normal', 'title': '必背历史小论文，中考答题直接套用', 'desc': '#历史论文[话题]# #中考历史怎样提分[话题]# #中考历史[话题]# #初中学习资料[话题]# #初中历史学习资料[话题]# #家长收藏孩子受益[话题]# #初中学习方法[话题]# #学霸养成[话题]# #学习规划[话题]#', 'video_url': '', 'time': 1776954002000, 'last_update_time': 1776914826000, 'user_id': '691fc64000000000320154f0', 'nickname': '梦梦老师爱分享-拔尖', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/fbbe1aea-1d7b-313f-9e52-a8de11bb68b8', 'liked_count': '1', 'collected_count': '', 'comment_count': '1', 'share_count': '', 'ip_location': '河南', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/6b0f86b544ae6665a94e41ec7c220339/spectrum/1040g0k031v9p7e72jm005q8vop0cil7ggvi6h4g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/9c6b3a27cdb571cc9145d701ecfec94e/spectrum/1040g0k031v9p7e72jm0g5q8vop0cil7g12rj27o!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/07562dff0e19e26c1823615de18666b1/spectrum/1040g0k031v9p7e72jm105q8vop0cil7grdc0vng!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/a5c526f5d6ad7b441fe677264a3cd817/spectrum/1040g0k031v9p7e72jm1g5q8vop0cil7g1qi8ado!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/9bfc372803a7dc371ce503a61e44d94f/spectrum/1040g0k031v9p7e72jm205q8vop0cil7g49m49l0!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/8417d8fe946b26f62dc5b11f1208bc06/spectrum/1040g0k031v9p7e72jm2g5q8vop0cil7g2ibtr8g!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/bde167ade59a7c94cbefb924433d8664/spectrum/1040g0k031v9p7e72jm305q8vop0cil7g5ob8i60!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/60b1f6d0be9f320275b27f0e15fb39bf/spectrum/1040g0k031v9p7e72jm3g5q8vop0cil7gvb20le0!nd_dft_wlteh_webp_3', 'tag_list': '历史论文,中考历史怎样提分,中考历史,初中学习资料,初中历史学习资料,家长收藏孩子受益,初中学习方法,学霸养成,学习规划', 'last_modify_ts': 1776955634554, 'note_url': 'https://www.xiaohongshu.com/explore/69e9918a000000002102f018?xsec_token=ABdxuakkykQQRfchaFNorE1iNrt40WcnNF3_DowIkW_xw=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'ABdxuakkykQQRfchaFNorE1iNrt40WcnNF3_DowIkW_xw='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e8caa1000000001a020158', 'type': 'normal', 'title': '2026年中考招生重要工作进程时间点\n#青岛转学[话题]# #青岛小学转学[话题]# #青岛学校[话题]# #中考志愿填报[话题]# #考试时间[话题]# #重要时间节点[话 题]# #公办中专[话题]# #中考[话题]#', 'desc': '2026年中考招生重要工作进程时间点\n#青岛转学[话题]# #青岛小学转学[话题]# #青岛学校[话题]# #中考志愿填报[话题]# #考试时间[话题]# #重要时间节点[话题]# #公办中专[话题]# #中考[话题]#', 'video_url': '', 'time': 1776953940000, 'last_update_time': 1776863906000, 'user_id': '602cf620000000000100aa8c', 'nickname': '青岛乐妈升学择校', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo311ntqqvk0ekg5o1cuog09akcno8b098', 'liked_count': '', 'collected_count': '', 'comment_count': '', 'share_count': '', 'ip_location': '山东', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/3c9dfbdb43886166c4ffa6e13010fd7d/spectrum/1040g34o31v90u2nqk02g5o1cuog09akcl2f0atg!nd_dft_wlteh_webp_3,http://sns-webpic-qc.xhscdn.com/202604232246/61c295a7b9bc001e65639775da1efe4c/spectrum/1040g34o31v90u2nqk0205o1cuog09akc3k5aim0!nd_dft_wlteh_webp_3', 'tag_list': '青岛转学,青岛小学转学,青岛 学校,中考志愿填报,考试时间,重要时间节点,公办中专,中考', 'last_modify_ts': 1776955634558, 'note_url': 'https://www.xiaohongshu.com/explore/69e8caa1000000001a020158?xsec_token=ABmk4aAslOFz7CfZFRgbwGSw2D4eKbYLZTzNGTY_evYDM=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'ABmk4aAslOFz7CfZFRgbwGSw2D4eKbYLZTzNGTY_evYDM='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:464) - [XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled
2026-04-23 22:47:14 MediaCrawler INFO (__init__.py:153) - [store.xhs.update_xhs_note] xhs note: {'note_id': '69e790540000000022025d43', 'type': 'normal', 'title': '南京市浦口区中考新政', 'desc': '重大利好，\n浦口区的家长笑醒了，中考志愿除了能报本区的高中，和六大之外\n也可以报市区（秦淮，建邺，鼓楼，玄武）所有的学校了✅✅✅\n江宁的家长羡慕了\n江宁的学生还是只能报江宁的高中和六大❌❌❌\n六大：一中，29中， 南师，金陵，中华，13中#中考物理[话题]# #南京中考[话题]#', 'video_url': '', 'time': 1776783444000, 'last_update_time': 1776783444000, 'user_id': '5fe9c131000000000101de20', 'nickname': '初高物理张', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31us8fg69ig605nv9o4ogbnh0nl88nbo', 'liked_count': '3', 'collected_count': '1', 'comment_count': '12', 'share_count': '5', 'ip_location': '江苏', 'image_list': 'http://sns-webpic-qc.xhscdn.com/202604232246/5f1b30f442c103f1403f7d12077e1f06/1040g00831v7qi6b02a605nv9o4ogbnh0rupmv3o!nd_dft_wlteh_webp_3', 'tag_list': '中考物理,南京中考', 'last_modify_ts': 1776955634562, 'note_url': 'https://www.xiaohongshu.com/explore/69e790540000000022025d43?xsec_token=ABLeb7HcP31mDZHFFx1h4uPE1dH87spBqMPZdDiO7dAb8=&xsec_source=pc_search', 'source_keyword': " '中考']", 'xsec_token': 'ABLeb7HcP31mDZHFFx1h4uPE1dH87spBqMPZdDiO7dAb8='}
2026-04-23 22:47:14 MediaCrawler INFO (core.py:178) - [XiaoHongShuCrawler.search] Note details: [{'title': '', 'desc': '镇江三中初三数学零模试卷。 #镇江数学中考[话题]#  #零模试卷[话题]# #2026中考[话题]#', 'interact_info': {'relation': 'none', 'liked': False, 'liked_count': '', 'collected': False, 'collected_count': '', 'comment_count': '', 'share_count': '', 'followed': False}, 'time': 1776955422000, 'last_update_time': 1776955423000, 'ip_location': '江苏', 'type': 'normal', 'user': {'user_id': '61dc552f000000001000cc52', 'nickname': '镇江数学化学于老师', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/61dc552f000000001000cc52.jpg', 'xsec_token': 'ABSKXWUfqooJ4SyIRROgXw94J6vtLM-YN5YS1oJJSsuSQ='}, 'image_list': [{'width': 1200, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/6d373b6a720229637e1b62a782d0c592/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_dft_wlteh_webp_3', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/805f7efa6a1d1a2df365db5a8f075bc8/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/6d373b6a720229637e1b62a782d0c592/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_dft_wlteh_webp_3'}], 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/6d373b6a720229637e1b62a782d0c592/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_dft_wlteh_webp_3', 'stream': {}, 'file_id': '', 'height': 1600, 'trace_id': '', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/805f7efa6a1d1a2df365db5a8f075bc8/1040g2sg31vacesauigjg5oesaknk1j2i5mugn3o!nd_prv_wlteh_webp_3', 'live_photo': False}, {'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/ee32239028e72726b2f3483a56254c05/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_dft_wgth_webp_3', 'live_photo': False, 'file_id': '', 'width': 3256, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/ee32239028e72726b2f3483a56254c05/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_dft_wgth_webp_3', 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/adcd5fdef515873e31d654b19036979b/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_prv_wgth_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/ee32239028e72726b2f3483a56254c05/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_dft_wgth_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/adcd5fdef515873e31d654b19036979b/1040g2sg31vacesauigeg5oesaknk1j2i5jerfeo!nd_prv_wgth_webp_3', 'stream': {}, 'height': 2436}, {'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/ddb2f6991b3c1e37c33c9fb9c4915110/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_prv_wgth_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/4757f0a427f868a6b7cf619edc00542c/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_dft_wgth_webp_3', 'live_photo': False, 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/ddb2f6991b3c1e37c33c9fb9c4915110/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_prv_wgth_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/4757f0a427f868a6b7cf619edc00542c/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_dft_wgth_webp_3'}], 'height': 2400, 'width': 3268, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/4757f0a427f868a6b7cf619edc00542c/1040g00831vacjpp5ia505oesaknk1j2inkc01d0!nd_dft_wgth_webp_3', 'trace_id': '', 'stream': {}, 'file_id': ''}, {'width': 3296, 'live_photo': False, 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/f8e1b74ff940cd53fefa2f2ba475ee64/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_dft_wgth_webp_3', 'stream': {}, 'file_id': '', 'height': 2436, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/f8e1b74ff940cd53fefa2f2ba475ee64/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_dft_wgth_webp_3', 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/3be373dad8a2ad8aa0371f464e002bf6/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_prv_wgth_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/f8e1b74ff940cd53fefa2f2ba475ee64/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_dft_wgth_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/3be373dad8a2ad8aa0371f464e002bf6/1040g00831vacjpp5ia605oesaknk1j2i66hbu90!nd_prv_wgth_webp_3'}, {'live_photo': False, 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/cc2941fe8c5b7aa5ca287213ca682091/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/687e82f76878deee84b9c1aa726304df/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_dft_wlteh_webp_3'}], 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/687e82f76878deee84b9c1aa726304df/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_dft_wlteh_webp_3', 'stream': {}, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/687e82f76878deee84b9c1aa726304df/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_dft_wlteh_webp_3', 'trace_id': '', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/cc2941fe8c5b7aa5ca287213ca682091/1040g00831vacjpp5ia6g5oesaknk1j2i3iv6350!nd_prv_wlteh_webp_3', 'file_id': '', 'height': 3448, 'width': 2324}, {'height': 3292, 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/1a0f22933d3d84452515cc7542c2a5c0/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/563ec663216f53b4ae38e58d75e617f2/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_dft_wlteh_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/1a0f22933d3d84452515cc7542c2a5c0/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_prv_wlteh_webp_3', 'live_photo': False, 'file_id': '', 'width': 2264, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/563ec663216f53b4ae38e58d75e617f2/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_dft_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/563ec663216f53b4ae38e58d75e617f2/1040g00831vacjpnd2g605oesaknk1j2ia44tb7o!nd_dft_wlteh_webp_3', 'stream': {}}, {'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/a6aa935ad91b6ceeb69faefee7a981eb/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_prv_wlteh_webp_3', 'height': 3476, 'width': 2324, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/f17e75a5b9123d2e1119c4cb26c8cf1c/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_dft_wlteh_webp_3', 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/a6aa935ad91b6ceeb69faefee7a981eb/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/f17e75a5b9123d2e1119c4cb26c8cf1c/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_dft_wlteh_webp_3'}], 'file_id': '', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/f17e75a5b9123d2e1119c4cb26c8cf1c/1040g2sg31vacesauige05oesaknk1j2iuftcg98!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False}, {'trace_id': '', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/db08d0a66f4f6734d05e81283923f461/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_prv_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/b9453a004bf41ca0b3025399b7c8920a/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_dft_wlteh_webp_3', 'stream': {}, 'file_id': '', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/b9453a004bf41ca0b3025399b7c8920a/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_dft_wlteh_webp_3', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/db08d0a66f4f6734d05e81283923f461/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/b9453a004bf41ca0b3025399b7c8920a/1040g2sg31vacesauigh05oesaknk1j2i239c14o!nd_dft_wlteh_webp_3'}], 'live_photo': False, 'height': 3420, 'width': 2360}], 'tag_list': [{'id': '680f4921000000001201b5c3', 'name': '镇江数学中考', 'type': 'topic'}, {'id': '650a4c4f000000000d01c781', 'name': '零模试卷', 'type': 'topic'}, {'id': '62f25e510000000001001633', 'name': '2026中考', 'type': 'topic'}], 'at_user_list': [], 'share_info': {'un_share': False}, 'note_id': '69ea301e0000000020007007', 'xsec_token': 'AB-Kw1pgh4a9ki1JHIdRngnha0DPLYhDfWJxKneJvE_ZQ=', 'xsec_source': None}, {'desc': '中考阶段，孩子需从起跑线抓起，建立学科信心。理科基础一旦落后难补，化学尤其重要，关系高 一选科。初三第一次期中考试是关键，考得好能保持优势，考差了可能长期落后。#中考[话题]# #升学规划[话题]# #家长[话题]# #备战中考[话题]# #中考加油[话题]# #初中[话题]#', 'image_list': [{'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/cde44cdf1fbcc48c9ee0b2a355f9f52e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/16d6a0af13265489e9f1f30ff669642e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_dft_wlteh_webp_3'}], 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/16d6a0af13265489e9f1f30ff669642e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False, 'file_id': '', 'height': 2400, 'width': 1440, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/16d6a0af13265489e9f1f30ff669642e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_dft_wlteh_webp_3', 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/cde44cdf1fbcc48c9ee0b2a355f9f52e/1040g2sg31vaceci52qdg4a536ri91j7s9jedflo!nd_prv_wlteh_webp_3'}, {'height': 2400, 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/36988ef6973738b29619c1534f36ae27/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_dft_wlteh_webp_3', 'stream': {}, 'live_photo': False, 'file_id': '', 'width': 1440, 'trace_id': '', 'info_list': [{'image_scene': 'WB_PRV', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/97ba8d0848c2af01351767176b81a46c/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_prv_wlteh_webp_3'}, {'image_scene': 'WB_DFT', 'url': 'http://sns-webpic-qc.xhscdn.com/202604232246/36988ef6973738b29619c1534f36ae27/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_dft_wlteh_webp_3'}], 'url_pre': 'http://sns-webpic-qc.xhscdn.com/202604232246/97ba8d0848c2af01351767176b81a46c/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_prv_wlteh_webp_3', 'url_default': 'http://sns-webpic-qc.xhscdn.com/202604232246/36988ef6973738b29619c1534f36ae27/1040g2sg31vaceci52qd04a536ri91j7svcvsd3o!nd_dft_wlteh_webp_3'}], 'at_user_list': [], 'time': 1776955131000, 'share_info': {'un_share': False}, 'note_id': '69ea2efb000000001a0346aa', 'type': 'normal', 'title': '家有中考生', 'last_update_time': 1776955131000, 'ip_location': '安徽', 'user': {'user_id': '5aee649011be1016a851ccfc', 'nickname': '夏天夏天', 'avatar': 'https://sns-avatar-qc.xhscdn.com/avatar/5aee649011be1016a2026-04-23 22:47:14 MediaCrawler INFO (core.py:328) - [XiaoHongShuCrawler.batch_get_note_comments] Crawling comment mode is not enabled
2026-04-23 22:47:16 MediaCrawler INFO (core.py:183) - [XiaoHongShuCrawler.search] Sleeping for 2 seconds after page 1
2026-04-23 22:47:16 MediaCrawler INFO (core.py:127) - [XiaoHongShuCrawler.start] Xhs Crawler finished ...
2026-04-23 22:47:16 MediaCrawler INFO (cdp_browser.py:463) - [CDPBrowserManager] Browser connection disconnected
2026-04-23 22:47:16 MediaCrawler INFO (browser_launcher.py:255) - [BrowserLauncher] Closing browser process...
2026-04-23 22:47:16 MediaCrawler INFO (browser_launcher.py:287) - [BrowserLauncher] Browser process closed
2026-04-23 22:47:17 | INFO     | 使用数据文件: search_contents_2026-04-23_22-47-14.jsonl
2026-04-23 22:47:17 | INFO     | 成功转换 10 条小红书数据
2026-04-23 22:47:17 | INFO     | ✅ 小红书采集完成，共 10 条内容
2026-04-23 22:47:17 | INFO     | xiaohongshu 采集到 10 条内容
2026-04-23 22:47:17 | WARNING  | 采集数量不足: 当前18条，目标30条
2026-04-23 22:47:17 | INFO     | 总计采集到 18 条唯一内容
2026-04-23 22:47:17 | INFO     | 采集完成，共获取 18 条热点内容
2026-04-23 22:47:17 | INFO     | 
采集内容预览（前5条）:
2026-04-23 22:47:17 | INFO     |   1. [微信公众号] 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开展英语中考备考教研
2026-04-23 22:47:17 | INFO     |   2. [微信公众号] 26中考化学新趋势跨学科专项训练14题有答案
2026-04-23 22:47:17 | INFO     |   3. [微信公众号] 中考化学131个“题眼”,吃透考试稳了 #必考考点 #家长收藏孩子受益 #初中化学知识点 #初中物理
2026-04-23 22:47:17 | INFO     |   4. [微信公众号] 2026常熟中考零模数学+英语试卷+答案(2026.4.22)
2026-04-23 22:47:17 | INFO     |   5. [微信公众号] 中考道法·答题方法:做法类、措施类这么答,比别人多拿几分(含常考角度模板)
2026-04-23 22:47:17 | INFO     | 
第二步：合并多源数据为统一JSON文件...
2026-04-23 22:47:17 | INFO     | ============================================================
2026-04-23 22:47:17 | INFO     | 开始合并多源数据
2026-04-23 22:47:17 | INFO     | ============================================================
2026-04-23 22:47:17 | INFO     | 总数据量: 18 条
2026-04-23 22:47:17 | INFO     | 数据来源统计:
2026-04-23 22:47:17 | INFO     |   - 微信公众号: 8 条
2026-04-23 22:47:17 | INFO     |   - xiaohongshu: 10 条
2026-04-23 22:47:17 | INFO     | ✅ 数据合并完成
2026-04-23 22:47:17 | INFO     | 📄 合并文件: merged_data\merged_hotspots_20260423_224717.json
2026-04-23 22:47:17 | INFO     | 📋 包含字段: title, source, author, publish_time, content_summary, url, popularity, cover_image, image_list, tags, score, score_details
2026-04-23 22:47:17 | INFO     | ============================================================
2026-04-23 22:47:17 | INFO     | 合并文件已生成: merged_data\merged_hotspots_20260423_224717.json
2026-04-23 22:47:17 | INFO     | 
第三步：开始对内容进行智能打分...
2026-04-23 22:47:17 | INFO     | 开始对 18 条内容进行打分...
2026-04-23 22:47:54 | INFO     | 第1条评分成功: 6.65 | 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开
2026-04-23 22:47:54 | INFO     | 第2条评分成功: 7.15 | 26中考化学新趋势跨学科专项训练14题有答案
2026-04-23 22:47:54 | INFO     | 第3条评分成功: 6.95 | 中考化学131个“题眼”,吃透考试稳了 #必考考点 #家长收
2026-04-23 22:47:54 | INFO     | 第4条评分成功: 8.0 | 2026常熟中考零模数学+英语试卷+答案(2026.4.22
2026-04-23 22:47:54 | INFO     | 第5条评分成功: 7.35 | 中考道法·答题方法:做法类、措施类这么答,比别人多拿几分(含
2026-04-23 22:47:54 | INFO     | 已完成第 1 批打分
2026-04-23 22:48:34 | INFO     | 第1条评分成功: 6.15 | 中考语文考前必背知识清单,想拿高分背这一份就够了!
2026-04-23 22:48:34 | INFO     | 第2条评分成功: 6.2 | 中考英语核心考点:名词复数
2026-04-23 22:48:34 | INFO     | 第3条评分成功: 7.0 | 中考550分左右,选普高还是职校?
2026-04-23 22:48:34 | INFO     | 第4条评分成功: 5.1 | 镇江三中初三数学零模试卷。 #镇江数学中考[话题]#  #零
2026-04-23 22:48:34 | INFO     | 第5条评分成功: 5.8 | 家有中考生
2026-04-23 22:48:34 | INFO     | 已完成第 2 批打分
2026-04-23 22:49:10 | INFO     | 第1条评分成功: 3.95 | 中考
2026-04-23 22:49:10 | INFO     | 第2条评分成功: 4.65 | 会乐器的孩子青岛中考如何加分?
#青岛转学[话题]# #青岛
2026-04-23 22:49:10 | INFO     | 第3条评分成功: 3.35 | 仰卧起坐平时47 8 9个体育中考前还要练么
2026-04-23 22:49:10 | INFO     | 第4条评分成功: 5.0 | 别自我感动了！26中考不是靠刷题能赢的
2026-04-23 22:49:10 | INFO     | 第5条评分成功: 5.15 | 来自2019年的中考毕业生有话说
2026-04-23 22:49:10 | INFO     | 已完成第 3 批打分
2026-04-23 22:49:35 | INFO     | 第1条评分成功: 3.4 | 必背历史小论文，中考答题直接套用
2026-04-23 22:49:35 | INFO     | 第2条评分成功: 5.55 | 2026年中考招生重要工作进程时间点
#青岛转学[话题]# 
2026-04-23 22:49:35 | INFO     | 第3条评分成功: 5.95 | 南京市浦口区中考新政
2026-04-23 22:49:35 | INFO     | 已完成第 4 批打分
2026-04-23 22:49:35 | INFO     | 打分完成，共 18 条内容
2026-04-23 22:49:35 | INFO     | 打分完成，所有内容已评分
2026-04-23 22:49:35 | INFO     | 
评分概览（前5条）:
2026-04-23 22:49:35 | INFO     |   1. 评分: 6.65 | 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开展英语中考备考教研
2026-04-23 22:49:35 | INFO     |   2. 评分: 7.15 | 26中考化学新趋势跨学科专项训练14题有答案
2026-04-23 22:49:35 | INFO     |   3. 评分: 6.95 | 中考化学131个“题眼”,吃透考试稳了 #必考考点 #家长收藏孩子受益 #初中化
2026-04-23 22:49:35 | INFO     |   4. 评分: 8.00 | 2026常熟中考零模数学+英语试卷+答案(2026.4.22)
2026-04-23 22:49:35 | INFO     |   5. 评分: 7.35 | 中考道法·答题方法:做法类、措施类这么答,比别人多拿几分(含常考角度模板)
2026-04-23 22:49:35 | INFO     | 
第四步：保存打分后的数据到 scored_data...
2026-04-23 22:49:35 | INFO     | ============================================================
2026-04-23 22:49:35 | INFO     | 开始合并多源数据
2026-04-23 22:49:35 | INFO     | ============================================================
2026-04-23 22:49:35 | INFO     | 总数据量: 18 条
2026-04-23 22:49:35 | INFO     | 数据来源统计:
2026-04-23 22:49:35 | INFO     |   - 微信公众号: 8 条
2026-04-23 22:49:35 | INFO     |   - xiaohongshu: 10 条
2026-04-23 22:49:35 | INFO     | ✅ 数据合并完成
2026-04-23 22:49:35 | INFO     | 📄 合并文件: scored_data\merged_hotspots_20260423_224935.json
2026-04-23 22:49:35 | INFO     | 📋 包含字段: title, source, author, publish_time, content_summary, url, popularity, cover_image, image_list, tags, score, score_details
2026-04-23 22:49:35 | INFO     | ============================================================
2026-04-23 22:49:35 | INFO     | ✅ 打分数据已保存: scored_data\merged_hotspots_20260423_224935.json
2026-04-23 22:49:35 | INFO     | 
第五步：筛选前 10 条高分内容...
2026-04-23 22:49:35 | INFO     | 已选取前 10 条高分内容，最高分: 8.00
2026-04-23 22:49:35 | INFO     | 筛选完成，最终选取 10 条优质内容
2026-04-23 22:49:35 | INFO     | 
最终入选热点（按评分排序）:
2026-04-23 22:49:35 | INFO     |   1. 8.0分 | 2026常熟中考零模数学+英语试卷+答案(2026.4.22)
2026-04-23 22:49:35 | INFO     |   2. 7.3分 | 中考道法·答题方法:做法类、措施类这么答,比别人多拿几分(含常考角度模板)
2026-04-23 22:49:35 | INFO     |   3. 7.2分 | 26中考化学新趋势跨学科专项训练14题有答案
2026-04-23 22:49:35 | INFO     |   4. 7.0分 | 中考550分左右,选普高还是职校?
2026-04-23 22:49:35 | INFO     |   5. 7.0分 | 中考化学131个“题眼”,吃透考试稳了 #必考考点 #家长收藏孩子受益 #初中化学知识点 #初中物理
2026-04-23 22:49:35 | INFO     |   6. 6.7分 | 研思并行促提升,中考备考共前行 ——李观清工作室赴吴川四中开展英语中考备考教研
2026-04-23 22:49:35 | INFO     |   7. 6.2分 | 中考英语核心考点:名词复数
2026-04-23 22:49:35 | INFO     |   8. 6.2分 | 中考语文考前必背知识清单,想拿高分背这一份就够了!
2026-04-23 22:49:35 | INFO     |   9. 6.0分 | 南京市浦口区中考新政
2026-04-23 22:49:35 | INFO     |   10. 5.8分 | 家有中考生
2026-04-23 22:49:35 | INFO     | 
第六步：生成 Markdown 日报...
2026-04-23 22:49:35 | INFO     | 正在生成日报: 教育热点日报_20260423.md
2026-04-23 22:49:35 | INFO     | 日报已保存至: output\教育热点日报_20260423.md
2026-04-23 22:49:35 | INFO     | 日报生成成功！
2026-04-23 22:49:35 | INFO     | 文件位置: output\教育热点日报_20260423.md
2026-04-23 22:49:35 | INFO     | 
============================================================
2026-04-23 22:49:35 | INFO     | 教育热点搜集任务全部完成！
2026-04-23 22:49:35 | INFO     | ============================================================
2026-04-23 22:49:35 | INFO     | 
今日成果:
2026-04-23 22:49:35 | INFO     |    - 采集内容: 18 条
2026-04-23 22:49:35 | INFO     |    - 合并文件: merged_data\merged_hotspots_20260423_224717.json
2026-04-23 22:49:35 | INFO     |    - 打分数据: scored_data\merged_hotspots_20260423_224935.json
2026-04-23 22:49:35 | INFO     |    - 最终入选: 10 条
2026-04-23 22:49:35 | INFO     |    - 输出文件: output\教育热点日报_20260423.md
2026-04-23 22:49:35 | INFO     |    - 最高评分: 8.00
2026-04-23 22:49:35 | INFO     |    - 日志文件: ./logs/agent.log
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
| `KEYWORDS` | 搜索关键词列表 | `["学习方法", "考研"]` |
| `TIME_RANGE_MIN` | 最小时间范围(小时) | 0 |
| `TIME_RANGE_MAX` | 最大时间范围(小时) | 24 |
| `ENABLED_SOURCES` | 启用的数据源 | `["zhihu"]` |
| `SCHEDULE_TIME` | 定时执行时间 | `"08:00"` |
| `LOG_LEVEL` | 日志级别 | `"INFO"` |
| `LOG_FILE` | 日志文件路径 | `"./logs/agent.log"` |

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

---

### 🤖 AI 打分 API 调用示例

系统使用 OpenAI 兼容的 API 格式，批量对内容进行智能评分。以下是完整的请求和响应示例：

#### 1️⃣ 请求消息 (Request)

**API 配置**:
```python
model = "gpt-5.4"
temperature = 0.3
max_tokens = 2000
```

**System Message**:
```json
{
  "role": "system",
  "content": "你是专业的教育内容评估专家，擅长判断教育资讯的价值和质量。"
}
```

**User Message (Prompt)**:
```
你是一位教育领域的内容评估专家，请对以下教育热点内容进行综合评分。

评分维度（每项1-10分）：
1. 热度：内容的关注度和传播度
2. 权威性：信息来源的可靠性和专业性
3. 内容质量：信息的完整性、准确性和深度
4. 家长实用性：对家长群体的实用价值和参考意义
5. 信息时效性：内容的新鲜程度和及时性

综合评分 = (热度×0.2 + 权威性×0.25 + 内容质量×0.25 + 家长实用性×0.2 + 时效性×0.1)

请严格按照以下JSON格式返回评分结果（只返回JSON，不要其他文字）：
{
  "scores": [
    {
      "item_index": 1,
      "heat": 8.5,
      "authority": 9.0,
      "quality": 8.0,
      "practicality": 9.5,
      "timeliness": 8.0,
      "overall": 8.65,
      "reason": "简要说明评分理由"
    }
  ]
}

需要评分的内容：

第1条内容:
- 标题: 22考研数学一143分经验贴(针对27考研进行了更新)
- 来源: zhihu
- 发布时间: 2022-04-01 06:39
- 摘要: 27邂逅遗憾考研数学交流q群：1079402290（已满），2群：398227280写在最最开头：为了感谢大家对邂逅遗憾经验贴的支持与认可，此经验贴每年都会进行若干次更新。同时，为了感谢各位对我的支持，知乎的每一条评论，我都会尽可能地回复！此外，我于2026.1.17发表了新帖，万字长文，同样全程干货...
- 热度指标: 19774.0

第2条内容:
- 标题: 考研英语复习规划指南
- 来源: zhihu
- 发布时间: 2026-03-15 10:20
- 摘要: 考研英语复习需要系统性规划，从基础阶段到强化阶段再到冲刺阶段，每个阶段都有不同的重点任务。基础阶段重点背单词和学习语法，强化阶段重点做真题和专项训练，冲刺阶段重点模拟考试和查漏补缺...
- 热度指标: 8523.0

第3条内容:
- 标题: 家庭教育中的沟通技巧
- 来源: wechat
- 发布时间: 2026-04-20 14:30
- 摘要: 良好的亲子沟通是家庭教育的基础。本文介绍了5个实用的沟通技巧：1.倾听孩子的想法 2.尊重孩子的感受 3.使用积极的语言 4.设定合理的期望 5.创造轻松的沟通氛围...
- 热度指标: 12456.0

请开始评分：
```

#### 2️⃣ 响应消息 (Response)

**大模型返回的 JSON**:
```json
{
  "scores": [
    {
      "item_index": 1,
      "heat": 7.8,
      "authority": 5.5,
      "quality": 7.9,
      "practicality": 8.6,
      "timeliness": 6.5,
      "overall": 7.25,
      "reason": "内容质量较高，经验分享详细具体，但发布时间较早，时效性一般"
    },
    {
      "item_index": 2,
      "heat": 6.5,
      "authority": 7.0,
      "quality": 8.2,
      "practicality": 9.0,
      "timeliness": 8.5,
      "overall": 7.68,
      "reason": "系统性强，实用价值高，时效性好，适合当前备考学生参考"
    },
    {
      "item_index": 3,
      "heat": 8.2,
      "authority": 8.5,
      "quality": 8.8,
      "practicality": 9.5,
      "timeliness": 9.0,
      "overall": 8.71,
      "reason": "内容权威实用，贴近家长需求，发布及时，具有很强的参考价值"
    }
  ]
}
```

#### 3️⃣ 解析后的结果

系统将大模型返回的 JSON 解析并赋值给对应的 `EducationHotspot` 对象：

```python
# 第1条内容 - 考研数学经验贴
hotspot_1.score = 7.25
hotspot_1.score_details = {
    "heat": 7.8,           # 热度：较高（19774点赞）
    "authority": 5.5,      # 权威性：一般（个人经验分享）
    "quality": 7.9,        # 内容质量：较好（内容详实）
    "practicality": 8.6,   # 实用性：很高（对考生有指导意义）
    "timeliness": 6.5      # 时效性：一般（2022年发布）
}

# 第2条内容 - 英语复习指南
hotspot_2.score = 7.68
hotspot_2.score_details = {
    "heat": 6.5,
    "authority": 7.0,
    "quality": 8.2,
    "practicality": 9.0,
    "timeliness": 8.5
}

# 第3条内容 - 家庭教育沟通技巧
hotspot_3.score = 8.71
hotspot_3.score_details = {
    "heat": 8.2,
    "authority": 8.5,
    "quality": 8.8,
    "practicality": 9.5,
    "timeliness": 9.0
}
```

#### 4️⃣ 关键技术点

**批量处理**:
- 每批次处理 5 条内容（可配置 `batch_size`）
- 避免单次请求过长导致超时
- 失败批次自动重试并赋予默认分数

**JSON 解析容错**:
```python
# 1. 尝试直接解析
data = json.loads(result_text)

# 2. 如果失败，尝试从文本中提取 JSON
import re
json_pattern = r'\{[\s\S]*\}'
match = re.search(json_pattern, result_text)
if match:
    json_str = match.group()
    data = json.loads(json_str)

# 3. 转换为 item_X 格式字典
scores_dict = {}
for item in data.get("scores", []):
    index = item.get("item_index", 0)
    key = f"item_{index}"
    scores_dict[key] = item
```

**异常处理**:
- API 调用失败：赋予默认分数 5.0
- JSON 解析失败：记录警告日志，使用默认分数
- 单条数据缺失：不影响其他数据评分


### 日志查看

实时查看日志：
```bash
tail -f logs/agent.log
```

---

**最后更新**: 2026-04-23  
**版本**: v1.0.0


## ✨ 核心功能

- **多源数据采集**: 支持微信公众号、知乎、小红书等多个平台
- **智能去重**: 基于标题和URL的自动化去重机制
- **AI智能评分**: 使用大模型对内容进行多维度综合评分
- **Top N筛选**: 自动筛选高分优质内容
- **Markdown报告**: 生成格式精美、家长友好的日报文档
- **定时调度**: 支持每日自动执行，持续监控教育热点
