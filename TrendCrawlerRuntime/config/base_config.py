# -*- coding: utf-8 -*-
# Copyright (c) 2025 runtime-maintainer@example.local
#
# This file is part of TrendCrawlerRuntime project.
# Repository: https://internal.local/TrendCrawlerRuntime/blob/main/config/base_config.py
# GitHub: https://internal.local
# Licensed under PRIVATE INTERNAL USE NOTICE 1.1
#

import os

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# ==================== 基础配置 ====================
# 爬取平台，可选值：xhs（小红书）| dy（抖音）| ks（快手）| bili（B站）| wb（微博）| tieba（贴吧）| zhihu（知乎）
PLATFORM = "xhs"

# 是否使用海外版小红书 (rednote.com)
# 开启后 API 走 webapi.rednote.com，cookie 域使用 .rednote.com
XHS_INTERNATIONAL = False

# 关键词搜索配置，多个关键词用英文逗号分隔
# 优先从环境变量读取，支持外部配置
_keywords_env = os.getenv("TREND_CRAWLER_RUNTIME_KEYWORDS", "")
if _keywords_env:
    KEYWORDS = ",".join(k.strip() for k in _keywords_env.split(",") if k.strip())
else:
    KEYWORDS = "教育"

# 登录类型，可选值：qrcode（二维码登录）| phone（手机号登录）| cookie（使用已有cookie）
LOGIN_TYPE = "qrcode"
# Cookie 字符串，当 LOGIN_TYPE 设置为 "cookie" 时需要填写
COOKIES = ""

# 爬取类型，可选值：search（关键词搜索）| detail（帖子详情）| creator（创作者主页数据）
CRAWLER_TYPE = "search"


# ==================== 代理 配置 ====================
# 是否启用 IP 代理
ENABLE_IP_PROXY = False

# 代理 IP 池数量
IP_PROXY_POOL_COUNT = 2

# 代理 IP 提供商名称，可选值：kuaidaili（快代理）| wandouhttp（豌豆HTTP）
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# 浏览器配置
# 设置为 True 将不打开浏览器（无头模式）
# 设置为 False 将打开浏览器（可见模式）
# 如果小红书一直扫码登录但失败，可以打开浏览器手动通过滑动验证码
# 如果抖音一直提示失败，可以打开浏览器查看扫码登录后是否出现手机验证，如有则手动通过后重试
HEADLESS = False

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# ==================== CDP (Chrome DevTools Protocol) 配置 ====================
# 是否启用 CDP 模式 - 使用用户本地的 Chrome/Edge 浏览器进行爬取，具有更好的反检测能力
# 开启后，会自动检测并启动用户的 Chrome/Edge 浏览器，通过 CDP 协议进行控制
# 该方式使用真实浏览器环境，包括用户的扩展、Cookie 和设置，大幅降低被风控检测的风险
ENABLE_CDP_MODE = True

# CDP 调试端口，用于与浏览器通信
# 如果端口被占用，系统会自动尝试下一个可用端口
CDP_DEBUG_PORT = 9222

# 自定义浏览器路径（可选）
# 如果为空，系统会自动检测 Chrome/Edge 的安装路径
# Windows 示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS 示例: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = ""

# 是否在 CDP 模式下启用无头模式
# 注意：即使设置为 True，某些反检测功能在无头模式下可能无法正常工作
CDP_HEADLESS = False

# 浏览器启动超时时间（秒）
BROWSER_LAUNCH_TIMEOUT = 60

# 是否连接用户已打开的浏览器，而不是启动新的浏览器
# 开启后，程序会连接一个已经启用了远程调试的浏览器
# 用户需要在 Chrome 中开启远程调试：chrome://inspect/#remote-debugging
# 或者使用命令行参数启动 Chrome：--remote-debugging-port=9222
# 这种方式反检测效果最好，因为直接使用用户真实浏览器的所有 Cookie、扩展和浏览历史
# 设置为 False 让程序自动启动新浏览器，无需手动允许远程调试
CDP_CONNECT_EXISTING = False

# 程序结束时是否自动关闭浏览器
# 设置为 False 可以保持浏览器运行，方便调试
AUTO_CLOSE_BROWSER = True

# ==================== 数据存储配置 ====================
# 数据保存类型选项配置，支持：csv、db、json、jsonl、sqlite、excel、postgres
# 建议保存到数据库，具有去重功能
SAVE_DATA_OPTION = "jsonl"

# 数据保存路径，如未指定默认保存到 data 文件夹
SAVE_DATA_PATH = ""

# 浏览器用户数据目录配置，%s 会被替换为平台名称
USER_DATA_DIR = "%s_user_data_dir"

# ==================== 爬取控制配置 ====================
# 开始爬取的起始页码，默认从第1页开始
START_PAGE = 1

# 控制爬取的视频/帖子数量
# 优先从环境变量读取，支持外部配置
_crawler_max_notes_env = os.getenv("TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT", "")
if _crawler_max_notes_env:
    try:
        CRAWLER_MAX_NOTES_COUNT = int(_crawler_max_notes_env)
    except ValueError:
        CRAWLER_MAX_NOTES_COUNT = 15
else:
    CRAWLER_MAX_NOTES_COUNT = 15

# 是否启用时间过滤（仅对小红书有效）
ENABLE_TIME_FILTER = True
# 时间过滤范围（小时），只爬取距今指定小时内的内容
# 优先从环境变量读取，支持外部配置
_time_filter_env = os.getenv("TREND_CRAWLER_RUNTIME_TIME_RANGE_MAX", "")
if _time_filter_env:
    try:
        TIME_FILTER_HOURS = int(_time_filter_env)
    except ValueError:
        TIME_FILTER_HOURS = 48
else:
    TIME_FILTER_HOURS = 48


# 控制并发爬取数量
MAX_CONCURRENCY_NUM = 1

# 是否启用媒体资源爬取模式（包括图片或视频资源），默认不启用
ENABLE_GET_MEIDAS = False

# 是否启用评论爬取模式，默认启用评论爬取
ENABLE_GET_COMMENTS = False

# 控制单个视频/帖子的一级评论爬取数量
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 10

# 是否启用二级评论爬取模式，默认不启用二级评论爬取
# 如果旧版本项目使用 db，需要参考 schema/tables.sql 第287行添加表字段
ENABLE_GET_SUB_COMMENTS = False

# ==================== 词云图相关配置 ====================
# 是否启用生成评论词云图
ENABLE_GET_WORDCLOUD = False

# 自定义词汇及其分组
# 添加规则格式：xx:yy 其中 xx 是自定义添加的词汇，yy 是该词汇所属的分组名称
CUSTOM_WORDS = {
    "零几": "年份",  # 识别"零几点"作为整体
    "高频词": "专业术语",  # 示例自定义词汇
}

# 停用词文件路径
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# 中文字体文件路径
FONT_PATH = "./docs/STZHONGS.TTF"

# 爬取间隔时间（秒）
CRAWLER_MAX_SLEEP_SEC = 2

# 是否禁用 SSL 证书验证
# 仅在使用企业代理、Burp Suite、mitmproxy 等会注入自签名证书的中间人代理时设为 True
# 警告：禁用 SSL 验证将使所有流量暴露于中间人攻击风险，请勿在生产环境中开启
DISABLE_SSL_VERIFY = False

# 导入各平台的特定配置
from .bilibili_config import *
from .xhs_config import *
from .dy_config import *
from .ks_config import *
from .weibo_config import *
from .tieba_config import *
from .zhihu_config import *
