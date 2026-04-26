import streamlit as st

from modules.underground import UndergroundDesign
from modules.visuals import plot_blast_layout


st.set_page_config(page_title="Underground Blast Design", layout="wide")
st.title("Underground Blast Design")

tunnel = {"width": st.number_input("Tunnel width (m)", value=4.0), "height": st.number_input("Tunnel height (m)", value=4.0), "rock_hardness": st.number_input("Rock hardness", value=10.0)}
explosive = {"energy_factor": 1.0, "fragmentation_factor": 1.0}

design = UndergroundDesign(tunnel, explosive)

if st.button("Generate"):
    st.write({"face_area": design.face_area(), "specific_charge": design.specific_charge(), "holes": design.hole_distribution()})
    points = design.v_cut_points()
    st.plotly_chart(plot_blast_layout(points, "V-Cut Layout"), use_container_width=True)
