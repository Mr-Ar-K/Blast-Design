import numpy as np
import streamlit as st

from modules.delay import row_wise_delay
from modules.flyrock import flyrock_risk_zone
from modules.fragmentation import distribution_curve, key_fragment_sizes
from modules.opencast import OpencastDesign, airblast_overpressure, max_allowable_charge_per_delay, max_instantaneous_charge, ppv
from modules.rock_mass import auto_adjustment_factors, calculate_rmr, estimate_gsi
from modules.simulation import simulate_burden_distribution
from modules.visuals import plot_blast_layout, plot_delay_layout, plot_fragmentation_curve
from modules.cost_optimization import recommend_opencast_layout, total_drilling_blasting_cost, cost_per_tonne
from modules.reporting import generate_pdf_report


st.set_page_config(page_title="Opencast Blast Design", layout="wide")
st.title("Opencast Blast Engineering")
st.markdown(
    """
Optimize hard rock fragmentation while ensuring strict environmental compliance.
Complete the parameters below, then generate your blast report.
"""
)
st.divider()

tab1, tab2, tab3 = st.tabs(["1. Geometry & Economics", "2. Geomechanics", "3. Blast Report"])

with tab1:
    st.subheader("Bench & Economic Parameters")
    col1, col2 = st.columns(2)
    with col1:
        bench_height = st.number_input("Bench Height (m)", value=10.0, step=0.5)
        hole_dia = st.number_input("Hole Diameter (mm)", value=150.0, step=5.0)
        tonnage = st.number_input("Target Tonnage (t)", value=1200.0, step=100.0)
        blast_length = st.number_input("Blast Length (m)", value=24.0, step=1.0)
        blast_width = st.number_input("Blast Width (m)", value=18.0, step=1.0)
    with col2:
        drill_cost = st.number_input("Drilling Cost (INR)", value=5000.0, step=500.0)
        delay_cost = st.number_input("Delay/Accessories Cost (INR)", value=2500.0, step=500.0)
        aux_cost = st.number_input("Auxiliary Cost (INR)", value=1500.0, step=500.0)

    st.subheader("Environmental Limits")
    distance_to_structure = st.slider("Distance to Nearest Structure (m)", 50.0, 1000.0, 250.0)

with tab2:
    st.subheader("Rock & Explosive Properties")
    col3, col4 = st.columns(2)
    with col3:
        rock_density = st.number_input("Rock Density (kg/m3)", value=2600.0, step=50.0)
        ucs_mpa = st.number_input("UCS (MPa)", value=120.0, step=10.0)
        youngs_modulus_gpa = st.number_input("Young's Modulus (GPa)", value=35.0, step=1.0)

        with st.expander("Rock Mass Rating Inputs"):
            ucs_rating = st.slider("RMR component: UCS rating", 0, 20, 12)
            rqd_rating = st.slider("RMR component: RQD rating", 0, 20, 13)
            spacing_rating = st.slider("RMR component: Joint spacing rating", 0, 20, 10)
            condition_rating = st.slider("RMR component: Condition rating", 0, 30, 18)
            groundwater_rating = st.slider("RMR component: Groundwater rating", 0, 10, 7)
            disturbance_factor = st.slider("Disturbance factor", 0.0, 10.0, 2.0, 0.5)

        with st.expander("Advanced Structural Parameters (Rock Mass)"):
            rmd_label = st.selectbox("Rock Mass Description", ["Powdery/Friable", "Blocky", "Jointed", "Competent", "Massive"], index=2)
            jps_label = st.selectbox("Joint Plane Spacing", ["Very close", "Close", "Moderate", "Wide"], index=2)
            jpo_label = st.selectbox("Joint Plane Orientation", ["Very unfavorable", "Unfavorable", "Intermediate", "Favorable"], index=2)

    with col4:
        exp_density = st.number_input("Explosive Density (kg/m3)", value=800.0, step=50.0)
        rws = st.number_input("Relative Weight Strength (ANFO=115)", value=115.0, step=1.0)
        exp_cost = st.number_input("Explosive Cost (INR/kg)", value=65.0, step=1.0)

