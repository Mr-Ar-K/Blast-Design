import numpy as np
import streamlit as st

from modules.cost_optimization import cost_per_tonne, optimize_blast, optimize_underground, total_drilling_blasting_cost
from modules.delay import row_wise_delay
from modules.flyrock import flyrock_risk_zone
from modules.fragmentation import distribution_curve, key_fragment_sizes
from modules.opencast import OpencastDesign, airblast_overpressure, max_allowable_charge_per_delay, max_instantaneous_charge, ppv
from modules.rock_mass import auto_adjustment_factors, calculate_rmr, estimate_gsi
from modules.simulation import simulate_burden_distribution
from modules.underground import UndergroundDesign, delay_timing_simulation, drill_deviation_model, flyrock_safety_margin, ppv_usbm
from modules.visuals import plot_3d_layout, plot_blast_layout, plot_delay_layout, plot_fragmentation_curve
from modules.cost_optimization import recommend_opencast_layout


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
        "Very close": 10,
        "Close": 20,
        "Moderate": 30,
        "Wide": 40,
    }
    jpo_options = {
        "Very unfavorable": 10,
        "Unfavorable": 20,
        "Intermediate": 30,
        "Favorable": 40,
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Rock & Mass Properties")
        rock_density = st.number_input("Rock Density (kg/m3)", value=2600.0)
        ucs_mpa = st.number_input("UCS (MPa)", value=120.0)
        youngs_modulus_gpa = st.number_input("Young's Modulus (GPa)", value=35.0)
        rmd_label = st.selectbox("Rock Mass Description (RMD)", list(rmd_options.keys()))
        jps_label = st.selectbox("Joint Plane Spacing (JPS)", list(jps_options.keys()))
        jpo_label = st.selectbox("Joint Plane Orientation (JPO)", list(jpo_options.keys()))

        with st.expander("RMR Inputs"):
            ucs_rating = st.slider("UCS rating", 0, 20, 12)
            rqd_rating = st.slider("RQD rating", 0, 20, 13)
            spacing_rating = st.slider("Joint spacing rating", 0, 20, 10)
            condition_rating = st.slider("Condition rating", 0, 30, 18)
            groundwater_rating = st.slider("Groundwater rating", 0, 10, 7)
            disturbance_factor = st.slider("Disturbance factor", 0.0, 10.0, 2.0, 0.5)

    with col2:
        st.subheader("Explosive Properties")
        exp_density = st.number_input("Explosive Density (kg/m3)", value=800.0)
        rws = st.number_input("Relative Weight Strength (ANFO=115)", value=115.0)
        explosive_cost = st.number_input("Explosive Cost per kg", value=65.0)

    with col3:
        st.subheader("Bench & Cost")
        hole_dia = st.number_input("Hole Diameter (mm)", value=150.0)
        bench_height = st.number_input("Bench Height (m)", value=10.0)
        tonnage = st.number_input("Tonnage (t)", value=1200.0)
        blast_length = st.number_input("Blast Length (m)", value=24.0)
        blast_width = st.number_input("Blast Width (m)", value=18.0)
        drilling_cost = st.number_input("Drilling Cost", value=5000.0, key="drill_cost_opencast")
        delay_cost = st.number_input("Delay Cost", value=2500.0, key="delay_cost_opencast")
        aux_cost = st.number_input("Auxiliary Cost", value=1500.0, key="aux_cost_opencast")

    rmr = calculate_rmr(ucs_rating, rqd_rating, spacing_rating, condition_rating, groundwater_rating)
    gsi = estimate_gsi(rmr, disturbance_factor)
    adjustments = auto_adjustment_factors(rmr, gsi)

    rock = {
        "density": rock_density,
        "rmr": rmr,
        "gsi": gsi,
    }
    explosive = {"density": exp_density, "rws": rws, "cost_per_kg": explosive_cost}
    bench = {
        "hole_diameter": hole_dia,
        "bench_height": bench_height,
        "drilling_cost_per_m": drilling_cost / max(bench_height, 1e-6),
        "accessories_cost": delay_cost + aux_cost,
    }
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
    st.caption(
        f"Calculated Cunningham A: {rock_factor_a:.2f} | "
        f"RMR {rmr:.1f}, GSI {gsi:.1f}, "
        f"geometry factor {adjustments['geometry_factor']:.2f}, "
        f"charging factor {adjustments['charging_factor']:.2f}"
    )

    if st.button("Generate Advanced Opencast Report", type="primary"):
        options_df, best_layout, best_points = recommend_opencast_layout(
            rock=rock,
            explosive=explosive,
            base_bench=bench,
            blast_length=blast_length,
            blast_width=blast_width,
            target_tonnage=tonnage,
            target_x50=35.0,
        )
        bench["hole_diameter"] = float(best_layout["Hole Dia (mm)"])
        design = OpencastDesign(rock, explosive, bench)
        summary = design.fragmentation_summary()
        charge_mass = summary["Charge per hole (kg)"]
        n_index = max(summary["Uniformity index (n)"], 0.2)
        sizes = key_fragment_sizes(summary["X50 / Xm (cm)"], n_index)
        curve_x, curve_y = distribution_curve(summary["X50 / Xm (cm)"], n_index)

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        total_cost = total_drilling_blasting_cost(
            ca=charge_mass * explosive_cost,
            cb=drilling_cost,
            cd=delay_cost,
            cdr=aux_cost,
        )
        kpi1.metric("Cost per Tonne", f"INR {cost_per_tonne(total_cost, tonnage):.2f}")
        kpi2.metric("X50", f"{summary['X50 / Xm (cm)']:.1f} cm")
        kpi3.metric("P80", f"{sizes['P80']:.1f} cm")
        kpi4.metric("Powder Factor", f"{summary['Powder factor (kg/m3)']:.2f} kg/m3")

        rec1, rec2, rec3 = st.columns(3)
        rec1.metric("Best Pattern", str(best_layout["Pattern"]))
        rec2.metric("Best Hole Size", f"{best_layout['Hole Dia (mm)']} mm")
        rec3.metric("Best Hole Count", f"{int(best_layout['Holes'])}")

        geo_col, env_col = st.columns(2)
        with geo_col:
            st.info(
                f"""
            Burden: {summary['Burden (m)']:.2f} m
            Spacing: {summary['Spacing (m)']:.2f} m
            Stemming: {summary['Stemming (m)']:.2f} m
            Subdrilling: {summary['Subdrilling (m)']:.2f} m
            Charge per hole: {charge_mass:.1f} kg
            """
            )

        with env_col:
            ppv_value = ppv(distance_to_structure, charge_mass, k=1140.0, n=1.6)
            airblast_db = airblast_overpressure(distance_to_structure, charge_mass)
            mic = max_instantaneous_charge(distance_to_structure, target_scaled_distance=target_sd)
            max_charge = max_allowable_charge_per_delay(5.0, distance_to_structure, k=1140.0, n=1.6)
            if ppv_value > 5.0:
                st.warning("Unsafe vibration level")
                st.error(f"PPV: {ppv_value:.2f} mm/s")
            else:
                st.success(f"PPV: {ppv_value:.2f} mm/s")

            if airblast_db > 133.0:
                st.error(f"Airblast: {airblast_db:.1f} dB")
            else:
                st.success(f"Airblast: {airblast_db:.1f} dB")

            st.caption(f"MIC: {mic:.2f} kg | Max charge/delay @ 5 mm/s: {max_charge:.2f} kg")
            flyrock = flyrock_risk_zone(summary["Burden (m)"], summary["Stemming (m)"], charge_mass)
            st.metric("Flyrock Risk", flyrock["risk"])
            st.caption(f"Flyrock radius: {flyrock['distance_m']:.1f} m")

        st.subheader("Fragmentation Distribution")
        frag_col1, frag_col2 = st.columns(2)
        with frag_col1:
            st.plotly_chart(plot_fragmentation_curve(curve_x, curve_y), use_container_width=True)
        with frag_col2:
            st.metric("P20", f"{sizes['P20']:.1f} cm")
            st.metric("P50", f"{sizes['P50']:.1f} cm")
            st.metric("P80", f"{sizes['P80']:.1f} cm")
            mc = simulate_burden_distribution(mean_burden=summary["Burden (m)"], std_burden=0.2, n=1000)
            st.caption(f"Monte Carlo burden mean: {mc['mean']:.2f} m")
            st.caption(f"Monte Carlo burden std: {mc['std']:.2f} m")
            st.caption(f"95% CI: {mc['ci95'][0]:.2f} to {mc['ci95'][1]:.2f} m")

        points = best_points
        delays = [event["delay_ms"] for event in row_wise_delay(int(best_layout["Rows"]), int(best_layout["Cols"]))]
        vis_col1, vis_col2 = st.columns(2)
        with vis_col1:
            st.plotly_chart(plot_blast_layout(points, title="Opencast Blast Layout"), use_container_width=True)
        with vis_col2:
            st.plotly_chart(plot_delay_layout(points, delays, title="Delay Timing Map"), use_container_width=True)

        st.subheader("Bench Pattern Alternatives")
        st.dataframe(options_df, use_container_width=True)

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

