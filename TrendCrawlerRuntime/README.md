# TrendCrawlerRuntime

TrendCrawlerRuntime 是 AITrend 内部使用的多平台内容采集运行时。

## 定位

- 给 AITrend 的小红书、知乎等来源提供登录、搜索、账号内容采集和本地 JSONL 落盘能力。
- 默认由 AITrend 外层 wrapper 调用，不建议业务代码直接绕过 AITrend 使用。
- 当前目录是私有自用运行时，不作为独立开源项目发布。

## 常用入口

```bash
python main.py --platform xhs --lt qrcode --type search --keywords 教育改革
python main.py --platform xhs --lt qrcode --type creator --creator_id 'https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=TOKEN&xsec_source=pc_search'
python main.py --platform zhihu --lt qrcode --type creator --creator_id 'https://www.zhihu.com/people/URL_TOKEN'
```

## 运行态目录

- `browser_data/`：浏览器登录态。
- `data/`：采集输出，AITrend 会读取其中的 JSONL 文件。

## 注意

请控制请求频率，只采集业务需要的少量公开内容。
