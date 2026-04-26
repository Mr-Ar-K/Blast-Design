import numpy as np
import streamlit as st

from modules.opencast import OpencastDesign
from modules.visuals import plot_blast_layout


st.set_page_config(page_title="Opencast Blast Design", layout="wide")
st.title("Opencast Blast Design")

rock = {"density": st.number_input("Rock density (kg/m3)", value=2600.0), "rock_factor": st.number_input("Rock factor (A)", value=7.0)}
explosive = {"density": st.number_input("Explosive density (kg/m3)", value=800.0), "rws": st.number_input("Relative Weight Strength (ANFO=115)", value=115.0)}
bench = {"hole_diameter": st.number_input("Hole diameter (mm)", value=150.0), "bench_height": st.number_input("Bench height (m)", value=10.0)}

design = OpencastDesign(rock, explosive, bench)

if st.button("Calculate"):
    st.json(design.fragmentation_summary())
    points = np.array([[0, 0], [design.spacing(), 0], [0, design.burden()], [design.spacing(), design.burden()]])
    st.plotly_chart(plot_blast_layout(points, "Opencast Blast Layout"), use_container_width=True)
