# Blast Design Optimization for Hard Rock Critical Mineral Mining

This repository contains a Streamlit-based engineering decision-support application for blasting in opencast and underground operations.

The app combines blast geometry, rock-mass intelligence, environmental compliance checks, cost optimization, and scenario analysis.

## Key Capabilities

- Opencast blast design with dynamic Cunningham rock factor.
- Rock mass context integration using RMR, GSI, and adjustment factors.
- Bench pattern optimization across multiple layouts and hole diameters.
- Fragmentation modeling with Kuz-Ram plus Rosin-Rammler distribution.
- P20, P50, and P80 fragmentation outputs for crusher/plant alignment.
- Vibration, airblast, MIC, and allowable charge-per-delay estimates.
- Flyrock risk prediction and risk-zone radius reporting.
- Delay timing sequence generation and delay heat-map visualization.
- Monte Carlo simulation for burden uncertainty and confidence bands.
- Underground cut/contour pattern support and specific-charge estimation.
- Underground tabbed dashboard for tunnel drivage planning.
- One-click PDF blast report export for opencast and underground plans.

## Project Structure

```text
.
├── app.py
├── modules
│   ├── __init__.py
│   ├── cost_optimization.py
│   ├── delay.py
│   ├── flyrock.py
│   ├── fragmentation.py
│   ├── opencast.py
│   ├── rock_mass.py
│   ├── simulation.py
│   ├── underground.py
│   ├── reporting.py
│   └── visuals.py
├── pages
│   ├── 1_Opencast.py
│   ├── 2_Underground.py
│   └── 3_Cost_Optimization.py
└── requirements.txt
```

## Engineering Modules

### modules/opencast.py

- Burden and spacing calculation with rock-mass adjustment.
- Stemming, subdrilling, charge-per-hole, and powder factor.
- Kuz-Ram mean fragment size (X50/Xm) and uniformity index.
- Cunningham rock factor from geology descriptors.
- Environmental helpers:
	- Scaled distance and airblast overpressure.
	- Peak particle velocity (PPV).
	- Maximum instantaneous charge (MIC).
	- Maximum allowable charge per delay.

### modules/rock_mass.py

- RMR calculation from rating components.
- GSI estimation from RMR and disturbance.
- Auto-adjustment factors for geometry and charging.

### modules/fragmentation.py

- Rosin-Rammler passing function.
- Full size-distribution curve generation.
- Fragment size percentiles (P20, P50, P80).

### modules/cost_optimization.py

- Cost functions (`cost_per_tonne`, `cost_per_cubic_meter`).
- Opencast and underground optimization routines.
- Scenario generation across standard hole diameters.
- Bench layout recommendation across patterns:
	- Square
	- Staggered
	- Triangular
	- Echelon

### modules/delay.py

- Row-wise delay schedule generation.
- V-cut sequence timing.
- Delay scatter data assembly.

### modules/flyrock.py

- Flyrock distance estimate.
- Risk-zone classification (LOW, MEDIUM, HIGH).

### modules/simulation.py

- Monte Carlo burden simulation.
- Confidence interval calculation.
- Distribution summary (mean, std, CI).

### modules/reporting.py

- PDF report generator for field-ready blast plans.
- Executive KPI and geometry section export.
- Used by opencast and underground Streamlit pages.

### modules/visuals.py

- Blast layout plot (2D).
- Underground layout plot (3D).
- Fragmentation curve plot.
- Delay timing map (color coded).

## Streamlit Pages

- `app.py`: main entry with opencast and underground workflows.
- `pages/1_Opencast.py`: advanced opencast report workflow.
- `pages/2_Underground.py`: tabbed underground dashboard with delay map and compliance checks.
- `pages/3_Cost_Optimization.py`: scenario and trade-off analysis.

## Reporting

- Opencast page supports PDF download for bench blast plan.
- Underground page supports PDF download for tunnel blast plan.
- Main `app.py` route also includes underground PDF export.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

If port 8501 is already in use, run:

```bash
streamlit run app.py --server.port 8502
```

## Practical Notes

- Model outputs are intended for engineering screening and optimization support.
- Always calibrate with site field data before production use:
	- Fragmentation measurements (sieving/image analysis)
	- Vibration monitoring logs
	- Geology/rock-mass mapping updates
	- Cost and productivity reconciliation