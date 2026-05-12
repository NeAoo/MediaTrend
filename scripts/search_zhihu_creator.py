"""Run Zhihu creator account crawl only."""

from search_common import run_single_source_search


if __name__ == "__main__":
    raise SystemExit(run_single_source_search("zhihu", default_mode="accounts"))
