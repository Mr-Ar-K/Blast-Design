def calculate_rmr(ucs_rating, rqd_rating, spacing_rating, condition_rating, groundwater_rating):
    """Computes Bieniawski-style RMR from component ratings (0-100 scale)."""
    total = ucs_rating + rqd_rating + spacing_rating + condition_rating + groundwater_rating
    return max(0.0, min(100.0, float(total)))


def estimate_gsi(rmr, disturbance_factor=0.0):
    """Approximates GSI from RMR with optional disturbance reduction."""
    gsi = rmr - 5.0 - disturbance_factor
    return max(5.0, min(95.0, gsi))


def rock_mass_factor(rmr):
    """Returns geometric adjustment factor for burden/spacing from rock mass quality."""
    if rmr < 30:
        return 0.85
    if rmr < 45:
        return 0.92
    if rmr < 60:
        return 1.00
    if rmr < 75:
        return 1.08
    return 1.15


def auto_adjustment_factors(rmr, gsi):
    """Returns suggested tuning multipliers for blast geometry and charging."""
    geometry_factor = rock_mass_factor(rmr)
    charging_factor = max(0.85, min(1.20, 1.0 + (55.0 - gsi) / 200.0))
    return {
        "geometry_factor": geometry_factor,
        "charging_factor": charging_factor,
    }
