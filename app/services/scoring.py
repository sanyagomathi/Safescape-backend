from .trust import trust_weight

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def time_multiplier(hour: int) -> float:
    if hour >= 21 or hour <= 5:
        return 0.88
    if hour >= 18:
        return 0.95
    return 1.0

def objective_base(lighting: float, crowd: float, shops_open: float, transport: float) -> float:
    base = 0.30 * lighting + 0.25 * crowd + 0.25 * shops_open + 0.20 * transport

    # dead-zone penalty: all objective signals weak
    dead_zone = lighting < 0.25 and crowd < 0.25 and shops_open < 0.25
    if dead_zone:
        base *= 0.60
    return clamp01(base)

def compute_score(
    *,
    hour: int,
    signals: dict,
    reviews: list[dict],
) -> dict:
    """
    Returns: overall, women, confidence, anomaly
    reviews list items: {"rating": float, "gender": str}
    """
    obj = objective_base(
        signals.get("lighting", 0.5),
        signals.get("crowd", 0.5),
        signals.get("shops_open", 0.5),
        signals.get("transport", 0.5),
    ) * time_multiplier(hour)
    obj = clamp01(obj)

    # weighted review average (general)
    def weighted_avg(filter_gender: str | None, viewer_gender: str) -> float | None:
        w_sum = 0.0
        x_sum = 0.0
        for r in reviews:
            if filter_gender and r["gender"] != filter_gender:
                continue
            w = trust_weight(r["gender"], viewer_gender, hour)
            w_sum += w
            x_sum += w * float(r["rating"])
        if w_sum == 0:
            return None
        return clamp01(x_sum / w_sum)

    women_avg = weighted_avg("woman", "woman")
    general_avg = weighted_avg(None, "unknown")

    # blend objective + reviews
    overall = 0.55 * obj + 0.45 * (general_avg if general_avg is not None else 0.5)

    # objective floor constraints (prevents “3 fake safe reviews” overriding dark/isolated reality)
    if obj < 0.35:
        overall = min(overall, 0.55)
    if obj < 0.25:
        overall = min(overall, 0.45)

    # anomaly detection: low objective + many high male ratings + low women ratings
    very_safe_men = sum(1 for r in reviews if r["gender"] == "man" and float(r["rating"]) >= 0.85)
    women_unsafe = sum(1 for r in reviews if r["gender"] == "woman" and float(r["rating"]) <= 0.35)
    anomaly = (obj < 0.45 and very_safe_men >= 3 and women_unsafe >= 1)
    if anomaly:
        overall = min(overall, 0.50)

    overall = clamp01(overall)

    # confidence: grows with review count and objective strength
    n = len(reviews)
    review_conf = 1 - pow(2.718281828, (-n / 6.0))
    obj_conf = 0.5 + 0.5 * obj
    confidence = clamp01(0.55 * review_conf + 0.45 * obj_conf)
    if anomaly:
        confidence = clamp01(confidence * 0.75)

    return {
        "overall": overall,
        "women": women_avg,
        "confidence": confidence,
        "anomaly": anomaly,
    }