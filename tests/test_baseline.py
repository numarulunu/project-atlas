from atlas_backend.baseline import compare_packet_to_manual_prompt


def test_packet_baseline_requires_hard_metric() -> None:
    result = compare_packet_to_manual_prompt(
        packet_minutes=8,
        manual_minutes=12,
        packet_accepted_findings=3,
        manual_accepted_findings=2,
    )
    assert result["beats_manual"] is True
    assert "time_saved_percent" in result
    assert "accepted_findings_delta" in result


def test_packet_baseline_fails_when_manual_is_better() -> None:
    result = compare_packet_to_manual_prompt(
        packet_minutes=14,
        manual_minutes=8,
        packet_accepted_findings=1,
        manual_accepted_findings=3,
    )
    assert result["beats_manual"] is False