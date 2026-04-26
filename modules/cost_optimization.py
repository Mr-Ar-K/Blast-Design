from scipy.optimize import minimize

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
