import math


def scaled_distance(distance_m, charge_weight_kg):
    if distance_m <= 0 or charge_weight_kg <= 0:
        raise ValueError("distance_m and charge_weight_kg must be positive")
    return distance_m / (charge_weight_kg ** 0.5)


def airblast_overpressure(distance_m, charge_weight_kg, k_air=164.4, alpha_air=-24.0):
    sd = scaled_distance(distance_m, charge_weight_kg)
    return k_air + (alpha_air * math.log10(sd))


def max_instantaneous_charge(distance_m, target_scaled_distance=22.0):
    if distance_m <= 0 or target_scaled_distance <= 0:
        raise ValueError("distance_m and target_scaled_distance must be positive")
    return (distance_m / target_scaled_distance) ** 2


class OpencastDesign:
    def __init__(self, rock, explosive, bench):
        self.rock = rock
        self.explosive = explosive
        self.bench = bench

    def calculate_hardness_factor(self, ucs_mpa, youngs_modulus_gpa):
        # Lightweight proxy where higher UCS and stiffness increase hardness contribution.
        return 0.5 * ((ucs_mpa / 5.0) + youngs_modulus_gpa)

    def calculate_rock_factor(self, rmd, jps, jpo, rdi, hardness):
        """
        Calculates Cunningham's Rock Factor (A) for the Kuz-Ram model.
        rmd: Rock Mass Description (10=powdery, 50=massive)
        jps: Joint Plane Spacing
        jpo: Joint Plane Orientation
        rdi: Rock Density Influence (25 * density_t_m3 - 50)
        hardness: Hardness factor (based on UCS and Young's Modulus)
        """
        joint_factor = jps + jpo
        rock_factor = 0.06 * (rmd + joint_factor + rdi + hardness)
        self.rock["rock_factor"] = rock_factor
        return rock_factor

    def burden_konya_walter(self):
        d = self.bench["hole_diameter"]
        rho_e = self.explosive["density"]
        rho_r = self.rock["density"]
        return 0.0315 * d * ((rho_e / rho_r) ** (1 / 3))

    def burden_langefors_kihlstrom(self, factor_of_structure=1.0):
        d = self.bench["hole_diameter"]
        rho_e = self.explosive["density"]
        rho_c = self.explosive.get("density", rho_e)
        c0 = max(self.rock.get("compressive_strength", 100.0), 1e-6)
        return 0.958 * d * math.sqrt(rho_e / (c0 * factor_of_structure)) * (rho_c / max(self.rock["density"], 1e-6)) ** (1 / 3)

    def burden(self):
        return self.burden_konya_walter()

    def spacing(self):
        return 1.25 * self.burden()

    def stemming(self):
        return self.burden()

    def subdrilling(self):
        return 0.3 * self.burden()

    def charge_per_hole(self):
        hole_diameter_m = self.bench["hole_diameter"] / 1000
        hole_depth = self.bench["bench_height"] + self.subdrilling()
        charge_length = max(hole_depth - self.stemming(), 0)
        hole_volume = math.pi * (hole_diameter_m / 2) ** 2 * charge_length
        return hole_volume * self.explosive["density"]

    def powder_factor(self):
        volume = self.burden() * self.spacing() * self.bench["bench_height"]
        return self.charge_per_hole() / max(volume, 1e-6)

    def kuz_ram_xm(self):
        factor_a = self.rock.get("rock_factor", 7.0)
        powder_factor = self.powder_factor()
        charge = self.charge_per_hole()
        anfo_strength = self.explosive["rws"]
        return factor_a * (1 / powder_factor) ** 0.8 * charge ** 0.167 * (115 / anfo_strength) ** 0.633

    def calibrate_kuz_ram(self, x50_observed_cm):
        model_xm = self.kuz_ram_xm()
        factor_a = self.rock["rock_factor"]
        if model_xm <= 0:
            raise ValueError("modeled fragment size must be positive")
        calibrated_a = factor_a * (x50_observed_cm / model_xm)
        return {
            "A_calibrated": calibrated_a,
            "X50_observed_cm": x50_observed_cm,
            "X50_modeled_cm": model_xm,
        }

    def uniformity_index(self):
        B = self.burden()
        D = self.bench.get("drill_spacing", self.spacing())
        W = self.bench.get("stemming", self.stemming())
        S = self.spacing()
        L_B = self.bench.get("burden_length", B)
        L_C = self.bench.get("column_length", B)
        L = self.bench.get("hole_length", self.bench["bench_height"])
        H = self.bench["bench_height"]
        return (2.2 - 14 * (B / max(D, 1e-6))) * (1 - W / max(B, 1e-6)) * (1 + (S / max(B, 1e-6)) / 2) ** 0.5 * (abs(L_B - L_C) / max(L_B + L_C, 1e-6) + 0.1) ** 0.1 * (L / max(H, 1e-6))

    def fragmentation_summary(self):
        return {
            "Rock factor A": self.rock.get("rock_factor", 7.0),
            "Burden (m)": self.burden(),
            "Spacing (m)": self.spacing(),
            "Stemming (m)": self.stemming(),
            "Subdrilling (m)": self.subdrilling(),
            "Charge per hole (kg)": self.charge_per_hole(),
            "Powder factor (kg/m3)": self.powder_factor(),
            "X50 / Xm (cm)": self.kuz_ram_xm(),
            "Uniformity index (n)": self.uniformity_index(),
        }
