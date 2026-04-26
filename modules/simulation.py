import numpy as np


def simulate_deviation(mean_burden=3.0, std_burden=0.2, n=1000, seed=42):
    rng = np.random.default_rng(seed)
    burdens = rng.normal(mean_burden, std_burden, n)
    return burdens.mean(), burdens.std(ddof=1)


def confidence_interval(samples, confidence=0.95):
    alpha = (1.0 - confidence) / 2.0
    lower = np.quantile(samples, alpha)
    upper = np.quantile(samples, 1.0 - alpha)
    return float(lower), float(upper)


def simulate_burden_distribution(mean_burden=3.0, std_burden=0.2, n=1000, seed=42):
    rng = np.random.default_rng(seed)
    burdens = rng.normal(mean_burden, std_burden, n)
    low, high = confidence_interval(burdens)
    return {
        "samples": burdens,
        "mean": float(burdens.mean()),
        "std": float(burdens.std(ddof=1)),
        "ci95": (low, high),
    }
