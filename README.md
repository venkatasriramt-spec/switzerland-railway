# ARTEMIS Switzerland — Railway Data Pipeline & Simulation 🇨🇭🚋

**ARTEMIS** (**A**utomated **R**ailway **T**ransport **E**nergy **M**odelling and **I**nfrastructure **S**ystem) — Switzerland Edition

A comprehensive data pipeline that automatically downloads, processes, models, and visualizes railway network infrastructure and timetable data for the entire Swiss rail system. This project collects real-world geographic, scheduling, and rolling stock data and transforms it into clean, analysis-ready datasets. 

Building on this data, the project features a **multi-agent Reinforcement Learning (RL) simulation** where an AI (trained via PPO) learns to schedule and route thousands of trains simultaneously across the network, visualized in real-time through a dedicated web dashboard.

---

## 📂 Project Structure

```text
ARTEMIS_Switzerland/
│
├── data_preparation/                       # Core pipeline scripts (run sequentially)
│   ├── 01_download_infrastructure.py       # Download OSM data for Switzerland
│   ├── ...
│   └── 10_add_station_metadata.py          # Enrich master dataset with coordinates + platforms
│
├── simulation/                             # RL Simulation Environment & Training
│   ├── artemis_env.py                      # Original Gym environment (full 5,600+ train fleet)
│   ├── artemis_env_advanced.py             # Advanced env with curriculum learning & GPS interpolation
│   ├── dispatcher_env.py                   # Regional Dispatcher env (Hold/Dispatch per-train actions)
│   ├── callbacks.py                        # Custom SB3 callbacks (curriculum, file-progress)
│   ├── train_agent.py                      # Standard PPO training script
│   └── run_trained_model.py                # Evaluation script for the trained model
│
├── scripts/                                # Helper / preprocessing scripts
│   ├── preprocess_data.py                  # Generates mini_routes.json for fast env loading
│   ├── split_regions.py                    # Splits master dataset into 4 geographic regions
│   ├── shared_memory_server.py             # Loads compiled_routes.json into Redis for IPC
│   └── master_progress_bar.py              # Unified terminal progress bar (reads Redis)
│
├── dashboard/                              # Real-time Web Dashboard
│   ├── backend/                            # FastAPI backend (WebSocket simulation streaming)
│   └── frontend/                           # React frontend (Vite) with multi-page routing
│       └── src/pages/                      # Home, Visualization, About pages
│
├── train_advanced.py                       # Multi-core advanced PPO training orchestrator
├── train_dispatcher.py                     # Per-region Dispatcher PPO training (4 parallel regions)
├── monitor_safety.py                       # Resource watcher daemon (RAM/CPU guard)
├── run_safely.sh                           # Orchestrates advanced training with safety monitor
├── run_dispatcher_safely.sh                # Orchestrates regional dispatcher training (28 vCPUs)
├── start_dashboard.sh                      # One-command launcher for backend + frontend
├── plot_training.py                        # Script to plot training metrics from CSV logs
│
├── data/                                   # Generated data directory (mostly gitignored)
│   ├── rolling_stock_profiles.json         # ✅ Tracked — hand-curated train physics config
│   ├── compiled_routes.json                # ❌ Ignored — precompiled route distances
│   ├── mini_routes.json                    # ❌ Ignored — preprocessed fast-loading routes
│   ├── regions.json                        # ❌ Ignored — geographic region splits
│   └── ...                                 # Other generated files (CSV, GeoJSON, etc.)
│
├── models/                                 # Trained AI models (gitignored)
│   ├── checkpoints_advanced/               # ❌ Ignored — periodic training snapshots
│   └── tb_logs/                            # ❌ Ignored — TensorBoard training logs
│
├── logs/                                   # ❌ Ignored — CSV and text progress logs
├── tensorboard_logs/                       # ❌ Ignored — Advanced TensorBoard logs
├── tensorboard_images/                     # Screenshots for TensorBoard guide
├── tensorboard_guide.md                    # Guide to understanding PPO training metrics
├── .env                                    # API tokens (gitignored)
├── .gitignore                              # Version control exclusions
├── project_history.md                      # Chronological development log
└── README.md                               # You are here
```

---

## 🛠️ Data Pipeline Steps

The pipeline consists of 10 sequentially numbered Python scripts in `data_preparation/`. Each step builds on the outputs of previous steps.

### Step 1 — Download Infrastructure (`01_download_infrastructure.py`)
Downloads the latest OpenStreetMap `.pbf` export for Switzerland (~520 MB) from Geofabrik.

### Step 2 — Extract Tracks & Stations (`02_extract_tracks_and_stations.py`)
Uses `pyrosm` to parse the massive OSM file and extract rail track and station geometries.

### Step 3 — Fetch Live Schedules (`03_fetch_schedules.py`)
Fetches real-time departure boards for major Swiss railway hubs via `transport.opendata.ch`.

### Step 4 — Visualize Network (`04_visualize_network.py`)
Renders a high-resolution, dark-themed geographic map of the Swiss rail network using `matplotlib`.

### Step 5 — Build Network Graph (`05_build_network_graph.py`)
Converts the flat track geometries into a topologically connected, directed routing graph using `NetworkX`.

### Step 6 — Download & Process GTFS (`06_download_gtfs.py`)
Downloads and processes the massive official Swiss GTFS dataset (~3 GB text), enriching it with train physical attributes (weight, max speed, etc.) from `data/rolling_stock_profiles.json`.

### Step 7 — Create Master Dataset (`07_create_master_dataset.py`)
Inner joins the live API snapshot with the full GTFS timetable to extract full journey details for matched trains.

