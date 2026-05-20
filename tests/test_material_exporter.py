from __future__ import annotations

import json
from datetime import date, datetime

from formatters.material_exporter import MaterialExporter
from models.hotspot import EducationHotspot


def test_material_exporter_writes_contract_files(tmp_path):
    hotspot = EducationHotspot(
        title="OpenAI 发布新工具",
        source="aihot",
        publish_time=datetime(2026, 5, 20, 9, 30),
        content="这是一段用于生成个人媒体内容的参考素材。",
        url="https://example.com/openai",
        author="AI HOT",
        score=8.75,
        score_details={
            "heat": 8,
            "authority": 9,
            "quality": 8.5,
            "resonance": 7.5,
            "timeliness": 9,
            "reference_value": 8,
            "risk_control": 9,
            "reason": "信息密度高",
            "best_angle": "普通人如何使用新工具",
        },
    )

    output_dir = MaterialExporter(output_root=str(tmp_path)).export(
        [hotspot],
        material_date=date(2026, 5, 20),
        source_names=["aihot"],
    )

    manifest_path = output_dir / "manifest.json"
    content_path = output_dir / "candidates" / "001.md"
    metadata_path = output_dir / "candidates" / "001.json"

    assert manifest_path.exists()
    assert content_path.exists()
    assert metadata_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["date"] == "2026-05-20"
    assert manifest["count"] == 1
    assert manifest["source_names"] == ["aihot"]
    assert manifest["items"][0]["file"] == "candidates/001.md"
    assert manifest["items"][0]["metadata_file"] == "candidates/001.json"
    assert manifest["items"][0]["score"] == 8.75

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["rank"] == 1
    assert metadata["title"] == "OpenAI 发布新工具"
    assert metadata["score_details"]["best_angle"] == "普通人如何使用新工具"

    content = content_path.read_text(encoding="utf-8")
    assert 'title: "OpenAI 发布新工具"' in content
    assert "## AITrend 评分" in content
    assert "## 正文" in content
    assert "这是一段用于生成个人媒体内容的参考素材。" in content
