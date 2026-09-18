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
│   ├── 02_extract_tracks_and_stations.py   # Extract rail tracks + stations from OSM
│   ├── 03_fetch_schedules.py               # Fetch live schedules from transport API
│   ├── 04_visualize_network.py             # Render a geographic network map (matplotlib)
│   ├── 05_build_network_graph.py           # Build a routable NetworkX graph
│   ├── 06_download_gtfs.py                 # Download + process official Swiss GTFS feed
│   ├── 07_create_master_dataset.py         # Merge API + GTFS into a master dataset
│   ├── 08_map_stations_to_graph.py         # Snap GTFS stations to nearest graph nodes
│   ├── 09_visualize_map.py                 # Generate Google Maps verification map
│   └── 10_add_station_metadata.py          # Enrich master dataset with coordinates + platforms
│
├── simulation/                             # RL Simulation Environment & Training
│   ├── artemis_env.py                      # Custom Gym Environment for train simulation
│   ├── train_agent.py                      # Stable Baselines3 PPO training script
│   └── run_trained_model.py                # Evaluation script for the trained model
│
├── dashboard/                              # Real-time Web Dashboard
│   ├── backend/                            # FastAPI backend (WebSocket simulation streaming)
│   └── frontend/                           # React frontend (Vite) for map visualization
│
├── visualization/                          # Standalone visualization outputs
│   └── map.html                            # Leaflet.js single-journey map (example: S1 Baar)
│
├── data/                                   # Generated data directory (mostly gitignored)
│   ├── rolling_stock_profiles.json         # ✅ Tracked — hand-curated train physics config
│   ├── compiled_routes.json                # ❌ Ignored — precompiled route distances
│   ├── raw/                                # ❌ Ignored — raw downloads (OSM .pbf, GTFS .zip)
│   ├── master_dataset.csv                  # ❌ Ignored — final merged dataset (~13 MB)
│   └── ...                                 # Other generated files (CSV, GeoJSON, etc.)
│
├── models/                                 # Trained AI models (gitignored)
│   ├── artemis_final_model.zip             # ❌ Ignored — trained PPO agent
│   └── tb_logs/                            # ❌ Ignored — TensorBoard training logs
│
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

Once the data pipeline produces the `master_dataset.csv` and `compiled_routes.json`, the simulation environment takes over.

### The Gym Environment (`simulation/artemis_env.py`)
A custom OpenAI Gym environment simulates the kinematics (acceleration, braking, coasting) of up to 5,600+ scheduled trains simultaneously. The environment interpolates geographical coordinates using precomputed trip distances to reflect realistic train movement.

### Training the Agent (`simulation/train_agent.py`)
We use **Proximal Policy Optimization (PPO)** from Stable Baselines3 to train an AI agent. The agent observes the positions, speeds, and delays of all trains and must choose control actions (Accelerate, Coast, Brake) to minimize cumulative network delay and energy consumption. 

> For a deep dive into the training performance and metrics, see the **[TensorBoard Guide](tensorboard_guide.md)**.

### Running & Evaluating (`simulation/run_trained_model.py`)
Evaluates the saved `models/artemis_final_model.zip` policy deterministically over a set of episodes and traces the reward outputs in the terminal.

---

## 🖥️ Web Dashboard

The `dashboard/` directory contains a real-time web interface for visualizing the live simulation.

- **Backend (`dashboard/backend/main.py`)**: A FastAPI application that loads the trained PPO model, steps the `ArtemisEnv`, and streams live train coordinates, speeds, and delays via WebSockets.
- **Frontend (`dashboard/frontend/`)**: A React/Vite application that connects to the WebSocket and plots trains dynamically on a map interface.

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

### 2. AI Simulation
```bash
pip install stable-baselines3[extra] gym
# Train the model (outputs to models/ and tensorboard logs to models/tb_logs/)
python simulation/train_agent.py
# Evaluate the trained model
python simulation/run_trained_model.py
```

### 3. Web Dashboard
**Backend:**
```bash
cd dashboard/backend
pip install fastapi uvicorn websockets
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd dashboard/frontend
npm install
npm run dev
```

---

## 🛡️ Scope & Limitations
- **Passenger trains only.** Freight trains are not included as their schedules are not public.
- **Estimated rolling stock data.** Physical properties are mapped by category (e.g., IC, S-Bahn).
- **Euclidean snapping.** Station-to-graph node mapping uses straight-line distance, which may occasionally snap to parallel lines.