### Step 8 — Map Stations to Graph (`08_map_stations_to_graph.py`)
Snaps GTFS stations to the nearest routable node in the `NetworkX` graph using KD-tree spatial search.

### Step 9 — Generate Verification Map (`09_visualize_map.py`)
Produces a Google Maps HTML visualization to verify station placement. (Requires `GOOGLE_MAPS_API_KEY` in `.env`).

### Step 10 — Add Station Metadata (`10_add_station_metadata.py`)
Enriches the master dataset with exact coordinates and platform counts per station.

---

## 🤖 AI Simulation & Training

Once the data pipeline produces the `master_dataset.csv` and `compiled_routes.json`, the simulation environment takes over. There are two tiers of training:

### Tier 1 — Low-Level Driver (`simulation/artemis_env_advanced.py`)
A custom OpenAI Gym environment simulates the kinematics (acceleration, braking, coasting) of up to 500 trains simultaneously. The environment interpolates geographical coordinates using precomputed trip distances to reflect realistic train movement. Features include:
- **Collision detection** with dynamic penalty scaling.
- **Curriculum learning** that ramps the number of active trains as the agent improves.
- **GPS interpolation** (`get_train_coordinates()`) for real-time map visualization.

Training is orchestrated by `train_advanced.py`, which uses `SubprocVecEnv` to parallelize across all available CPU cores with safety monitoring via `run_safely.sh` and `monitor_safety.py`.

### Tier 2 — Regional Dispatcher (`simulation/dispatcher_env.py`)
A higher-level Gym environment where the agent makes **Hold/Dispatch** decisions for trains within a geographic region. The Swiss network is split into 4 quadrants (Northeast, Northwest, Southeast, Southwest) by `scripts/split_regions.py`, and each region trains its own PPO agent in parallel via `train_dispatcher.py`.

The full dispatcher pipeline is orchestrated by `run_dispatcher_safely.sh`:
1. Loads route topology into **Redis** shared memory (`scripts/shared_memory_server.py`).
2. Chunks the master dataset into 4 regions (`scripts/split_regions.py`).
3. Launches 4 parallel regional trainers (7 envs each = 28 vCPUs).
4. Displays a unified progress bar via `scripts/master_progress_bar.py`.

> For a deep dive into the training performance and metrics, see the **[TensorBoard Guide](tensorboard_guide.md)**.

### Running & Evaluating (`simulation/run_trained_model.py`)
Evaluates the saved policy deterministically over a set of episodes and traces the reward outputs in the terminal.

---

## 🖥️ Web Dashboard

The `dashboard/` directory contains a real-time web interface for visualizing the live simulation.

- **Backend (`dashboard/backend/main.py`)**: A FastAPI application that loads the trained PPO model, steps the `ArtemisAdvancedEnv`, and streams live train coordinates (in km/h), speeds, and delays via WebSockets.
- **Frontend (`dashboard/frontend/`)**: A React/Vite application with client-side routing. Pages include Home, Interactive Map Visualization (Google Maps), and About.
- **One-command launch**: `./start_dashboard.sh` starts both servers and cleans up old processes.

---

## 📊 Data Dictionary

| File | Size | Description |
|------|------|-------------|
| `switzerland_tracks.geojson` | ~48 MB | GeoJSON of all rail track geometries in Switzerland |
| `switzerland_stations.geojson` | ~1.2 MB | GeoJSON of all station/halt point locations |
| `switzerland.graphml` | ~172 MB | Directed routing graph (nodes + edges with attributes) |
| `in_depth_schedules.csv` | ~294 MB | Full GTFS schedules enriched with rolling stock physics |
| `master_dataset.csv` | ~13 MB | Merged API + GTFS dataset with coordinates, platforms, graph links |
| `station_to_node_mapping.csv` | ~17 MB | GTFS stop → graph node spatial mapping with snap distances |

> **Note:** The `data/` directory is mostly ignored by Git due to file size limits. Run the pipeline to regenerate these files.

---

## 🚀 How to Run

### 1. Data Pipeline
```bash
pip install requests pandas geopandas pyrosm networkx matplotlib shapely scipy numpy
# Run scripts 01 through 10 sequentially:
python data_preparation/01_download_infrastructure.py
# ...
```

### 2. AI Simulation — Low-Level Driver
```bash
pip install stable-baselines3[extra] gymnasium
# Preprocess data for fast simulation loading
python scripts/preprocess_data.py

# Run the advanced, multi-core training with safety monitoring
./run_safely.sh

# Evaluate the trained model
python simulation/run_trained_model.py
```

### 3. AI Simulation — Regional Dispatcher
```bash
# Requires Redis running locally (apt install redis-server && redis-server --daemonize yes)
pip install redis

# Run the full dispatcher pipeline (data preprocessing → region split → 4-region parallel training)
./run_dispatcher_safely.sh
```

### 4. Web Dashboard
```bash
# One-command launch (starts backend + frontend):
./start_dashboard.sh

# Or manually:
cd dashboard/backend && pip install fastapi uvicorn websockets && uvicorn main:app --reload --port 8000
cd dashboard/frontend && npm install && npm run dev
```

---

## 🛡️ Scope & Limitations
- **Passenger trains only.** Freight trains are not included as their schedules are not public.
- **Estimated rolling stock data.** Physical properties are mapped by category (e.g., IC, S-Bahn).
- **Euclidean snapping.** Station-to-graph node mapping uses straight-line distance, which may occasionally snap to parallel lines.
- **Linear GPS interpolation.** Train positions on the dashboard map are interpolated linearly between start/end coordinates rather than following exact track geometry.
