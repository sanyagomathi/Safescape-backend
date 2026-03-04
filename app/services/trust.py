def trust_weight(reviewer_gender: str, viewer_gender: str, hour: int) -> float:
    """
    MVP trust weighting:
    - At late night, women viewers weigh women reviews higher.
    - Men reviews slightly downweighted at night for women viewers.
    """
    night = (hour >= 21 or hour <= 5)

    if viewer_gender == "woman" and night:
        if reviewer_gender == "woman":
            return 1.25
        if reviewer_gender == "man":
            return 0.85
    return 1.0