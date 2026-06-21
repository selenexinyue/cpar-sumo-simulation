# CPAR SUMO Microsimulation — GDP10

Traffic microsimulation files, demand assumptions and KPI analysis for the
**Chattogram Port Access Road (CPAR)** study. This repository accompanies the group
report and lets readers reproduce the simulations and the key performance indicators
(KPIs).

The study compares four scenarios on the same corridor; the three 2040 scenarios use
an identical travel demand, so any difference in performance comes from the road
design, not the demand.

## Scenarios

| Folder | Scenario | Network |
|--------|----------|---------|
| `Baseline` | 2022 observed demand (reference / "today") | existing network |
| `Do-nothing` | 2040 demand, no upgrade | existing network |
| `Option1-ServiceLane` | 2040 demand, at-grade upgrade (service lanes + roundabouts) | upgraded network |
| `Option3-ElevatedRoad` | 2040 demand, elevated viaduct (grade-separated freight) | elevated network |

## Repository structure

```
cpar-sumo-simulation/
├── simulation/                    SUMO input files (run these)
│   ├── OD_Matrices.xlsx           demand assumptions (see "Demand" below)
│   ├── Background.poly.xml        OSM background polygons (optional, for visuals)
│   ├── Baseline/                  net + routes + config + toll + view
│   ├── Do-nothing/
│   ├── Option1-ServiceLane/
│   └── Option3-ElevatedRoad/
├── outputs/                       simulation outputs + KPI results
│   ├── <scenario>/Tripinfo.xml    per-trip results (incl. emissions)
│   ├── <scenario>/SSM.xml         surrogate safety measures (conflicts)
│   └── KPI_results.md             computed KPIs and SPF scores
└── scripts/
    └── kpi_extract.py             KPI / SPF extraction from the outputs
```

## Software

- **Eclipse SUMO 1.26**
- **Python 3** (standard library only — no extra packages needed for `kpi_extract.py`)

## How to run a scenario

Open the scenario's `.sumocfg` in `sumo-gui`, or from the scenario folder:

```bash
sumo -c Option1.sumocfg            # headless
sumo-gui -c Option1.sumocfg        # with GUI
```

Each run stops automatically once the network clears.

To **regenerate the output files** (Tripinfo / Emissions / SSM), run the
`*_with_output.sumocfg` variant instead, e.g.:

```bash
sumo -c Option1_with_output.sumocfg
```

This writes the outputs to an `Output/` subfolder.

## Reproducing the KPIs

KPIs and the combined SPF score are produced by `scripts/kpi_extract.py` from each
scenario's `SSM.xml` and `Tripinfo.xml`. Emissions (CO₂/NOₓ/PM) are read directly
from `Tripinfo.xml`, so the large raw `Emissions.xml.gz` files are **not** required.

Extract the 8 KPIs for one scenario:

```bash
python3 scripts/kpi_extract.py outputs/Option1-ServiceLane/SSM.xml \
                               outputs/Option1-ServiceLane/Tripinfo.xml Option1
```

Reproduce the full SPF comparison (Do-nothing / Option 1 / Option 3):

```python
import sys; sys.path.insert(0, "scripts")
import kpi_extract as K

base = "outputs"
scen = {"Do-nothing": "Do-nothing",
        "Option1":    "Option1-ServiceLane",
        "Option3":    "Option3-ElevatedRoad"}
vals = {name: K.extract(f"{base}/{f}/SSM.xml", f"{base}/{f}/Tripinfo.xml", name)
        for name, f in scen.items()}
K.kpi_score(vals)
```

The resulting scores are recorded in [`outputs/KPI_results.md`](outputs/KPI_results.md)
(Option 3 ≈ 99.8, Option 1 ≈ 76.5, Do-nothing ≈ 0.0).

## Demand (OD matrix)

The travel demand is the group's own construction, built to match the client's
forecast of total corridor demand. The assumptions are in
`simulation/OD_Matrices.xlsx` and are realised as SUMO traffic flows in each
scenario's `.rou.xml`. The three 2040 scenarios share the same zone-to-zone demand
(N1 Junction, Bay Terminal, Chattogram Port, South).

## Notes

- The networks were derived from OpenStreetMap and refined in **netedit**; they are
  provided directly as `.net.xml` files (there is no build script for the final
  networks).
- `Tripinfo.xml` already contains per-trip emissions, which is all the KPI analysis
  needs. The raw per-timestep `Emissions.xml.gz` files (~1.7 GB total) are not
  included here due to size; they can be regenerated with the `*_with_output.sumocfg`
  configs or shared separately on request.
