# 搜索源扩展执行记录

日期：2026-05-10

分支：`codex/search-source-expansion`

计划来源：

- `docs/superpowers/specs/2026-05-10-search-source-expansion-design.md`
- `docs/superpowers/plans/2026-05-10-search-source-expansion.md`

执行范围：

- 扩展 `wechat`、`wechat_mp`、`xiaohongshu`、`zhihu`、`google_news` 五类搜索源。
- 小红书和知乎支持关键词搜索与明确账号主页 URL 采集。
- 通用关键词搜索第一版使用 Google News。
- `TrendCrawlerRuntime` 第一阶段改为支持外置路径，不删除当前内嵌目录。

注意事项：

- 当前工作区已有与本任务无关的修改，执行时不回滚不相关文件。
- 当前 `TrendCrawlerRuntime` 仍保留在仓库中，对外发布前的历史清理作为独立步骤处理。

验证结果：

- `python -m pytest tests/test_app_config.py tests/test_settings.py -q`：通过，10 passed。
- `python -m pytest tests/test_google_news_crawler.py -q`：通过，2 passed。
- `python -m pytest tests/test_xiaohongshu_crawler_modes.py -q`：通过，1 passed。
- `python -m pytest tests/test_zhihu_crawler_modes.py tests/test_trendcrawler_arg_zhihu_creator.py -q`：通过，2 passed。
- `python -m pytest tests/test_bootstrap.py -q`：通过，7 passed。
- `python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_bootstrap.py tests/test_google_news_crawler.py tests/test_xiaohongshu_crawler_modes.py tests/test_zhihu_crawler_modes.py tests/test_trendcrawler_arg_zhihu_creator.py -q`：通过，22 passed。
- `python -m pytest tests/test_app_config.py tests/test_settings.py tests/test_wechat_mp_browser_mode.py tests/test_bootstrap.py -q`：通过，20 passed。
- `python scripts/bootstrap.py --check`：通过；提示当前 Python 环境在 `/Users/neo/anaconda3`，不是项目 `.venv`。
- `python -m pytest -q`：通过，35 passed。为避免根项目收集第三方 `TrendCrawlerRuntime` 自带测试，已新增 `pytest.ini` 限定 `testpaths = tests`。
- `AI_TREND_CONFIG=config.yaml.example python scripts/bootstrap.py --check`：通过；示例配置会创建 `third_party/TrendCrawlerRuntime` 运行目录，并在未 place compatible TrendCrawlerRuntime 时提示 requirements 缺失和首次运行需要登录。
- 当前 Anaconda 环境尚未安装 `gnews`，但 `requirements.txt` 已声明 `gnews>=0.4.1,<1`；正式运行前执行 `python scripts/bootstrap.py` 会安装根项目依赖。
- 复查时修正了 `scripts/bootstrap.py` 的登录态判断：不再把刚创建的空 `TrendCrawlerRuntime/browser_data` 目录误报为已有登录态。

真实抓取验证：

- `python scripts/bootstrap.py`：完成依赖安装和运行目录检查；提示当前使用的是 `/Users/neo/anaconda3`，不是项目 `.venv`。
- `python -u scripts/search_wechat.py -k 教育改革,中考`：通过，产物 `merged_data/merged_hotspots_20260510_122659.json`，8 条。
- `python -u scripts/search_google_news.py -k 教育改革,中考`：通过，产物 `merged_data/merged_hotspots_20260510_122645.json`，3 条。
- `python -u scripts/search_zhihu.py`：通过，知乎登录态正常，产物 `merged_data/merged_hotspots_20260510_122724.json`，17 条。
- `python -u scripts/search_xiaohongshu.py`：通过，小红书登录态正常，产物 `merged_data/merged_hotspots_20260510_122917.json`，20 条。
- `python -u scripts/search_wechat_mp.py`：验证到前 3 个公众号均能正常采集，用户确认公众号账号链路不用继续测试后停止。

真实运行中修复：

- Google News 的 `gnews.GNews.get_news()` 内部跳转请求无超时，真实运行会卡住；改为直接读取 Google News RSS，并默认保留 RSS 链接，不再同步解析原始站点链接。
- 根项目直接 import `feedparser`，已在 `requirements.txt` 显式声明。
- TrendCrawlerRuntime 依赖安装把当前 Anaconda 环境的 NumPy 推到 2.x，触发 pandas 可选二进制包 `_ARRAY_API` 报错；已约束 `numpy>=1.26,<2`，并把 TrendCrawlerRuntime 的 `opencv-python` 约束到 `<4.12`。
- 小红书和知乎原始日志会输出整段搜索响应、正文和图片列表；已改为摘要日志，避免长跑时日志爆炸。
