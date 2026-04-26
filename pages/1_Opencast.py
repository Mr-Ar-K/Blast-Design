import numpy as np
import streamlit as st

from modules.opencast import OpencastDesign, airblast_overpressure, max_instantaneous_charge
from modules.underground import ppv_usbm
from modules.visuals import plot_blast_layout
from modules.cost_optimization import total_drilling_blasting_cost, cost_per_tonne


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

    rock = {"density": rock_density}
    explosive = {"density": exp_density, "rws": rws, "cost_per_kg": exp_cost}
    bench = {"hole_diameter": hole_dia, "bench_height": bench_height}

    rmd_map = {"Powdery/Friable": 10, "Blocky": 20, "Jointed": 30, "Competent": 40, "Massive": 50}
    jps_map = {"Very close": 10, "Close": 20, "Moderate": 30, "Wide": 40}
    jpo_map = {"Very unfavorable": 10, "Unfavorable": 20, "Intermediate": 30, "Favorable": 40}

    design = OpencastDesign(rock, explosive, bench)
    rdi = 25.0 * (rock_density / 1000.0) - 50.0
    hardness = design.calculate_hardness_factor(ucs_mpa, youngs_modulus_gpa)
    rock_factor_a = design.calculate_rock_factor(rmd_map[rmd_label], jps_map[jps_label], jpo_map[jpo_label], rdi, hardness)

    if st.button("Generate Blast Report", type="primary"):
        summary = design.fragmentation_summary()
        charge_mass = summary["Charge per hole (kg)"]

        st.markdown("### Engineering Outcomes")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        total_cost = total_drilling_blasting_cost(charge_mass * exp_cost, drill_cost, delay_cost, aux_cost)
        cpt = cost_per_tonne(total_cost, tonnage)

        kpi1.metric("Cost per Tonne", f"INR {cpt:.2f}")
        kpi2.metric("Mean Fragment (X50)", f"{summary['X50 / Xm (cm)']:.1f} cm")
        kpi3.metric("Powder Factor", f"{summary['Powder factor (kg/m3)']:.2f} kg/m3")
        kpi4.metric("Cunningham Rock Factor", f"{rock_factor_a:.1f}")

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
            ppv = ppv_usbm(charge_mass, distance_to_structure)
            airblast_db = airblast_overpressure(distance_to_structure, charge_mass)
            mic = max_instantaneous_charge(distance_to_structure)

            if ppv > 5.0:
                st.error(f"PPV: {ppv:.2f} mm/s (Exceeds 5.0 Limit)")
            else:
                st.success(f"PPV: {ppv:.2f} mm/s (Safe)")

            if airblast_db > 133.0:
                st.error(f"Airblast: {airblast_db:.1f} dB (Exceeds 133 Limit)")
            else:
                st.success(f"Airblast: {airblast_db:.1f} dB (Safe)")

            st.caption(f"Maximum Instantaneous Charge (MIC): {mic:.2f} kg")

        st.markdown("#### Pattern Visualization")
        points = np.array([[0, 0], [design.spacing(), 0], [0, design.burden()], [design.spacing(), design.burden()]])
        st.plotly_chart(plot_blast_layout(points, "Bench Layout Profile"), use_container_width=True)
