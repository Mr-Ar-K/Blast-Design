import streamlit as st
import numpy as np

from modules.underground import UndergroundDesign, delay_timing_simulation, drill_deviation_model
from modules.opencast import airblast_overpressure
from modules.underground import ppv_usbm
from modules.reporting import generate_pdf_report
from modules.visuals import plot_blast_layout, plot_3d_layout, plot_delay_layout


st.set_page_config(page_title="Underground Blast Design", layout="wide")

st.title("Underground Tunnel Blast Engineering")
st.markdown("Design cut patterns, optimize specific charge, and sequence delays for tunnel drivage.")
st.divider()

tab1, tab2, tab3 = st.tabs(["1. Tunnel Geometry", "2. Rock & Explosives", "3. Blast Pattern Report"])

with tab1:
    st.subheader("Tunnel Profile")
    col1, col2 = st.columns(2)
    with col1:
        tunnel_width = st.number_input("Tunnel Width (m)", value=4.5, step=0.5)
        tunnel_height = st.number_input("Tunnel Height (m)", value=4.5, step=0.5)
        advance = st.number_input("Expected Round Advance (m)", value=3.0, step=0.1)
    with col2:
        cut_type = st.selectbox("Select Cut Pattern", ["V-Cut", "Burn Cut"])
        distance_to_surface = st.slider("Distance to Surface / Infrastructure (m)", 10.0, 500.0, 100.0)

with tab2:
    st.subheader("Geomechanics & Energy")
    col3, col4 = st.columns(2)
    with col3:
        rock_hardness = st.number_input("Rock Hardness Coefficient (f) - Protodyakonov", value=10.0, step=1.0)
        rock_density = st.number_input("Rock Density (kg/m3)", value=2700.0, step=50.0)
    with col4:
        exp_cost = st.number_input("Explosive Cost (INR/kg)", value=65.0, step=1.0)
        energy_factor = st.slider("Explosive Energy Factor (e)", 0.5, 1.5, 1.0)

with tab3:
    tunnel = {
        "width": tunnel_width,
        "height": tunnel_height,
        "rock_hardness": rock_hardness,
        "cut_holes": 6,
        "outside_holes": 12,
        "contour_holes": 16,
    }
    explosive = {"energy_factor": energy_factor, "fragmentation_factor": 1.0, "cost_per_kg": exp_cost}

    design = UndergroundDesign(tunnel, explosive)

    if st.button("Generate Underground Pattern", type="primary"):
        s_dr = design.face_area()
        q = design.specific_charge()
        total_tonnage = s_dr * advance * (rock_density / 1000)
        total_explosives = q * s_dr * advance

        st.markdown("### Tunnel Drivage Outcomes")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        kpi1.metric("Total Explosives", f"{total_explosives:.1f} kg")
        kpi2.metric("Specific Charge (q)", f"{q:.2f} kg/m3")
        kpi3.metric("Tonnage per Round", f"{total_tonnage:.1f} t")
        kpi4.metric("Est. Explosive Cost", f"INR {total_explosives * exp_cost:,.2f}")

        st.divider()

        hole_counts = design.hole_distribution()
        cut_points = design.v_cut_points() if cut_type == "V-Cut" else design.burn_cut_points()
        contour_points = design.contour_hole_points(spacing=0.6)
        points = np.vstack((cut_points, contour_points))
        adjusted_points = drill_deviation_model(points, deviation_std_m=0.05)

        col_geo, col_safe = st.columns(2)
        with col_geo:
            st.markdown("#### Blast Hole Distribution")
            st.info(
                f"""
            - Cut Holes: {hole_counts['N_cut']}
            - Reliever/Outside Holes: {hole_counts['N_out']}
            - Contour/Perimeter Holes: {hole_counts['N_o']}
            - Total Holes: {len(points)} (Visualized)
            """
            )

        with col_safe:
            st.markdown("#### Vibration Compliance")
            est_charge_per_delay = (total_explosives / max(len(points), 1)) * 3
            ppv = ppv_usbm(est_charge_per_delay, distance_to_surface)
            airblast_db = airblast_overpressure(distance_to_surface, est_charge_per_delay)

            if ppv > 5.0:
                st.error(f"PPV: {ppv:.2f} mm/s (High Vibration Risk)")
            else:
                st.success(f"PPV: {ppv:.2f} mm/s (Safe)")

            if airblast_db > 133.0:
                st.error(f"Airblast: {airblast_db:.1f} dB (Above 133 dB)")
            else:
                st.success(f"Airblast: {airblast_db:.1f} dB (Safe)")

        st.markdown("#### Drill & Delay Sequence")
        delay_events = delay_timing_simulation(rows=max(hole_counts["N_cut"], 1), cols=1, inter_row_ms=25, inter_hole_ms=0)
        delays = [i * 25 for i in range(len(adjusted_points))]

        vis_col1, vis_col2 = st.columns(2)
        with vis_col1:
            st.plotly_chart(plot_blast_layout(adjusted_points, f"{cut_type} Profile"), use_container_width=True)
            st.caption(f"Delay events preview: {delay_events[:5]}")
        with vis_col2:
            st.plotly_chart(plot_delay_layout(adjusted_points, delays, "Delay Map (ms)"), use_container_width=True)
            st.plotly_chart(plot_3d_layout(adjusted_points, f"{cut_type} 3D Pattern"), use_container_width=True)

        st.markdown("#### Field Operations")
        kpi_dict = {
            "Specific Charge (kg/m3)": f"{q:.2f}",
            "Total Explosives (kg)": f"{total_explosives:.1f}",
            "Tonnage per Round (t)": f"{total_tonnage:.1f}",
            "Estimated Cost (INR)": f"{total_explosives * exp_cost:,.2f}",
        }
        geo_dict = {
            "Tunnel Width (m)": tunnel_width,
            "Tunnel Height (m)": tunnel_height,
            "Advance (m)": advance,
            "Cut Type": cut_type,
            "Visualized Holes": len(points),
            "Estimated Charge/Delay (kg)": f"{est_charge_per_delay:.1f}",
        }

        pdf_path = generate_pdf_report("Underground Tunnel Blast", kpi_dict, geo_dict)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Underground Blast Report (PDF)",
                data=pdf_file,
                file_name="Underground_Blast_Report.pdf",
                mime="application/pdf",
                type="primary",
            )

