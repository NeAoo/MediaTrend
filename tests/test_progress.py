from web.backend.progress import count_progress, expected_count_warning


def test_count_progress_uses_max_count():
    assert count_progress(current_count=5, max_count=10) == 0.5
    assert count_progress(current_count=12, max_count=10) == 1.0


def test_expected_count_warning_is_not_failure():
    warning = expected_count_warning(unit_name="AI education", current_count=2, expected_min_count=3)
    assert warning == "AI education 低于预期：2/3"
    assert expected_count_warning("AI education", 3, 3) == ""
