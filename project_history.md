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
- Once matched, it extracts the complete journey details (all intermediate stops) for every matched train, producing `master_dataset.csv`.

#### Data Quality Checks
- Verified that the weekday distribution in the master dataset is varied (not all rows showing the same day).
- Confirmed that there are no rows with missing/null values in any column of the master dataset.
- Investigated the join coverage: some API rows could not be matched to GTFS records due to minor differences in naming conventions or timing. The inner join approach ensures that only high-confidence matches make it into the master dataset.

---

### 10 September 2026 — Documentation & Gitignore Update

- Rewrote `README.md` from scratch with comprehensive coverage.
- Created `project_history.md` to document the evolution of the project.
- Updated `.gitignore` to use granular file-type patterns (instead of blanket `data/` exclusion) so that the small, hand-curated `data/rolling_stock_profiles.json` is properly version-controlled.
- Fixed `04_visualize_network.py` to save the output map image to `data/` instead of a hardcoded development-environment artifact path.

---

### 11 September 2026 — Graph Linking, Station Metadata & Visualization

#### Station-to-Graph Mapping (Step 8)
- Created `08_map_stations_to_graph.py` to link GTFS stations to the geographic network graph.
- The script loads `switzerland.graphml` (all ~650K+ nodes), builds a KD-tree using `scipy.spatial.cKDTree`, and performs nearest-neighbor lookups for every GTFS stop.
- Computes the haversine distance in meters between each station and its nearest graph node for quality verification.
- Produces `station_to_node_mapping.csv` and adds a `graph_node_id` column to the master dataset.
- All stations are retained regardless of snap distance (no rows dropped).

#### Interactive Map Visualization (Step 9)
- Created `09_visualize_map.py` to generate a Google Maps-based interactive verification map.
- The map plots all unique stations from the master dataset as red circle markers on a terrain base map, centered on Switzerland.
- Country borders are overlaid via GeoJSON, with all non-Swiss countries dimmed using a semi-transparent black fill to clearly isolate Switzerland.
- Hovering over a station shows an info window with the station name and platform count.
- Required a Google Maps API key, stored as `GOOGLE_MAPS_API_KEY` in `.env`.

#### Exploration of Full Track Visualization
- Attempted to render the full ~48 MB track GeoJSON in the browser using multiple approaches:
  - **Leaflet.js markers + polylines:** Crashed the browser due to the sheer number of DOM elements.
  - **WebGL rendering:** Exported all track coordinates into `tracks_data.js` (~53 MB) and created `webgl_map.html`, but browser memory constraints remained an issue.
  - **Google Maps with GeoJSON overlay:** Successfully rendered stations but track rendering at full resolution proved too intensive for the browser without GPU acceleration.
- Concluded that station-only maps are the most practical for browser-based verification. Full track visualization is better handled by `matplotlib` (Step 4) or desktop GIS tools.

#### Journey Visualization Proof-of-Concept
- Explored journey visualization by creating a Leaflet.js interactive map showing a single train journey (S1 line to Baar).
- Displays a red polyline connecting all stops in sequence with clickable markers showing arrival/departure times at each station.
- Demonstrates the feasibility of per-journey visualization using the master dataset.

#### Station Metadata Enrichment (Step 10)
- Created `10_add_station_metadata.py` to enrich the master dataset with:
  - **Exact coordinates:** `stop_lat` and `stop_lon` for each station, extracted from GTFS `stops.txt`.
  - **Platform count:** Number of unique non-null platform codes per station. Defaults to 1 if the GTFS data does not specify platform information for a station.
- Columns are inserted directly after `stop_name` for logical ordering.
- The script is idempotent — it drops existing metadata columns before re-adding them, so it can be safely re-run.
- Master dataset grew to ~13 MB with the additional columns.

---

### 11 September 2026 — Documentation & Gitignore Update (Round 2)

- Updated `README.md` to document all 10 pipeline steps, the visualization outputs, updated data dictionary with new columns and new files, added `GOOGLE_MAPS_API_KEY` to the environment variable table, added `scipy` and `numpy` to the dependency list, and updated scope/limitations section.
- Updated `project_history.md` with all Sep 11 developments.
- Updated `.gitignore` to also ignore generated `.html` and `.js` files in `data/`.

---

### 18 September 2026 — Multi-Agent Simulation & Dashboard

