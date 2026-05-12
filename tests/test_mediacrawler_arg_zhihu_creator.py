import asyncio
import importlib
import sys
from pathlib import Path


def test_mediacrawler_maps_zhihu_creator_id(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    mediacrawler_root = project_root / "MediaCrawler"
    for name in list(sys.modules):
        if name == "config" or name.startswith("config."):
            sys.modules.pop(name)
    monkeypatch.syspath_prepend(str(mediacrawler_root))

    try:
        arg_module = importlib.import_module("cmd_arg.arg")
        config = importlib.import_module("config")

        asyncio.run(
            arg_module.parse_cmd(
                [
                    "--platform",
                    "zhihu",
                    "--lt",
                    "qrcode",
                    "--type",
                    "creator",
                    "--creator_id",
                    "https://www.zhihu.com/people/yd1234567",
                ]
            )
        )

        assert config.ZHIHU_CREATOR_URL_LIST == [
            "https://www.zhihu.com/people/yd1234567"
        ]
    finally:
        for name in list(sys.modules):
            if (
                name == "config"
                or name.startswith("config.")
                or name == "cmd_arg"
                or name.startswith("cmd_arg.")
            ):
                sys.modules.pop(name)
