import pandas as pd
from scipy.optimize import minimize
import numpy as np

from modules.opencast import OpencastDesign
from modules.underground import UndergroundDesign


def total_drilling_blasting_cost(ca, cb, cd, cdr):
    return ca + cb + cd + cdr


def cost_per_tonne(total_cost, tonnage):
    return total_cost / max(tonnage, 1e-6)


def cost_per_cubic_meter(total_cost, volume):
    return total_cost / max(volume, 1e-6)


def optimize_blast(rock, explosive, bench, target_xm=15.0, target_n=1.5):
    def objective(x):
        trial_bench = dict(bench)
        trial_bench["hole_diameter"] = x[0]
        trial_bench["bench_height"] = x[1]
        design = OpencastDesign(rock, explosive, trial_bench)
        xm = design.kuz_ram_xm()
        n = design.uniformity_index()
        total_cost = total_drilling_blasting_cost(
            ca=design.charge_per_hole() * explosive.get("cost_per_kg", 0.0),
            cb=trial_bench.get("drilling_cost", 0.0),
            cd=trial_bench.get("delay_cost", 0.0),
            cdr=trial_bench.get("support_cost", 0.0),
        )
        penalty = max(0.0, xm - target_xm) * 100.0 + max(0.0, target_n - n) * 100.0
        return total_cost + penalty

    return minimize(objective, [bench["hole_diameter"], bench["bench_height"]], bounds=[(100, 300), (5, 25)])


def optimize_underground(tunnel, explosive):
    design = UndergroundDesign(tunnel, explosive)
    total_cost = total_drilling_blasting_cost(
        ca=design.specific_charge() * explosive.get("cost_per_kg", 0.0),
        cb=tunnel.get("drilling_cost", 0.0),
        cd=tunnel.get("delay_cost", 0.0),
        cdr=tunnel.get("support_cost", 0.0),
    )
    return {
        "specific_charge": design.specific_charge(),
        "total_cost": total_cost,
        "cost_per_tonne": cost_per_tonne(total_cost, tunnel.get("tonnage", 1.0)),
        "cost_per_cubic_meter": cost_per_cubic_meter(total_cost, design.face_area() * tunnel.get("advance", 1.0)),
    }


def generate_opencast_scenarios(rock, explosive, base_bench, target_x50=15.0):
    """
    Generates multiple blast design cases based on standard hole diameters.
    Returns a DataFrame of results and identifies the best case.
    """
    standard_diameters = [89.0, 102.0, 115.0, 150.0, 165.0, 200.0]
    results = []

    for diameter in standard_diameters:
        trial_bench = dict(base_bench)
        trial_bench["hole_diameter"] = diameter
        design = OpencastDesign(rock, explosive, trial_bench)

        burden = design.burden()
        spacing = design.spacing()
        charge = design.charge_per_hole()
        pf = design.powder_factor()
        x50 = design.kuz_ram_xm()
        n_index = design.uniformity_index()

        tonnage_per_hole = burden * spacing * trial_bench["bench_height"] * rock["density"] / 1000
        cost_explosive = charge * explosive.get("cost_per_kg", 0.0)
        cost_drilling = trial_bench.get("drilling_cost_per_m", 0.0) * (trial_bench["bench_height"] + design.subdrilling())
        total_hole_cost = cost_explosive + cost_drilling + trial_bench.get("accessories_cost", 0.0)

        cost_per_tonne_value = total_hole_cost / max(tonnage_per_hole, 1e-6)

        results.append(
            {
                "Hole Dia (mm)": diameter,
                "Burden x Spacing (m)": f"{burden:.1f} x {spacing:.1f}",
                "Powder Factor (kg/m3)": round(pf, 2),
                "Mean Fragment X50 (cm)": round(x50, 2),
                "Uniformity (n)": round(n_index, 2),
                "Cost per Tonne (₹)": round(cost_per_tonne_value, 2),
                "Total Hole Cost (₹)": round(total_hole_cost, 2),
                "_x50_raw": x50,
                "_cost_raw": cost_per_tonne_value,
            }
        )

    df = pd.DataFrame(results)

    valid_cases = df[df["_x50_raw"] <= target_x50]

    if not valid_cases.empty:
        best_idx = valid_cases["_cost_raw"].idxmin()
        best_case = df.loc[best_idx].copy()
    else:
        best_idx = df["_x50_raw"].idxmin()
        best_case = df.loc[best_idx].copy()
        best_case["Note"] = "Target X50 not met, showing finest fragmentation."

    df_clean = df.drop(columns=["_x50_raw", "_cost_raw"])

    return df_clean, best_case


