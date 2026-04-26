# Blast Design Optimization for Hard Rock Critical Mineral Mining

This repository provides a Streamlit-based engineering application for blast design, pattern generation, and cost optimization across opencast and underground mining scenarios.

## Scope

- Opencast bench blast design calculations
- Underground tunnel blast planning (V-cut and burn-cut)
- Cost analysis and constrained optimization
- 2D and 3D blast hole visualization with Plotly
- Practical engineering checks:
	- Delay timing simulation
	- USBM-based PPV estimate
	- Flyrock stemming margin check
	- Drill deviation perturbation model
	- Kuz-Ram calibration against observed fragmentation

## Project Structure

```text
.
├── app.py
├── modules
│   ├── __init__.py
│   ├── cost_optimization.py
│   ├── opencast.py
│   ├── underground.py
│   └── visuals.py
├── pages
│   ├── 1_Opencast.py
│   ├── 2_Underground.py
│   └── 3_Cost_Optimization.py
└── requirements.txt
```

## Engineering Models Included

### Opencast

- Burden (Konya and Walter style metric form)
- Spacing, stemming, and subdrilling
- Charge per hole and powder factor
- Kuz-Ram fragmentation mean size $X_m$/$X_{50}$
- Uniformity index $n$ (Rosin-Rammler related)

### Underground

- Tunnel face area
- Rock constraining factor $k_{cons} = \frac{6.5}{\sqrt{S_{dr}}}$
- Specific charge estimation (Pokrovsky-style structure)
- Hole distribution accounting:
	- $N = N_{cut} + N_{out} + N_o$
- Geometric V-cut and burn-cut generation

### Cost and Optimization

- Total cost model:
	- $C_T = C_A + C_B + C_D + C_{DR}$
- Objective minimization with penalty constraints for:
	- Fragment size target
	- Uniformity index target

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Notes

- The formulas in this app are structured for engineering decision support and rapid scenario analysis.
- Field calibration (fragmentation sieving, vibration logs, geology class updates) should be performed before production deployment.