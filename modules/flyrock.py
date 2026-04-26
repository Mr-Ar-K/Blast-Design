import math


def flyrock_distance(burden_m, stemming_m, charge_kg):
    if burden_m <= 0 or stemming_m <= 0 or charge_kg <= 0:
        raise ValueError("burden_m, stemming_m, and charge_kg must be positive")
    confinement_ratio = burden_m / stemming_m
    return max(10.0, 8.0 * math.sqrt(charge_kg) * confinement_ratio)


def flyrock_risk_zone(burden_m, stemming_m, charge_kg):
    distance = flyrock_distance(burden_m, stemming_m, charge_kg)
    if distance > 300:
        risk = "HIGH"
    elif distance > 180:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    return {
        "distance_m": distance,
        "risk": risk,
    }
