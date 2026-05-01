"""Run WeChat public-platform fixed-account search only."""

from search_common import run_single_source_search


if __name__ == "__main__":
    raise SystemExit(run_single_source_search("wechat_mp"))
