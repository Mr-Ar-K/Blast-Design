import numpy as np
import streamlit as st

from modules.opencast import OpencastDesign, airblast_overpressure, max_instantaneous_charge
from modules.underground import ppv_usbm
from modules.visuals import plot_blast_layout


st.set_page_config(page_title="Opencast Blast Design", layout="wide")
st.title("Opencast Blast Design")

distance_to_structure = st.sidebar.slider("Distance to Nearest Structure (m)", min_value=10.0, max_value=2000.0, value=250.0, step=5.0)
target_sd = st.sidebar.slider("Target Scaled Distance (m/kg^0.5)", min_value=5.0, max_value=50.0, value=22.0, step=0.5)

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

rock_density = st.number_input("Rock density (kg/m3)", value=2600.0)
ucs_mpa = st.number_input("UCS (MPa)", value=120.0)
youngs_modulus_gpa = st.number_input("Young's Modulus (GPa)", value=35.0)
rmd_label = st.selectbox("Rock Mass Description (RMD)", list(rmd_options.keys()))
jps_label = st.selectbox("Joint Plane Spacing (JPS)", list(jps_options.keys()))
jpo_label = st.selectbox("Joint Plane Orientation (JPO)", list(jpo_options.keys()))

rock = {"density": rock_density}
explosive = {"density": st.number_input("Explosive density (kg/m3)", value=800.0), "rws": st.number_input("Relative Weight Strength (ANFO=115)", value=115.0)}
bench = {"hole_diameter": st.number_input("Hole diameter (mm)", value=150.0), "bench_height": st.number_input("Bench height (m)", value=10.0)}

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

if st.button("Calculate"):
    summary = design.fragmentation_summary()
    st.json(summary)

    charge_mass = summary["Charge per hole (kg)"]
    ppv = ppv_usbm(charge_mass, distance_to_structure)
    airblast_db = airblast_overpressure(distance_to_structure, charge_mass)
    mic = max_instantaneous_charge(distance_to_structure, target_scaled_distance=target_sd)
    st.write(f"Estimated PPV: {ppv:.2f} mm/s")
    st.write(f"Estimated Airblast: {airblast_db:.2f} dB")
    st.write(f"Maximum Instantaneous Charge (MIC) for SD target: {mic:.2f} kg")
    if ppv > 5.0:
        st.warning("PPV exceeds 5 mm/s guideline threshold.")
    if airblast_db > 133.0:
        st.warning("Airblast exceeds 133 dB guideline threshold.")

    points = np.array([[0, 0], [design.spacing(), 0], [0, design.burden()], [design.spacing(), design.burden()]])
    st.plotly_chart(plot_blast_layout(points, "Opencast Blast Layout"), use_container_width=True)
