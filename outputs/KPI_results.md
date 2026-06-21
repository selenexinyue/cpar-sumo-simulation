# KPI Results (SPF Framework)

These results are produced by `scripts/kpi_extract.py` from the simulation outputs
in this folder (`SSM.xml` + `Tripinfo.xml` for each scenario). Emissions
(CO₂/NOₓ/PM) are read directly from `Tripinfo.xml`, so the raw per-timestep
`Emissions.xml.gz` files are not required to reproduce these numbers.

## Raw KPIs per scenario

| KPI | Baseline (2022) | Do-nothing | Option 1 | Option 3 |
|-----|-----------------|------------|----------|----------|
| TTC incidents (safety, lower better) | 2,829 | 18,127 | 9,726 | 8,104 |
| DRAC incidents (safety, lower better) | 220 | 5,344 | 4,926 | 3,986 |
| Avg effective speed (m/s, higher better) | 3.52 | 2.04 | 3.51 | 3.87 |
| Avg delay (s, lower better) | 1,665.8 | 4,414.4 | 2,153.8 | 1,851.5 |
| 95th-pct travel time (s, lower better) | 4,769 | 9,864 | 6,535 | 5,322 |
| CO₂ (kg, lower better) | 25,650 | 101,545 | 52,831 | 53,622 |
| NOₓ (kg, lower better) | 158.3 | 715.0 | 338.5 | 328.0 |
| PM (kg, lower better) | 1.43 | 8.48 | 3.42 | 3.27 |
| Vehicles completed | 2,115 | 5,214 | 5,222 | 5,225 |

*Avg effective speed and delay include entry (insertion) waiting time. Baseline uses
2022 observed demand and is shown for reference; the SPF score below compares the
three 2040 scenarios.*

## SPF score (2040 scenarios)

Each KPI is normalised 0–100 across the three 2040 options and combined with the
SPF weights (safety 40%, congestion 30%, emissions 30%). Higher is better.

| Scenario | SPF score |
|----------|-----------|
| **Option 3 (elevated)** | **99.8** |
| Option 1 (at-grade) | 76.5 |
| Do-nothing | 0.0 |

Option 3 is best on safety, congestion and emissions; Option 1 only edges Option 3
on CO₂. To regenerate, see the commands in the repository `README.md`.
