#!/usr/bin/env python3
"""Run Google News keyword search only."""

from search_common import run_single_source_search


if __name__ == "__main__":
    raise SystemExit(run_single_source_search("google_news"))
