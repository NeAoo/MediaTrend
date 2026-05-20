from datetime import datetime
from pathlib import Path

from models.hotspot import EducationHotspot
from web.backend.job_runner import JobArtifacts, run_merge_score_report


def test_run_merge_score_report_skips_scoring_when_disabled(tmp_path: Path):
    item = EducationHotspot(
        title="测试",
        source="aihot",
        publish_time=datetime.now(),
        content="正文",
        url="https://example.com",
    )

    artifacts = run_merge_score_report(
        hotspots=[item],
        selected_sources=["aihot"],
        scoring_enabled=False,
        output_root=tmp_path,
    )

    assert isinstance(artifacts, JobArtifacts)
    assert artifacts.merged_file
    assert artifacts.scored_file == ""
    assert artifacts.report_file == ""