PATTERN_ROW_PITCH_FACTOR = {
    "Square": 1.00,
    "Staggered": 1.00,
    "Triangular": 0.866,
    "Echelon": 0.90,
}


def build_bench_pattern_points(pattern, rows, cols, burden, spacing):
    points = []
    row_pitch = burden * PATTERN_ROW_PITCH_FACTOR.get(pattern, 1.0)
    for i in range(rows):
        for j in range(cols):
            x = j * spacing
            y = i * row_pitch
            if pattern == "Staggered" and i % 2 == 1:
                x += spacing / 2.0
            elif pattern == "Triangular" and i % 2 == 1:
                x += spacing / 2.0
            elif pattern == "Echelon":
                x += (i * 0.2 * spacing)
            points.append((x, y))
    return np.array(points)


def recommend_opencast_layout(
    rock,
    explosive,
    base_bench,
    blast_length,
    blast_width,
    target_tonnage,
    target_x50=25.0,
):
    patterns = ["Square", "Staggered", "Triangular", "Echelon"]
    diameters = [89.0, 102.0, 115.0, 150.0, 165.0, 200.0]
    candidates = []

    for hole_dia in diameters:
        trial_bench = dict(base_bench)
        trial_bench["hole_diameter"] = hole_dia
        design = OpencastDesign(rock, explosive, trial_bench)
        base_burden = design.burden()
        base_spacing = design.spacing()
        x50 = design.kuz_ram_xm()
        charge_per_hole = design.charge_per_hole()

        for pattern in patterns:
            row_pitch = base_burden * PATTERN_ROW_PITCH_FACTOR[pattern]
            rows = max(1, int(blast_length / max(row_pitch, 1e-6)) + 1)
            cols = max(1, int(blast_width / max(base_spacing, 1e-6)) + 1)
            holes = rows * cols

            volume_per_hole = row_pitch * base_spacing * trial_bench["bench_height"]
            tonnage_per_hole = volume_per_hole * rock["density"] / 1000.0
            total_tonnage = holes * tonnage_per_hole

            drilling_cost = trial_bench.get("drilling_cost_per_m", 0.0) * (trial_bench["bench_height"] + design.subdrilling())
            accessories_cost = trial_bench.get("accessories_cost", 0.0)
            hole_cost = charge_per_hole * explosive.get("cost_per_kg", 0.0) + drilling_cost + accessories_cost
            total_cost = holes * hole_cost
            cost_t = total_cost / max(total_tonnage, 1e-6)

            tonnage_penalty = max(0.0, target_tonnage - total_tonnage) * 0.5
            frag_penalty = max(0.0, x50 - target_x50) * 25.0
            score = cost_t + tonnage_penalty + frag_penalty

            candidates.append(
                {
                    "Pattern": pattern,
                    "Hole Dia (mm)": hole_dia,
                    "Rows": rows,
                    "Cols": cols,
                    "Holes": holes,
                    "Burden (m)": round(base_burden, 2),
                    "Spacing (m)": round(base_spacing, 2),
                    "X50 (cm)": round(x50, 2),
                    "Total Tonnage (t)": round(total_tonnage, 1),
                    "Cost per Tonne (₹)": round(cost_t, 2),
                    "Total Cost (₹)": round(total_cost, 2),
                    "_score": score,
                }
            )

    df = pd.DataFrame(candidates)
    best_idx = df["_score"].idxmin()
    best_row = df.loc[best_idx].copy()

    best_pattern_points = build_bench_pattern_points(
        pattern=best_row["Pattern"],
        rows=int(best_row["Rows"]),
        cols=int(best_row["Cols"]),
        burden=float(best_row["Burden (m)"]),
        spacing=float(best_row["Spacing (m)"]),
    )

    return df.drop(columns=["_score"]).sort_values("Cost per Tonne (₹)").reset_index(drop=True), best_row, best_pattern_points
