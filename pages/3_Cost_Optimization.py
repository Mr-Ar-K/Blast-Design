import streamlit as st

from modules.cost_optimization import optimize_blast


st.set_page_config(page_title="Cost Optimization", layout="wide")
st.title("Blast Cost Optimization")

rock = {"density": 2600.0, "compressive_strength": 100.0, "rock_factor": 7.0}
explosive = {"density": 800.0, "rws": 115.0, "cost_per_kg": 3.5}
bench = {"hole_diameter": 150.0, "bench_height": 10.0, "drilling_cost": 5000.0, "delay_cost": 2500.0, "support_cost": 1500.0}

if st.button("Run Optimization"):
    result = optimize_blast(rock, explosive, bench)
    st.write({"success": result.success, "objective": result.fun, "x": result.x.tolist()})
