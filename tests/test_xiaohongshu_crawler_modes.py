import importlib


def test_xiaohongshu_runs_search_and_creator_modes(monkeypatch):
    module = importlib.import_module("crawlers.xiaohongshu")
    creator_url = (
        "https://www.xiaohongshu.com/user/profile/abc?"
        "xsec_token=token&xsec_source=pc_search"
    )
    monkeypatch.setattr(module, "XIAOHONGSHU_CREATOR_URLS", [creator_url])
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD", 8)
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT", 6)
    monkeypatch.setattr(module, "XIAOHONGSHU_LOGIN_TYPE", "qrcode")
    monkeypatch.setattr(module, "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)

    crawler = module.XiaohongshuCrawler()
    commands = []

    def fake_run(mode, items, max_count, time_range_hours, timeout):
        commands.append((mode, items, max_count, time_range_hours, timeout))
        return True

    monkeypatch.setattr(crawler, "_run_trendcrawler", fake_run)
    monkeypatch.setattr(crawler, "_load_and_convert_data", lambda *args, **kwargs: [])

    result = crawler.collect(
        ["教育改革"],
        time_range_hours=(0, 24),
        creator_time_range_hours=(0, 168),
        runtime_timeout_seconds=120,
    )

    assert result.success_count == 0
    assert commands == [
        ("search", ["教育改革"], 8, 24, 120),
        ("creator", [creator_url], 6, 168, 120),
    ]


def test_xiaohongshu_accepts_creator_url_override(monkeypatch):
    module = importlib.import_module("crawlers.xiaohongshu")
    creator_url = (
        "https://www.xiaohongshu.com/user/profile/override?"
        "xsec_token=token&xsec_source=pc_search"
    )
    monkeypatch.setattr(module, "XIAOHONGSHU_CREATOR_URLS", [])
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT", 6)
    monkeypatch.setattr(module, "XIAOHONGSHU_LOGIN_TYPE", "qrcode")
    monkeypatch.setattr(module, "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)

    crawler = module.XiaohongshuCrawler()
    commands = []

    def fake_run(mode, items, max_count, time_range_hours, timeout):
        commands.append((mode, items, max_count, time_range_hours, timeout))
        return True

    monkeypatch.setattr(crawler, "_run_trendcrawler", fake_run)
    monkeypatch.setattr(crawler, "_load_and_convert_data", lambda *args, **kwargs: [])

    result = crawler.collect([], time_range_hours=(0, 24), creator_urls=[creator_url])

    assert result.success_count == 0
    assert commands == [("creator", [creator_url], 6, 24, 900)]


def test_xiaohongshu_extracts_and_expands_share_short_link(monkeypatch):
    module = importlib.import_module("crawlers.xiaohongshu")
    share_text = (
        "@example_user received 123 likes and saves on rednote，"
        "visit the profile>> https://xhslink.com/m/examplePath"
    )
    profile_url = (
        "https://www.xiaohongshu.com/user/profile/0123456789abcdef01234567"
        "?xsec_token=token&xsec_source=app_share"
    )
    monkeypatch.setattr(module, "XIAOHONGSHU_CREATOR_URLS", [])
    monkeypatch.setattr(module, "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT", 6)
    monkeypatch.setattr(module, "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)

    crawler = module.XiaohongshuCrawler()
    commands = []

    def fake_expand(candidate_url):
        assert candidate_url == "https://xhslink.com/m/examplePath"
        return profile_url

    def fake_run(mode, items, max_count, time_range_hours, timeout):
        commands.append((mode, items, max_count, time_range_hours, timeout))
        return True

    monkeypatch.setattr(crawler, "_expand_short_creator_url", fake_expand)
    monkeypatch.setattr(crawler, "_run_trendcrawler", fake_run)
    monkeypatch.setattr(crawler, "_load_and_convert_data", lambda *args, **kwargs: [])

    result = crawler.collect([], time_range_hours=(0, 24), creator_urls=[share_text])

    assert result.success_count == 0
    assert commands == [("creator", [profile_url], 6, 24, 900)]
