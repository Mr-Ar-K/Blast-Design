import numpy as np


def row_wise_delay(rows, cols, inter_row_ms=42, inter_hole_ms=17):
    sequence = []
    for r in range(rows):
        for c in range(cols):
            sequence.append({"row": r, "col": c, "delay_ms": r * inter_row_ms + c * inter_hole_ms})
    return sequence


def v_cut_sequence(num_cut_holes=4, start_ms=0, increment_ms=25):
    return [{"hole": i + 1, "delay_ms": start_ms + i * increment_ms} for i in range(num_cut_holes)]


def delay_scatter(points, delays):
    if len(points) != len(delays):
        raise ValueError("points and delays must have same length")
    return np.column_stack((points[:, 0], points[:, 1], np.array(delays, dtype=float)))
