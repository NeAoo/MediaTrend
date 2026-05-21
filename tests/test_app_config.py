import pytest

from config.app_config import ConfigValidationError, load_app_config


def test_default_config_uses_no_login_google_news_source(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("{}", encoding="utf-8")

    config = load_app_config(config_file)

    assert config.enabled_sources == ["google_news"]
    assert config.google_news.keywords == ["教育改革", "中考"]


def test_load_app_config_reads_business_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat_mp
  - xiaohongshu
  - zhihu
collection:
  initial_collect_count: 12
  time_range_hours:
    min: 0
    max: 48
selection:
  top_n: 6
wechat:
  account_crawl:
    accounts:
      - 中国教育报
xiaohongshu:
  keyword_search:
    keywords:
      - 中考
    max_results_per_keyword: 9
    time_range_hours:
      min: 0
      max: 36
zhihu:
  keyword_search:
    keywords:
      - 教育改革
    max_results_per_keyword: 7
output:
  dir: ./out
  filename_pattern: report_{date}.md
  material_export_enabled: false
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.enabled_sources == ["wechat_mp", "xiaohongshu", "zhihu"]
    assert config.collection.initial_collect_count == 12
    assert config.collection.time_range_hours.max == 48
    assert config.selection.top_n == 6
    assert config.wechat.account_crawl.accounts == ["中国教育报"]
    assert config.xiaohongshu.keyword_search.keywords == ["中考"]
    assert config.xiaohongshu.keyword_search.time_range_hours.max == 36
    assert config.zhihu.keyword_search.max_results_per_keyword == 7
    assert config.output.dir == "./out"
    assert config.output.filename_pattern == "report_{date}.md"
    assert config.output.material_export_enabled is False


def test_load_app_config_supports_keyword_and_creator_sources(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - wechat
  - wechat_mp
  - xiaohongshu
  - zhihu
  - google_news
  - aihot
wechat:
  keyword_search:
    keywords:
      - 微信词
    max_results_per_keyword: 4
    time_range_hours:
      min: 0
      max: 12
    use_playwright: false
    fetch_detail_page: true
  account_crawl:
    accounts:
      - 中国教育报
    max_results_per_account: 3
    time_range_hours:
      min: 0
      max: 72
xiaohongshu:
  keyword_search:
    keywords:
      - 小红书词
    max_results_per_keyword: 8
    time_range_hours:
      min: 0
      max: 48
  account_crawl:
    creator_urls:
      - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
    max_results_per_account: 6
    time_range_hours:
      min: 0
      max: 168
zhihu:
  keyword_search:
    keywords:
      - 知乎词
    max_results_per_keyword: 9
  account_crawl:
    creator_urls:
      - https://www.zhihu.com/people/yd1234567
    max_results_per_account: 7
    time_range_hours:
      min: 0
      max: 120
google_news:
  keywords:
    - 通用词
  max_results_per_keyword: 5
  period: 7d
  language: zh-CN
  country: CN
aihot:
  keywords:
    - OpenAI
  mode: selected
  categories:
    - ai-models
  max_results_per_query: 30
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.enabled_sources == [
        "wechat",
        "wechat_mp",
        "xiaohongshu",
        "zhihu",
        "google_news",
        "aihot",
    ]
    assert config.wechat.keyword_search.keywords == ["微信词"]
    assert config.wechat.keyword_search.max_results_per_keyword == 4
    assert config.wechat.keyword_search.time_range_hours.max == 12
    assert config.wechat.keyword_search.use_playwright is False
    assert config.wechat.keyword_search.fetch_detail_page is True
    assert config.wechat.account_crawl.max_results_per_account == 3
    assert config.wechat.account_crawl.time_range_hours.max == 72
    assert config.xiaohongshu.account_crawl.creator_urls[0].startswith(
        "https://www.xiaohongshu.com/user/profile/"
    )
    assert config.xiaohongshu.account_crawl.max_results_per_account == 6
    assert config.zhihu.account_crawl.creator_urls == [
        "https://www.zhihu.com/people/yd1234567"
    ]
    assert config.zhihu.account_crawl.max_results_per_account == 7
    assert config.zhihu.account_crawl.time_range_hours.max == 120
    assert config.google_news.keywords == ["通用词"]
    assert config.google_news.period == "7d"
    assert config.aihot.keywords == ["OpenAI"]
    assert config.aihot.mode == "selected"
    assert config.aihot.categories == ["ai-models"]
    assert config.aihot.max_results_per_query == 30


def test_web_defaults_load_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - google_news
google_news:
  keywords:
    - 教育
web:
  default_execution_mode: serial
  default_run_mode: collect_only
  unit_timeout_seconds: 90
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.web.default_execution_mode == "serial"
    assert config.web.default_run_mode == "collect_only"
    assert config.web.unit_timeout_seconds == 90


def test_enabled_creator_source_accepts_empty_keywords_when_creator_urls_exist(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
  - zhihu
xiaohongshu:
  keyword_search:
    keywords: []
  account_crawl:
    creator_urls:
      - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
zhihu:
  keyword_search:
    keywords: []
  account_crawl:
    creator_urls:
      - https://www.zhihu.com/people/yd1234567
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.xiaohongshu.account_crawl.creator_urls
    assert config.zhihu.account_crawl.creator_urls


def test_enabled_creator_source_ignores_disabled_submode_inputs(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
xiaohongshu:
  keyword_search:
    enabled: false
    keywords:
      - 不参与采集
  account_crawl:
    enabled: true
    creator_urls:
      - https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xsec_token=token&xsec_source=pc_search
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    config = load_app_config(config_file)

    assert config.xiaohongshu.keyword_search.enabled is False
    assert config.xiaohongshu.account_crawl.enabled is True


def test_enabled_creator_source_fails_when_all_submodes_disabled(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - zhihu
zhihu:
  keyword_search:
    enabled: false
    keywords:
      - 不参与采集
  account_crawl:
    enabled: false
    creator_urls:
      - https://www.zhihu.com/people/yd1234567
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="zhihu enabled"):
        load_app_config(config_file)


def test_google_news_requires_keywords_when_enabled(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - google_news
google_news:
  keywords: []
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="google_news.*keywords"):
        load_app_config(config_file)


def test_enabled_source_requires_configured_keywords(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - xiaohongshu
xiaohongshu:
  keyword_search:
    keywords: []
zhihu:
  keyword_search:
    keywords:
      - 教育
wechat:
  account_crawl:
    accounts:
      - 人民教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="xiaohongshu.*keywords"):
        load_app_config(config_file)


def test_unknown_enabled_source_fails(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
enabled_sources:
  - mastodon
wechat:
  account_crawl:
    accounts:
      - 人民教育
xiaohongshu:
  keyword_search:
    keywords:
      - 教育
zhihu:
  keyword_search:
    keywords:
      - 教育
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="Unsupported source"):
        load_app_config(config_file)
