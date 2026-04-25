def compare_packet_to_manual_prompt(
    packet_minutes: float,
    manual_minutes: float,
    packet_accepted_findings: int,
    manual_accepted_findings: int,
) -> dict[str, float | int | bool]:
    if packet_minutes <= 0 or manual_minutes <= 0:
        raise ValueError("Minutes must be positive")
    time_saved_percent = round(((manual_minutes - packet_minutes) / manual_minutes) * 100, 2)
    accepted_findings_delta = packet_accepted_findings - manual_accepted_findings
    return {
        "time_saved_percent": time_saved_percent,
        "accepted_findings_delta": accepted_findings_delta,
        "beats_manual": time_saved_percent >= 30 or accepted_findings_delta > 0,
    }