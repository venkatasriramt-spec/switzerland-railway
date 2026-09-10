# Project History

A chronological log of how the ARTEMIS Switzerland project evolved, from initial concept to the current data pipeline.

---

## Background — The ARTEMIS Project

This project is part of the broader **ARTEMIS** (Automated Railway Transport Energy Modelling and Infrastructure System) initiative. Prior work on ARTEMIS focused on training energy consumption models and visualization for railway systems. The Switzerland edition represents a fresh start with the goal of building a comprehensive, real-world railway data pipeline for the entire Swiss rail network.

The earlier ARTEMIS codebase (located in a separate `ARTEMIS` repository) had gone through two major versions. Version 2 introduced improvements to the modelling and visualization pipeline, including weight export scripts. The Switzerland edition was created as a standalone project to focus specifically on Swiss railway data collection and preparation.

---

## Timeline

### 7 September 2026 — Project Initialization & Core Pipeline

**Objective:** Collect comprehensive data about Switzerland's railway system — tracks, stations, schedules, and train characteristics.

#### Phase 1: Infrastructure & Geographic Data
- Created `01_download_infrastructure.py` to fetch the latest OpenStreetMap `.pbf` extract for Switzerland (~520 MB) from Geofabrik.
- Created `02_extract_tracks_and_stations.py` to parse the OSM data using `pyrosm`, extracting rail track geometries and station locations into GeoJSON format.

#### Phase 2: Schedule Data (API)
- Created `03_fetch_schedules.py` to pull live departure boards from the Swiss Open Transport API (`transport.opendata.ch`) for 9 major railway hubs: Zürich HB, Bern, Basel SBB, Genève, Lausanne, Luzern, Winterthur, St. Gallen, and Lugano.
- This produced a CSV snapshot capturing train categories (S, IC, IR, RE, etc.), train numbers, operators, platforms, departure times, and destinations.

#### Phase 3: Visualization
- Created `04_visualize_network.py` to render a dark-themed geographic map of the extracted tracks and stations using `matplotlib`. This served as a quick visual sanity check that the extraction was working correctly.

#### Phase 4: Network Graph
- Created `05_build_network_graph.py` to convert flat track geometries into a directed, routable `NetworkX` graph. The graph uses full 15-decimal coordinate precision for node IDs and adds bidirectional edges for each track segment. Edge attributes include `maxspeed`, `gauge`, `electrified`, and `railway` type where available from OSM tags. Exported as `switzerland.graphml`.

#### Phase 5: GTFS & Rolling Stock
- Created `06_download_gtfs.py` — the most complex script in the pipeline. It downloads the official Swiss GTFS feed from `opentransportdata.swiss`, extracts it, and processes the `routes`, `trips`, `stops`, and `stop_times` files to produce a comprehensive schedule dataset.
- Created `data/rolling_stock_profiles.json`, a hand-curated mapping of Swiss train categories (ICE, TGV, IC, IR, RE, S-Bahn, etc.) to their physical properties: weight, carriages, max speed, power supply, and track gauge.
- The GTFS processing script maps these physical attributes to every trip based on its route name prefix. The result is `in_depth_schedules.csv` (~294 MB), containing full journey details enriched with rolling stock physics for every scheduled passenger train in Switzerland.
- An API token for the Swiss OJP (Open Journey Planner) 2.0 API was obtained and stored in `.env` for potential future use. This API offers richer journey planning capabilities (quota: 20,000 calls/day, rate limit: 50 calls/minute).

#### First Commit
- Initialized the Git repository, configured `.gitignore` to exclude the large `data/` directory, and pushed the pipeline to GitHub.
- Commit: `feat: implement Swiss rail data pipeline and add documentation`

---

### 7 September 2026 — Documentation

- Expanded the `README.md` with a full project structure tree, detailed descriptions of each pipeline step, and execution instructions.
- Commit: `docs: expand README with project structure and detailed execution instructions`

---

### 9 September 2026 — Data Validation