#### Train Kinematics Simulation (`simulation/`)
- Created `simulation/artemis_env.py` - an OpenAI Gym environment that simulates the entire Swiss railway network.
  - Simulates the physics (acceleration, braking, coasting) of up to 5,600+ scheduled trains simultaneously.
  - Caps train speeds at 40 m/s (144 km/h) to maintain realistic physics boundaries.
  - Computes and interpolates real-time train positions (`lat`, `lon`) along routes based on progress (precompiled distance).
- Created `simulation/train_agent.py` to train an AI model via **Proximal Policy Optimization (PPO)** (from Stable Baselines3). The agent is tasked with selecting optimal train actions to minimize cumulative delay across the network.
- Developed `simulation/run_trained_model.py` to evaluate the finalized policy (saved at `models/artemis_final_model.zip`) deterministically, reporting total steps survived and cumulative reward.

#### TensorBoard Training Analysis
- Produced a deep-dive analysis (`tensorboard_guide.md`) capturing the results of 10M+ timesteps of PPO training on a 24-core instance.
- Visualized and explained optimization metrics (`approx_kl`, `entropy_loss`, `value_loss`), and throughput (`time/fps`), confirming highly stable, convergent training.

#### Real-Time Web Dashboard (`dashboard/`)
- Built a web visualization interface to spectate the AI agent managing the live simulation.
- **Backend**: A `FastAPI` application (`dashboard/backend/main.py`) that loads the PPO agent, runs the environment simulation loop, and broadcasts real-time train states (`lat`, `lon`, `speed`, `delay`) to clients via a WebSocket connection.
- **Frontend**: A `React`/`Vite` web app (`dashboard/frontend/`) that connects to the backend and renders trains moving dynamically over a map interface.

#### Configuration and Version Control
- Expanded `.gitignore` to explicitly ignore new simulation outputs: `simulation/*.log`, training checkpoints (`models/*.zip`, `models/tb_logs/`), and web dashboard builds (`dashboard/frontend/node_modules/`, `.playwright-mcp/`).
- Updated the comprehensive `README.md` to detail how to run the new AI simulation and launch the real-time web dashboard.

---

### 20 September 2026 — Advanced AI Training, Safety Monitoring & Dashboard Expansion

#### Advanced Multiprocessed Training Pipeline
- Developed `train_advanced.py` utilizing Stable Baselines3's `SubprocVecEnv` to parallelize PPO training across multiple CPU cores.
- Introduced `simulation/artemis_env_advanced.py` to support variable train capacities.
- Added custom training callbacks (`simulation/callbacks.py`):
  - **CurriculumCallback**: Dynamically increases the number of trains in the simulation (from 50 to 1000+) as training progresses to facilitate curriculum learning.
  - **FileProgressCallback**: Logs training progress cleanly to files in `logs/` rather than spamming stdout.
- Integrated `tensorboard_logs/` for tracking the advanced model metrics.

#### Background Safety & Resource Monitoring
- Created `monitor_safety.py` as an independent daemon that continuously monitors system RAM and CPU usage during training.
- Developed `run_safely.sh` to orchestrate the entire training process:
  - First runs data preprocessing.
  - Launches the safety monitor in the background.
  - Starts the advanced training script.
  - Ensures the monitor is gracefully killed when training completes.
- Wrote diagnostic scripts (`test_memory.py`, `test_pickle_size.py`) to investigate and optimize serialization and memory overhead during multi-core IPC.

#### Preprocessing & Dashboard Refactor
- Added `scripts/preprocess_data.py` to cache frequently accessed routes into `data/mini_routes.json`, vastly speeding up environment initialization.
- Refactored the React/Vite dashboard (`dashboard/frontend/`) to use client-side routing.
- Replaced the monolithic interface with discrete pages:
  - `Home.jsx`: Project introduction.
  - `Visualization.jsx`: Real-time WebSockets Leaflet map.
  - `About.jsx`: Project details and history.

---

### 23 September 2026 — Hierarchical Dispatcher, Regional Training & Dashboard Polish

#### Regional Dispatcher Environment (`simulation/dispatcher_env.py`)
- Created a new higher-level Gym environment where the AI makes **Hold/Dispatch** binary decisions for every train in a geographic region.
- Uses a `MultiBinary` action space (one bit per train: 0 = Hold, 1 = Dispatch).
- Models network congestion: dispatching too many trains simultaneously incurs a heavy penalty, while safe dispatching earns large rewards. Holding trains incurs a small delay penalty.
- Connects to a **Redis** instance for shared-memory inter-process communication, allowing all parallel CPU workers to share route topology without each loading the massive JSON into their own memory.

