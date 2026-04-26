import numpy as np
import streamlit as st

from modules.cost_optimization import cost_per_tonne, optimize_blast, optimize_underground, total_drilling_blasting_cost
from modules.opencast import OpencastDesign, airblast_overpressure, max_instantaneous_charge
from modules.underground import UndergroundDesign, delay_timing_simulation, drill_deviation_model, flyrock_safety_margin, ppv_usbm
from modules.visuals import plot_3d_layout, plot_blast_layout


st.set_page_config(page_title="Blast Design Optimizer", layout="wide")
st.sidebar.title("Mining Method")
method = st.sidebar.radio("Select Operation Type", ["Opencast (Surface)", "Underground (Tunneling)"])
distance_to_structure = st.sidebar.slider("Distance to Nearest Structure (m)", min_value=10.0, max_value=2000.0, value=250.0, step=5.0)
target_sd = st.sidebar.slider("Target Scaled Distance (m/kg^0.5)", min_value=5.0, max_value=50.0, value=22.0, step=0.5)

if method == "Opencast (Surface)":
    st.title("Opencast Blast Design & Kuz-Ram Optimization")

    rmd_options = {
        "Powdery/Friable": 10,
        "Blocky": 20,
        "Jointed": 30,
        "Competent": 40,
        "Massive": 50,
    }
    jps_options = {
        "Very close spacing": 10,
        "Close spacing": 20,
        "Moderate spacing": 30,
        "Wide spacing": 40,
    }
    jpo_options = {
        "Very unfavorable": 10,
        "Unfavorable": 20,
        "Intermediate": 30,
        "Favorable": 40,
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Rock Properties")
        rock_density = st.number_input("Rock Density (kg/m3)", value=2600.0)
        compressive_strength = st.number_input("Compressive Strength", value=100.0)
        ucs_mpa = st.number_input("UCS (MPa)", value=120.0)
        youngs_modulus_gpa = st.number_input("Young's Modulus (GPa)", value=35.0)
        rmd_label = st.selectbox("Rock Mass Description (RMD)", list(rmd_options.keys()))
        jps_label = st.selectbox("Joint Plane Spacing (JPS)", list(jps_options.keys()))
        jpo_label = st.selectbox("Joint Plane Orientation (JPO)", list(jpo_options.keys()))
        rock_mass_description = st.text_input("Rock Mass Description", value="moderate jointing")

    with col2:
        st.subheader("Explosive Properties")
        exp_density = st.number_input("Explosive Density (kg/m3)", value=800.0)
        rws = st.number_input("Relative Weight Strength (ANFO=115)", value=115.0)
        explosive_cost = st.number_input("Explosive Cost per kg", value=3.5)

    with col3:
        st.subheader("Bench Parameters")
        hole_dia = st.number_input("Hole Diameter (mm)", value=150.0)
        bench_height = st.number_input("Bench Height (m)", value=10.0)
        tonnage = st.number_input("Tonnage (t)", value=1200.0)

    rock = {
        "density": rock_density,
        "compressive_strength": compressive_strength,
        "rock_mass_description": rock_mass_description,
    }
    explosive = {"density": exp_density, "rws": rws, "cost_per_kg": explosive_cost}
    bench = {"hole_diameter": hole_dia, "bench_height": bench_height}
    design = OpencastDesign(rock, explosive, bench)
    rdi = 25.0 * (rock_density / 1000.0) - 50.0
    hardness = design.calculate_hardness_factor(ucs_mpa, youngs_modulus_gpa)
    rock_factor_a = design.calculate_rock_factor(
        rmd=rmd_options[rmd_label],
        jps=jps_options[jps_label],
        jpo=jpo_options[jpo_label],
        rdi=rdi,
        hardness=hardness,
    )
    st.caption(f"Calculated Cunningham Rock Factor (A): {rock_factor_a:.2f}")

    if st.button("Calculate Optimal Opencast Design"):
        burden = design.burden()
        spacing = design.spacing()
        stemming = design.stemming()
        subdrill = design.subdrilling()
        charge_mass = design.charge_per_hole()
        powder_factor = design.powder_factor()
        x50 = design.kuz_ram_xm()
        n = design.uniformity_index()

        st.success("Optimization Complete!")
        st.write(f"**Calculated Burden:** {burden:.2f} m")
        st.write(f"**Calculated Spacing:** {spacing:.2f} m")
        st.write(f"**Calculated Stemming:** {stemming:.2f} m")
        st.write(f"**Calculated Subdrilling:** {subdrill:.2f} m")
        st.write(f"**Charge per Hole:** {charge_mass:.2f} kg")
        st.write(f"**Powder Factor:** {powder_factor:.2f} kg/m³")
        st.write(f"**Mean Fragment Size (X50):** {x50:.2f} cm")
        st.write(f"**Uniformity Index (n):** {n:.2f}")
        st.write(design.calibrate_kuz_ram(x50_observed_cm=st.number_input("Observed X50 (cm)", value=18.0, key="x50_opencast")))

        ppv = ppv_usbm(charge_mass, distance_to_structure)
        airblast_db = airblast_overpressure(distance_to_structure, charge_mass)
        mic = max_instantaneous_charge(distance_to_structure, target_scaled_distance=target_sd)
        st.write(f"**Estimated PPV:** {ppv:.2f} mm/s")
        st.write(f"**Estimated Airblast:** {airblast_db:.2f} dB")
        st.write(f"**Maximum Instantaneous Charge (MIC):** {mic:.2f} kg")
        if ppv > 5.0:
            st.warning("PPV exceeds 5 mm/s guideline threshold.")
        if airblast_db > 133.0:
            st.warning("Airblast exceeds 133 dB guideline threshold.")

        total_cost = total_drilling_blasting_cost(
            ca=charge_mass * explosive_cost,
            cb=st.number_input("Drilling Cost", value=5000.0, key="drill_cost_opencast"),
            cd=st.number_input("Delay Cost", value=2500.0, key="delay_cost_opencast"),
            cdr=st.number_input("Auxiliary Cost", value=1500.0, key="aux_cost_opencast"),
        )
        st.write(f"**Cost per Tonne:** {cost_per_tonne(total_cost, tonnage):.2f}")

        points = np.array([
            (0.0, 0.0),
            (spacing, 0.0),
            (0.0, burden),
            (spacing, burden),
            (2 * spacing, 0.0),
            (2 * spacing, burden),
        ])
        st.plotly_chart(plot_blast_layout(points, title="Opencast Blast Layout"), use_container_width=True)

        opt_result = optimize_blast(rock, explosive, bench)
        st.write({"success": opt_result.success, "objective": opt_result.fun, "x": opt_result.x.tolist()})

elif method == "Underground (Tunneling)":
    st.title("Underground Blast Design & Pattern Generator")

    st.sidebar.subheader("Tunnel Parameters")
    tunnel_width = st.sidebar.number_input("Tunnel Width (m)", value=4.0)
    tunnel_height = st.sidebar.number_input("Tunnel Height (m)", value=4.0)
    rock_hardness = st.sidebar.number_input("Rock Hardness Coef (f)", value=10.0)
    advance = st.sidebar.number_input("Round Advance (m)", value=1.5)
    cut_type = st.selectbox("Select Cut Pattern", ["V-Cut", "Burn Cut"])

    tunnel = {
        "width": tunnel_width,
        "height": tunnel_height,
        "rock_hardness": rock_hardness,
        "cut_holes": 4,
        "outside_holes": 6,
        "contour_holes": 8,
        "tonnage": 300.0,
        "advance": advance,
    }
    explosive = {"energy_factor": 1.0, "fragmentation_factor": 1.0, "cost_per_kg": 3.5}
    design = UndergroundDesign(tunnel, explosive)

    if st.button("Generate Underground Pattern"):
        s_dr = design.face_area()
        q = design.specific_charge()
        hole_counts = design.hole_distribution()
        cut_points = design.v_cut_points() if cut_type == "V-Cut" else design.burn_cut_points()
        contour_points = design.contour_hole_points(spacing=0.6)
        points = np.vstack((cut_points, contour_points))

        st.write(f"**Cross-Sectional Area (S_dr):** {s_dr:.2f} m²")
        st.write(f"**Rock Constraining Factor:** {design.rock_constraining_factor():.2f}")
        st.write(f"**Estimated Specific Charge (q):** {q:.2f} kg/m³")
        st.write(f"**Estimated Total Blast Holes (N):** {hole_counts['N_total']}")
        estimated_charge_delay = max(q * s_dr / max(hole_counts["N_total"], 1), 0.1)
        ppv = ppv_usbm(estimated_charge_delay, distance_to_structure)
        airblast_db = airblast_overpressure(distance_to_structure, estimated_charge_delay)
        st.write(f"**PPV (USBM estimate):** {ppv:.2f}")
        st.write(f"**Estimated Airblast:** {airblast_db:.2f} dB")
        if ppv > 5.0:
            st.warning("PPV exceeds 5 mm/s guideline threshold.")
        if airblast_db > 133.0:
            st.warning("Airblast exceeds 133 dB guideline threshold.")
        st.write(f"**Flyrock Safety:** {flyrock_safety_margin(burden_m=1.0, stemming_m=1.6)}")

        adjusted_points = drill_deviation_model(points)
        layout = plot_blast_layout(adjusted_points, title=f"{cut_type} Layout Visualization")
        st.plotly_chart(layout, use_container_width=True)
        st.plotly_chart(plot_3d_layout(adjusted_points, title=f"{cut_type} 3D Layout"), use_container_width=True)

        st.write(delay_timing_simulation(rows=hole_counts["N_cut"], cols=1))

        st.write(optimize_underground(tunnel, explosive))

