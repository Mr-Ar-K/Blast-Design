import math


def rosin_rammler(x, x50, n):
    if x <= 0 or x50 <= 0 or n <= 0:
        return 0.0
    return 1.0 - math.exp(-((x / x50) ** n))


def size_at_percentile(x50, n, percentile):
    if x50 <= 0 or n <= 0:
        raise ValueError("x50 and n must be positive")
    if percentile <= 0 or percentile >= 100:
        raise ValueError("percentile must be in (0, 100)")
    p = percentile / 100.0
    return x50 * ((-math.log(1.0 - p)) ** (1.0 / n))


def distribution_curve(x50, n, x_min=1.0, x_max=250.0, points=60):
    if x_min <= 0 or x_max <= x_min:
        raise ValueError("x range is invalid")
    step = (x_max - x_min) / max(points - 1, 1)
    xs = [x_min + i * step for i in range(points)]
    ys = [rosin_rammler(x, x50, n) * 100.0 for x in xs]
    return xs, ys


def key_fragment_sizes(x50, n):
    return {
        "P20": size_at_percentile(x50, n, 20.0),
        "P50": size_at_percentile(x50, n, 50.0),
        "P80": size_at_percentile(x50, n, 80.0),
    }
