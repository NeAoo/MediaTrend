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
    )

    assert result.success_count == 0
    assert commands == [
        ("search", ["教育改革"], 8, 24, 900),
        ("creator", [creator_url], 6, 168, 900),
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