#### Geographic Region Splitting (`scripts/split_regions.py`)
- Splits the master dataset into 4 geographic quadrants (Northeast, Northwest, Southeast, Southwest) based on each train's starting station coordinates.
- Centre point: lat=46.8, lon=8.2 (approximate geographic centre of Switzerland).
- Outputs `data/regions.json` mapping region names to lists of trip IDs.

#### Redis Shared Memory Server (`scripts/shared_memory_server.py`)
- Loads `compiled_routes.json` into Redis as individual per-trip keys using pipelined batched writes.
- This solves the critical scalability problem: without shared memory, every `SubprocVecEnv` worker would independently load the ~200 MB+ route data, exhausting RAM.

#### Regional Dispatcher Training (`train_dispatcher.py`)
- Accepts a `--region` argument and trains a PPO agent specifically for that region's trains.
- Uses 7 parallel environments per region (4 regions × 7 = 28 vCPUs total).
- Includes a `RedisProgressCallback` that publishes timestep progress to Redis, consumed by the master progress bar.

#### Training Orchestration (`run_dispatcher_safely.sh`)
- Full pipeline script that:
  1. Starts the safety monitor.
  2. Loads route data into Redis (`shared_memory_server.py`).
  3. Splits the dataset into 4 regions (`split_regions.py`).
  4. Launches 4 background `train_dispatcher.py` processes (one per region).
  5. Runs `scripts/master_progress_bar.py` in the foreground — a unified terminal UI with per-region progress bars reading from Redis.
  6. Waits for all trainers, then shuts down the safety monitor.

#### Dashboard Convenience & Refinements
- Created `start_dashboard.sh` — a one-command launcher that starts the FastAPI backend and the Vite frontend simultaneously, cleans up any leftover processes on the relevant ports, and traps `CTRL+C` for graceful shutdown.
- Switched the dashboard backend from the original `ArtemisEnv` to `ArtemisAdvancedEnv`, eliminating the manual observation-batching workaround (the new model natively accepts the full 500-train observation matrix).
- Added `get_train_coordinates()` to `ArtemisAdvancedEnv` for GPS interpolation, so the backend can stream lat/lon without separate coordinate logic.
- Changed speed display units from m/s to km/h across the frontend (`Map.jsx`, `Visualization.jsx`).
- Removed the `TrainData` page from the frontend navigation and routing (the data was consolidated into the Visualization view).
- Updated `monitor_safety.py` to also watch for `train_dispatcher.py` processes and increased the sustained-alert threshold from 10s to 60s to reduce false alarms during heavy parallel training.

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
| `data/switzerland_railway_map.png` | — | Generated by Step 4 |
| `data/switzerland.graphml` | ~172 MB | Generated by Step 5 |
| `data/in_depth_schedules.csv` | ~294 MB | Generated by Step 6 |
| `data/master_dataset.csv` | ~13 MB | Generated by Steps 7, 8, 10 |
| `data/station_to_node_mapping.csv` | ~17 MB | Generated by Step 8 |
| `data/verification_map.html` | ~84 KB | Generated by Step 9 |
| `data/tracks_data.js` | ~53 MB | Generated during track visualization experiments |
| `data/webgl_map.html` | ~3 KB | Generated during track visualization experiments |
| `data/compiled_routes.json` | — | Very large JSON cache generated for the simulator |
| `data/mini_routes.json` | — | Preprocessed fast-loading routes for advanced training |
| `data/regions.json` | ~200 KB | Generated by `split_regions.py` for dispatcher training |
| `data/collision_avoidance.png` | — | Generated visualization artifact |
| `models/` | — | Large binary trained neural network weights and checkpoints |
| `logs/` | — | Progress and output logs from training |
| `tensorboard_logs/` | — | TensorBoard logs from advanced training |
| `simulation/*.log` | — | Training and evaluation log files |
| `dashboard/frontend/node_modules/`| — | Frontend dependencies |
| `test_*.py` | — | Throwaway diagnostic/debugging scripts |
| `.env` | ~194 B | Contains API tokens (security) |

The only data file that **is** committed is `data/rolling_stock_profiles.json` (3.5 KB) because it is a hand-curated configuration file that cannot be regenerated by code.

