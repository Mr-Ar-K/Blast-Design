import math

import numpy as np


def delay_timing_simulation(rows, cols, inter_row_ms=42, inter_hole_ms=17):
    events = []
    for row in range(rows):
        for col in range(cols):
            events.append({"row": row, "hole": col, "delay_ms": row * inter_row_ms + col * inter_hole_ms})
    return events


def ppv_usbm(charge_weight_kg, distance_m, k=1140.0, alpha=1.6):
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    return k * ((charge_weight_kg ** 0.5) / (distance_m ** alpha))


def flyrock_safety_margin(burden_m, stemming_m, factor=1.5):
    required_stemming = factor * burden_m
    return {
        "required_stemming_m": required_stemming,
        "margin_m": stemming_m - required_stemming,
        "is_safe": stemming_m >= required_stemming,
    }


def drill_deviation_model(points, deviation_std_m=0.15):
    adjusted = []
    for index, (x, y) in enumerate(points):
        delta = deviation_std_m * math.sin(index + 1)
        adjusted.append((x + delta, y - delta / 2))
    return np.array(adjusted)


class UndergroundDesign:
    def __init__(self, tunnel, explosive):
        self.tunnel = tunnel
        self.explosive = explosive

    def face_area(self):
        return self.tunnel["width"] * self.tunnel["height"]

    def rock_constraining_factor(self):
        return 6.5 / math.sqrt(max(self.face_area(), 1e-6))

    def specific_charge(self):
        q1 = self.tunnel["rock_hardness"] * 0.1
        e = self.explosive.get("energy_factor", 1.0)
        f1 = self.explosive.get("fragmentation_factor", 1.0)
        k_cons = self.rock_constraining_factor()
        return q1 * e * f1 * k_cons

    def hole_distribution(self):
        cut_holes = int(self.tunnel.get("cut_holes", 4))
        outside_holes = int(self.tunnel.get("outside_holes", 6))
        contour_holes = int(self.tunnel.get("contour_holes", 8))
        total = cut_holes + outside_holes + contour_holes
        return {
            "N_cut": cut_holes,
            "N_out": outside_holes,
            "N_o": contour_holes,
            "N_total": total,
        }

    def v_cut_points(self, center=(0.0, 0.0), radius=0.6):
        cx, cy = center
        holes = []
        for angle in (60, 70, 110, 120):
            rad = math.radians(angle)
            holes.append((cx + radius * math.cos(rad), cy + radius * math.sin(rad)))
        holes.append((cx, cy))
        return np.array(holes)

    def burn_cut_points(self, center=(0.0, 0.0), spacing=0.5):
        cx, cy = center
        return np.array([
            (cx, cy),
            (cx - spacing, cy),
            (cx + spacing, cy),
            (cx, cy + spacing),
            (cx, cy - spacing),
        ])

    def contour_hole_points(self, spacing=0.6):
        """Generates contour holes along tunnel perimeter (arch roof + straight walls)."""
        if spacing <= 0:
            raise ValueError("spacing must be positive")

        w = self.tunnel["width"]
        h = self.tunnel["height"]
        radius = w / 2.0
        arch_center_y = h - radius
        arch_length = math.pi * radius
        num_arch_holes = max(1, int(arch_length / spacing))
        points = []

        for i in range(num_arch_holes + 1):
            angle = math.pi * (i / num_arch_holes)
            x = radius * math.cos(angle)
            y = arch_center_y + radius * math.sin(angle)
            points.append((x, y))

        wall_height = max(arch_center_y, 0.0)
        num_wall_holes = int(wall_height / spacing)
        for i in range(1, num_wall_holes + 1):
            y = arch_center_y - (i * spacing)
            points.append((-radius, y))
            points.append((radius, y))

        return np.array(points)