with tab3:
    st.subheader("Actionable Blast Plan")

    rmr = calculate_rmr(ucs_rating, rqd_rating, spacing_rating, condition_rating, groundwater_rating)
    gsi = estimate_gsi(rmr, disturbance_factor)
    adjustment_factors = auto_adjustment_factors(rmr, gsi)

    rock = {"density": rock_density, "rmr": rmr, "gsi": gsi}
    explosive = {"density": exp_density, "rws": rws, "cost_per_kg": exp_cost}
    bench = {
        "hole_diameter": hole_dia,
        "bench_height": bench_height,
        "drilling_cost_per_m": drill_cost / max(bench_height, 1e-6),
        "accessories_cost": delay_cost + aux_cost,
    }

    rmd_map = {"Powdery/Friable": 10, "Blocky": 20, "Jointed": 30, "Competent": 40, "Massive": 50}
    jps_map = {"Very close": 10, "Close": 20, "Moderate": 30, "Wide": 40}
    jpo_map = {"Very unfavorable": 10, "Unfavorable": 20, "Intermediate": 30, "Favorable": 40}

    design = OpencastDesign(rock, explosive, bench)
    rdi = 25.0 * (rock_density / 1000.0) - 50.0
    hardness = design.calculate_hardness_factor(ucs_mpa, youngs_modulus_gpa)
    rock_factor_a = design.calculate_rock_factor(rmd_map[rmd_label], jps_map[jps_label], jpo_map[jpo_label], rdi, hardness)

    if st.button("Generate Blast Report", type="primary"):
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

        frag_sizes = key_fragment_sizes(summary["X50 / Xm (cm)"], n_index)
        sizes_curve, passing_curve = distribution_curve(summary["X50 / Xm (cm)"], n_index)

        st.markdown("### Engineering Outcomes")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        total_cost = total_drilling_blasting_cost(charge_mass * exp_cost, drill_cost, delay_cost, aux_cost)
        cpt = cost_per_tonne(total_cost, tonnage)

        kpi1.metric("Cost per Tonne", f"INR {cpt:.2f}")
        kpi2.metric("Mean Fragment (X50)", f"{summary['X50 / Xm (cm)']:.1f} cm")
        kpi3.metric("Powder Factor", f"{summary['Powder factor (kg/m3)']:.2f} kg/m3")
        kpi4.metric("Cunningham Rock Factor", f"{rock_factor_a:.1f}")

        rec1, rec2, rec3 = st.columns(3)
        rec1.metric("Best Pattern", str(best_layout["Pattern"]))
        rec2.metric("Best Hole Size", f"{best_layout['Hole Dia (mm)']} mm")
        rec3.metric("Best Hole Count", f"{int(best_layout['Holes'])}")

        st.caption(
            f"Rock context: RMR {rmr:.1f}, GSI {gsi:.1f}, "
            f"geometry factor {adjustment_factors['geometry_factor']:.2f}, "
            f"charging factor {adjustment_factors['charging_factor']:.2f}"
        )

        st.divider()

        col_geo, col_safe = st.columns(2)
        with col_geo:
            st.markdown("#### Drill Pattern Geometry")
            st.info(
                f"""
            - Burden: {summary['Burden (m)']:.2f} m
            - Spacing: {summary['Spacing (m)']:.2f} m
            - Stemming: {summary['Stemming (m)']:.2f} m
            - Subdrilling: {summary['Subdrilling (m)']:.2f} m
            - Charge/Hole: {charge_mass:.1f} kg
            """
            )

        with col_safe:
            st.markdown("#### Environmental Compliance")
            ppv_value = ppv(distance_to_structure, charge_mass, k=1140.0, n=1.6)
            airblast_db = airblast_overpressure(distance_to_structure, charge_mass)
            mic = max_instantaneous_charge(distance_to_structure)
            max_charge_ppv = max_allowable_charge_per_delay(5.0, distance_to_structure, k=1140.0, n=1.6)

            if ppv_value > 5.0:
                st.warning("Unsafe vibration level")
                st.error(f"PPV: {ppv_value:.2f} mm/s (Exceeds 5.0 Limit)")
            else:
                st.success(f"PPV: {ppv_value:.2f} mm/s (Safe)")

            if airblast_db > 133.0:
                st.error(f"Airblast: {airblast_db:.1f} dB (Exceeds 133 Limit)")
            else:
                st.success(f"Airblast: {airblast_db:.1f} dB (Safe)")

            st.caption(f"Maximum Instantaneous Charge (MIC): {mic:.2f} kg")
            st.caption(f"Max allowable charge per delay @ 5 mm/s: {max_charge_ppv:.2f} kg")

            flyrock = flyrock_risk_zone(summary["Burden (m)"], summary["Stemming (m)"], charge_mass)
            st.metric("Flyrock Risk", flyrock["risk"])
            st.caption(f"Estimated flyrock radius: {flyrock['distance_m']:.1f} m")

        st.markdown("#### Fragmentation Distribution")
        frag_col1, frag_col2 = st.columns(2)
        with frag_col1:
            st.plotly_chart(plot_fragmentation_curve(sizes_curve, passing_curve), use_container_width=True)
        with frag_col2:
            st.metric("P20", f"{frag_sizes['P20']:.1f} cm")
            st.metric("P80", f"{frag_sizes['P80']:.1f} cm")
            mc = simulate_burden_distribution(mean_burden=summary["Burden (m)"], std_burden=0.2, n=1000)
            st.caption(f"Monte Carlo burden mean: {mc['mean']:.2f} m")
            st.caption(f"Monte Carlo burden std: {mc['std']:.2f} m")
            st.caption(f"95% confidence band: {mc['ci95'][0]:.2f} to {mc['ci95'][1]:.2f} m")

        st.markdown("#### Pattern Visualization")
        points = best_points
        delay_plan = row_wise_delay(int(best_layout["Rows"]), int(best_layout["Cols"]), inter_row_ms=42, inter_hole_ms=17)
        delays = [entry["delay_ms"] for entry in delay_plan]
        vis_col1, vis_col2 = st.columns(2)
        with vis_col1:
            st.plotly_chart(plot_blast_layout(points, "Bench Layout Profile"), use_container_width=True)
        with vis_col2:
            st.plotly_chart(plot_delay_layout(points, delays, "Delay Timing Map"), use_container_width=True)

        st.markdown("#### Bench Pattern Alternatives")
        st.dataframe(options_df, use_container_width=True)

        st.markdown("#### Field Operations")
        kpi_dict = {
            "Target Tonnage (t)": tonnage,
            "Cost per Tonne (INR)": f"{cpt:.2f}",
            "Mean Fragment X50 (cm)": f"{summary['X50 / Xm (cm)']:.1f}",
            "Powder Factor (kg/m3)": f"{summary['Powder factor (kg/m3)']:.2f}",
        }
        geo_dict = {
            "Hole Diameter (mm)": bench["hole_diameter"],
            "Burden (m)": f"{summary['Burden (m)']:.2f}",
            "Spacing (m)": f"{summary['Spacing (m)']:.2f}",
            "Stemming (m)": f"{summary['Stemming (m)']:.2f}",
            "Subdrilling (m)": f"{summary['Subdrilling (m)']:.2f}",
            "Charge per Hole (kg)": f"{charge_mass:.1f}",
        }

        pdf_path = generate_pdf_report("Opencast Bench Layout", kpi_dict, geo_dict)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Blast Plan (PDF)",
                data=pdf_file,
                file_name="Blast_Plan_Report.pdf",
                mime="application/pdf",
                type="primary",
            )