- Investigated a potential data quality issue: the `gauge` column appeared to be `1435` for all rows in `in_depth_schedules.csv`. Confirmed this is expected — the vast majority of Swiss trains run on standard gauge (1435 mm). Only the Panorama Express (PE) runs on metre gauge (1000 mm) in the current rolling stock profiles.
- Verified that the `stop_sequence` column correctly orders stops within each trip (1, 2, 3, ...) rather than being a constant.

---

### 10 September 2026 — Weekly Frequency & Master Dataset

#### Adding Weekday Information
- Identified that the `in_depth_schedules.csv` was missing information about which days of the week each train runs.
- Updated `06_download_gtfs.py` to integrate GTFS `calendar.txt` (weekday flags) and `calendar_dates.txt` (exception days) into the processing pipeline.
- Initially added a `days_per_week` count column, but this was deemed insufficient — knowing *which* specific days a train runs (Mon, Tue, etc.) is more useful than just a count.
- Replaced `days_per_week` with a human-readable `weekdays` string column (e.g., `"Mon,Tue,Wed,Thu,Fri"`).
- Also added the `trip_id` column to the output for better traceability and uniqueness.

#### Creating the Master Dataset
- Created `07_create_master_dataset.py` to bridge the real-time API snapshot (`switzerland_schedules.csv`) with the full GTFS timetable (`in_depth_schedules.csv`).
- The script performs an inner join matching on station name, destination, departure time, and route identifier to link the live API observations to their full GTFS trip records.
- Once matched, it extracts the complete journey details (all intermediate stops) for every matched train, producing `master_dataset.csv` (~7.8 MB).

#### Data Quality Checks
- Verified that the weekday distribution in the master dataset is varied (not all rows showing the same day).
- Confirmed that there are no rows with missing/null values in any column of the master dataset.
- Investigated the join coverage: some API rows could not be matched to GTFS records due to minor differences in naming conventions or timing. The inner join approach ensures that only high-confidence matches make it into the master dataset.

---

### 10 September 2026 — Documentation Update & Project History

- Rewrote `README.md` from scratch with comprehensive coverage: project structure with file sizes and git tracking status, detailed pipeline step descriptions with explicit inputs/outputs, full data dictionary, rolling stock profiles table, environment variable documentation, data source links, system requirements, and scope/limitations.
- Created this `project_history.md` file to document the evolution of the project.
- Updated `.gitignore` to use granular file-type patterns (instead of blanket `data/` exclusion) so that the small, hand-curated `data/rolling_stock_profiles.json` is properly version-controlled.
- Fixed `04_visualize_network.py` to save the output map image to `data/` instead of a hardcoded development-environment artifact path.

---

## Files Not Committed (and Why)

The following files are generated by the pipeline and are excluded from version control due to their size or because they are reproducible from code:

| File | Size | Reason |
|------|------|--------|
| `data/raw/switzerland-latest.osm.pbf` | ~520 MB | Downloaded from Geofabrik; re-downloadable |
| `data/raw/ch_gtfs.zip` | ~237 MB | Downloaded from opentransportdata.swiss; re-downloadable |
| `data/raw/gtfs/*.txt` | ~3.8 GB total | Extracted from the GTFS zip |
| `data/switzerland_tracks.geojson` | ~48 MB | Generated by Step 2 |
| `data/switzerland_stations.geojson` | ~1.2 MB | Generated by Step 2 |
| `data/switzerland_schedules.csv` | ~44 KB | Generated by Step 3 (point-in-time snapshot) |
| `data/switzerland.graphml` | ~172 MB | Generated by Step 5 |
| `data/in_depth_schedules.csv` | ~294 MB | Generated by Step 6 |
| `data/master_dataset.csv` | ~7.8 MB | Generated by Step 7 |
| `data/switzerland_railway_map.png` | — | Generated by Step 4 |
| `.env` | ~135 B | Contains API tokens (security) |

The only data file that **is** committed is `data/rolling_stock_profiles.json` (3.5 KB) because it is a hand-curated configuration file that cannot be regenerated by code.
