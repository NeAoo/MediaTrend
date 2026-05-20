from __future__ import annotations


def count_progress(current_count: int, max_count: int) -> float:
    if max_count <= 0:
        return 0.0
    return min(1.0, max(0.0, current_count / max_count))


def expected_count_warning(
    unit_name: str,
    current_count: int,
    expected_min_count: int,
) -> str:
    if expected_min_count <= 0 or current_count >= expected_min_count:
        return ""
    return f"{unit_name} 低于预期：{current_count}/{expected_min_count}"
