from .ai_tools import get_area_snapshot


def build_home_insights(snapshot: dict, hour: int | None) -> dict:
    avg = snapshot["avg_safety"]
    segs = snapshot["segments_analyzed"]
    low = snapshot["low_safety_segments"]
    safe_points = snapshot["safe_points_nearby"]
    open_24 = snapshot["open_24x7_safe_points"]
    transit = snapshot["transit_points"]
    police = snapshot["police_points"]
    anomaly = snapshot["anomaly_segments"]

    time_phrase = (
        f"at {hour}:00" if hour is not None else "for the selected time"
    )

    if avg >= 0.7:
        tone = "generally safe"
    elif avg >= 0.45:
        tone = "moderately safe"
    else:
        tone = "relatively risky"

    summary = (
        f"Area appears {tone} {time_phrase}. "
        f"{segs} nearby segments were analyzed, with average safety {avg:.2f}."
    )

    highlights = []

    if transit > 0:
        highlights.append("Good transport presence nearby")
    if police > 0:
        highlights.append("Police safe points available nearby")
    if open_24 > 0:
        highlights.append("24/7 support points available nearby")
    if low > 0:
        highlights.append(f"{low} lower-safety segments need caution")
    if anomaly > 0:
        highlights.append(f"{anomaly} segment(s) show unusual safety disagreement patterns")
    if safe_points == 0:
        highlights.append("No registered safe points nearby in current radius")

    return {
        "summary": summary,
        "stats": snapshot,
        "highlights": highlights[:4],
    }


def run_agent_chat(*, message: str, snapshot: dict, hour: int | None) -> dict:
    text = message.lower()
    avg = snapshot["avg_safety"]
    low = snapshot["low_safety_segments"]
    safe_points = snapshot["safe_points_nearby"]
    police = snapshot["police_points"]
    medical = snapshot["medical_points"]
    transit = snapshot["transit_points"]

    if "safe" in text and "night" in text:
        if avg >= 0.7:
            reply = (
                f"This area looks fairly safe at night based on current signals. "
                f"Average safety is {avg:.2f}, with {safe_points} nearby safe points."
            )
        elif avg >= 0.45:
            reply = (
                f"This area looks moderately safe at night. "
                f"Average safety is {avg:.2f}; there are {low} lower-safety segments, "
                f"so prefer main roads and nearby transit-linked areas."
            )
        else:
            reply = (
                f"This area looks relatively risky at night. "
                f"Average safety is {avg:.2f}, and {low} low-safety segments were detected."
            )
    elif "police" in text:
        reply = f"There are {police} police safe point(s) within the selected radius."
    elif "medical" in text or "hospital" in text:
        reply = f"There are {medical} medical safe point(s) nearby."
    elif "transport" in text or "metro" in text or "bus" in text:
        reply = f"There are {transit} transit-linked safe point(s) nearby."
    else:
        reply = (
            f"I analyzed the nearby area and found average safety of {avg:.2f}, "
            f"{safe_points} safe points nearby, and {low} lower-safety segments. "
            f"Ask about night safety, police, medical, or safest movement advice."
        )

    return {
        "reply": reply,
        "context": {
            "avg_safety": avg,
            "safe_points_nearby": safe_points,
            "low_safety_segments": low,
            "hour": hour,
        },
    }