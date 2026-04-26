import pandas as pd
import plotly.express as px
import streamlit as st

from modules.cost_optimization import generate_opencast_scenarios


st.set_page_config(page_title="Cost & Scenario Optimization", layout="wide")
st.title("Blast Scenario & Cost Optimization (INR ₹)")
st.markdown("Compare different drill hole diameters to find the most cost-effective blast pattern that meets your fragmentation targets.")

st.sidebar.header("Economic & Rock Inputs")
rock_density = st.sidebar.number_input("Rock Density (kg/m3)", value=2600.0)
rock_factor = st.sidebar.number_input("Rock Factor (A)", value=7.0)

exp_density = st.sidebar.number_input("Explosive Density (kg/m3)", value=800.0)
exp_cost = st.sidebar.number_input("Explosive Cost (₹/kg)", value=65.0)

bench_height = st.sidebar.number_input("Bench Height (m)", value=10.0)
drill_cost_m = st.sidebar.number_input("Drilling Cost (₹/meter)", value=450.0)
acc_cost = st.sidebar.number_input("Accessories Cost per Hole (₹)", value=1500.0)

target_x50 = st.sidebar.slider("Target Maximum Fragment Size X50 (cm)", 10.0, 50.0, 25.0)

rock = {"density": rock_density, "rock_factor": rock_factor}
explosive = {"density": exp_density, "rws": 115.0, "cost_per_kg": exp_cost}
base_bench = {
    "bench_height": bench_height,
    "drilling_cost_per_m": drill_cost_m,
    "accessories_cost": acc_cost,
}

if st.button("Run Scenario Optimization", type="primary"):
    df_results, best_case = generate_opencast_scenarios(rock, explosive, base_bench, target_x50)

    st.success("### Best Recommended Choice")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Optimal Hole Dia", f"{best_case['Hole Dia (mm)']} mm")
    col2.metric("Cost per Tonne", f"₹ {best_case['Cost per Tonne (₹)']}")
    col3.metric("Fragmentation (X50)", f"{best_case['Mean Fragment X50 (cm)']} cm")
    col4.metric("Powder Factor", f"{best_case['Powder Factor (kg/m3)']}")

    st.info(
        f"Why this is the best? It yields the lowest drilling and blasting cost "
        f"(₹{best_case['Cost per Tonne (₹)']}/t) while keeping the mean fragment "
        f"size under your target of {target_x50} cm."
    )
    if "Note" in best_case:
        st.warning(str(best_case["Note"]))

    st.subheader("Scenario Comparison Table")
    st.dataframe(df_results, use_container_width=True)

    st.subheader("Trade-off Analysis")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig1 = px.scatter(
            df_results,
            x="Mean Fragment X50 (cm)",
            y="Cost per Tonne (₹)",
            size="Hole Dia (mm)",
            color="Hole Dia (mm)",
            text="Hole Dia (mm)",
            title="Cost vs. Fragmentation Trade-off",
            labels={"Mean Fragment X50 (cm)": "Fragment Size X50 (cm)", "Cost per Tonne (₹)": "Cost per Tonne (₹)"},
        )
        fig1.add_vline(x=target_x50, line_dash="dash", line_color="red", annotation_text=f"Target < {target_x50}cm")
        fig1.update_traces(textposition="top center")
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        fig2 = px.bar(
            df_results,
            x="Hole Dia (mm)",
            y="Powder Factor (kg/m3)",
            color="Cost per Tonne (₹)",
            title="Powder Factor by Hole Diameter",
            text="Powder Factor (kg/m3)",
        )
        fig2.update_layout(xaxis_type="category")
        st.plotly_chart(fig2, use_container_width=True)

