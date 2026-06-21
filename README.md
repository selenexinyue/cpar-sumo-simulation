# CPAR SUMO Microsimulation — GDP10

Traffic microsimulation files, demand assumptions and KPI analysis for the
**Chattogram Port Access Road (CPAR)** study. This repository accompanies the group
report and lets readers reproduce the simulations and the key performance indicators
(KPIs).

The study compares four scenarios on the same corridor; the three 2048 scenarios use
an identical travel demand, so any difference in performance comes from the road
design, not the demand.

## Scenarios

| Folder | Scenario | Network |
|--------|----------|---------|
| `Baseline` | 2021 observed demand (reference / "today") | existing network |
| `Do-nothing` | 2048 demand, no upgrade | existing network |
| `Option1-ServiceLane` | 2048 demand, at-grade upgrade (service lanes + roundabouts) | upgraded network |
| `Option3-ElevatedRoad` | 2048 demand, elevated viaduct (grade-separated freight) | elevated network |

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
├── outputs/                       simulation outputs
│   └── <scenario>/Tripinfo.xml    per-trip results (incl. emissions)
│       <scenario>/SSM.xml         surrogate safety measures (conflicts)
└── scripts/
    └── extract_kpis.py            KPI extraction from the outputs
```

## Software

- **Eclipse SUMO 1.26**
- **Python 3** (standard library only — no extra packages needed)

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

KPIs are produced by `scripts/extract_kpis.py` from each scenario's `Tripinfo.xml`
and `SSM.xml`. It reports safety (conflicts, TTC incidents, hard-braking events),
congestion/efficiency (travel time, speed, delay — both for the N1↔Port corridor and
network-wide) and emissions (CO₂/NOₓ/PM, total and per VKT), over a 15–75 minute
analysis window. Emissions are read directly from `Tripinfo.xml`, so the large raw
`Emissions.xml.gz` files are not required.

Run it from the `scripts` folder, passing the scenario's output folder:

```bash
cd scripts
python3 extract_kpis.py ../outputs/Option1-ServiceLane
python3 extract_kpis.py ../outputs/Option3-ElevatedRoad
```

## Demand (OD matrix)

The travel demand is the group's own construction, built to match the client's
forecast of total corridor demand. The assumptions are in
`simulation/OD_Matrices.xlsx` and are realised as SUMO traffic flows in each
scenario's `.rou.xml`. The three 2048 scenarios share the same zone-to-zone demand
(N1 Junction, Bay Terminal, Chattogram Port, South), totalling 5,187 vehicles/hour.

## Notes

- The networks were derived from OpenStreetMap data and edited for each scenario;
  they are provided directly as `.net.xml` files.
- `Tripinfo.xml` already contains per-trip emissions, which is all the KPI analysis
  needs. The raw per-timestep `Emissions.xml.gz` files (~1.7 GB total) are not
  included here due to size; they can be regenerated with the `*_with_output.sumocfg`
  configs or shared separately on request.
