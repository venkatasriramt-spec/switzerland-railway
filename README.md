# ARTEMIS Switzerland — Railway Data Pipeline 🇨🇭🚋

**ARTEMIS** (**A**utomated **R**ailway **T**ransport **E**nergy **M**odelling and **I**nfrastructure **S**ystem) — Switzerland Edition

A comprehensive data pipeline that automatically downloads, processes, models, and visualizes railway network infrastructure and timetable data for the entire Swiss rail system. This project collects real-world geographic, scheduling, and rolling stock data and transforms it into clean, analysis-ready datasets.

---

## 📂 Project Structure

```text
ARTEMIS_Switzerland/
│
├── data_preparation/                       # Core pipeline scripts (run sequentially)
│   ├── 01_download_infrastructure.py       # Download OSM data for Switzerland
│   ├── 02_extract_tracks_and_stations.py   # Extract rail tracks + stations from OSM
│   ├── 03_fetch_schedules.py               # Fetch live schedules from transport API
│   ├── 04_visualize_network.py             # Render a geographic network map
│   ├── 05_build_network_graph.py           # Build a routable NetworkX graph
│   ├── 06_download_gtfs.py                 # Download + process official Swiss GTFS feed
│   └── 07_create_master_dataset.py         # Merge API + GTFS into a master dataset
│
├── data/                                   # Generated data directory (mostly gitignored)
│   ├── rolling_stock_profiles.json         # ✅ Tracked — hand-curated train physics config
│   ├── raw/                                # ❌ Ignored — raw downloads (OSM .pbf, GTFS .zip)
│   │   ├── switzerland-latest.osm.pbf      #    (~520 MB)
│   │   ├── ch_gtfs.zip                     #    (~237 MB)
│   │   └── gtfs/                           #    Extracted GTFS text files (~3.8 GB total)
│   ├── switzerland_tracks.geojson          # ❌ Ignored — extracted rail track geometries
│   ├── switzerland_stations.geojson        # ❌ Ignored — extracted station locations
│   ├── switzerland_schedules.csv           # ❌ Ignored — real-time API schedule snapshot
│   ├── switzerland.graphml                 # ❌ Ignored — routable network graph (~172 MB)
│   ├── in_depth_schedules.csv              # ❌ Ignored — enriched GTFS schedules (~294 MB)
│   ├── master_dataset.csv                  # ❌ Ignored — final merged dataset (~7.8 MB)
│   └── switzerland_railway_map.png         # ❌ Ignored — rendered network visualization
│
├── .env                                    # API tokens (gitignored)
├── .gitignore                              # Version control exclusions
├── project_history.md                      # Chronological development log
└── README.md                               # You are here
```

---

## 🛠️ Pipeline Steps in Detail

The pipeline consists of 7 sequentially numbered Python scripts in `data_preparation/`. Each step builds on the outputs of previous steps.

### Step 1 — Download Infrastructure (`01_download_infrastructure.py`)

Downloads the latest OpenStreetMap (OSM) Protocolbuffer Binary Format (`.pbf`) export for Switzerland from [Geofabrik](https://download.geofabrik.de/europe/switzerland.html). This ~520 MB file contains the complete geographic footprint of Switzerland, including all mapped roads, buildings, and — crucially — railway infrastructure.

**Input:** Internet connection  
**Output:** `data/raw/switzerland-latest.osm.pbf`

---

### Step 2 — Extract Tracks & Stations (`02_extract_tracks_and_stations.py`)

Uses [`pyrosm`](https://pyrosm.readthedocs.io/) and [`geopandas`](https://geopandas.org/) to parse the massive OSM file. It applies custom filters to extract only railway-relevant features:

- **Tracks:** Standard rail (`rail`) and narrow gauge (`narrow_gauge`) geometries.
- **Stations:** Station and halt nodes/polygons (polygon geometries are reduced to centroids).

**Input:** `data/raw/switzerland-latest.osm.pbf`  
**Output:** `data/switzerland_tracks.geojson`, `data/switzerland_stations.geojson`

---

### Step 3 — Fetch Live Schedules (`03_fetch_schedules.py`)

Interfaces with the [Swiss Open Transport API](https://transport.opendata.ch/) to fetch real-time departure boards for 9 major Swiss railway hubs:

> Zürich HB, Bern, Basel SBB, Genève, Lausanne, Luzern, Winterthur, St. Gallen, Lugano

Collects train categories (S, IC, IR, RE, etc.), train numbers, operators (SBB, BLS, etc.), platforms, departure times, and destinations. Includes a polite 1-second delay between API calls to respect rate limits.

**Input:** Internet connection  
**Output:** `data/switzerland_schedules.csv`

---

### Step 4 — Visualize Network (`04_visualize_network.py`)

Renders a high-resolution, dark-themed geographic map of the entire Swiss railway network using `matplotlib`. Tracks are drawn as light blue lines and stations as pink dots, layered on a dark background for contrast.

**Input:** `data/switzerland_tracks.geojson`, `data/switzerland_stations.geojson`  
**Output:** `data/switzerland_railway_map.png`

---

### Step 5 — Build Network Graph (`05_build_network_graph.py`)

Converts the flat GeoJSON track geometries into a topologically connected, **directed** routing graph using [`NetworkX`](https://networkx.org/).

Key design decisions:
- **Full coordinate precision:** Node IDs use 15-decimal-place precision (`lon,lat`) to preserve topological connectivity.
- **Bidirectional edges:** Every track segment gets edges in both directions (rail is bidirectional by default).
- **Edge attributes:** Preserves `maxspeed`, `gauge`, `electrified`, and `railway` type where available from OSM tags.
- **MultiLineString handling:** Geometries are exploded into individual `LineString` segments before graph construction.

**Input:** `data/switzerland_tracks.geojson`  
**Output:** `data/switzerland.graphml`

---

### Step 6 — Download & Process GTFS (`06_download_gtfs.py`)

The most intensive script in the pipeline. It handles the complete lifecycle of Swiss GTFS data:

1. **Download:** Fetches the official Swiss GTFS feed (~237 MB zip) from [opentransportdata.swiss](https://opentransportdata.swiss/).
2. **Extract:** Unpacks the GTFS zip into individual text files (`routes.txt`, `trips.txt`, `stops.txt`, `stop_times.txt`, `calendar.txt`, `calendar_dates.txt`, etc.).
3. **Filter:** Keeps only rail-related routes (GTFS `route_type` 2 and extended types 100–109).
4. **Chunk processing:** Reads the massive `stop_times.txt` (~3 GB) in 500,000-row chunks to stay within memory limits.
5. **Calendar integration:** Merges weekday flags from `calendar.txt` and exception days from `calendar_dates.txt` to produce a human-readable `weekdays` column (e.g., `"Mon,Wed,Fri"`).
6. **Rolling stock enrichment:** Maps physical train properties (weight, carriages, max speed, power supply, gauge) from `data/rolling_stock_profiles.json` based on route name prefixes (IC, IR, S, RE, etc.).

**Input:** Internet connection, `data/rolling_stock_profiles.json`  
**Output:** `data/raw/gtfs/` (extracted GTFS files), `data/in_depth_schedules.csv`

---

### Step 7 — Create Master Dataset (`07_create_master_dataset.py`)

Bridges the gap between the live API snapshot (Step 3) and the full GTFS timetable (Step 6). It performs an inner join on:

- Station name ↔ Stop name
- Destination ↔ Trip headsign
- Departure time ↔ Departure time
- Category + Number ↔ Route short name

Once matched, it extracts the **full journey details** for every matched train (all intermediate stops, arrival/departure times, stop sequences), producing the final analysis-ready master dataset.

**Input:** `data/switzerland_schedules.csv`, `data/in_depth_schedules.csv`  
**Output:** `data/master_dataset.csv`

---

## 📊 Data Dictionary

### Generated Datasets

| File | Size | Description |
|------|------|-------------|
| `switzerland_tracks.geojson` | ~48 MB | GeoJSON of all rail track geometries in Switzerland |
| `switzerland_stations.geojson` | ~1.2 MB | GeoJSON of all station/halt point locations |
| `switzerland_schedules.csv` | ~44 KB | Live API snapshot of departures from 9 major stations |
| `switzerland.graphml` | ~172 MB | Directed routing graph (nodes + edges with attributes) |
| `in_depth_schedules.csv` | ~294 MB | Full GTFS schedules enriched with rolling stock physics |
| `master_dataset.csv` | ~7.8 MB | Merged API + GTFS dataset with full journey details |

### Master Dataset Columns

| Column | Source | Description |
|--------|--------|-------------|
| `trip_id` | GTFS | Unique identifier for each train journey |
| `route_short_name` | GTFS | Train category and number (e.g., `IC1`, `S8`, `IR36`) |
| `trip_headsign` | GTFS | Final destination displayed on the train |
| `stop_name` | GTFS | Name of the station at this stop |
| `arrival_time` | GTFS | Scheduled arrival time (`HH:MM:SS`) |
| `departure_time` | GTFS | Scheduled departure time (`HH:MM:SS`) |
| `stop_sequence` | GTFS | Order of this stop in the journey (1, 2, 3, ...) |
| `weight_tons` | Estimated | Train weight in metric tons |
| `carriages` | Estimated | Number of carriages |
| `max_speed_kmh` | Estimated | Maximum operating speed in km/h |
| `power_supply` | Estimated | Power type (`electric`) |
| `gauge` | Estimated | Track gauge in mm (1435 = standard, 1000 = narrow) |
| `weekdays` | GTFS | Days the train runs (e.g., `Mon,Tue,Wed,Thu,Fri`) |

> **Note on estimated fields:** Weight, carriages, max speed, power supply, and gauge are mapped from `rolling_stock_profiles.json` based on the route short name prefix. These are representative values for each train category, not per-vehicle measurements.

---

## 📋 Rolling Stock Profiles

The file `data/rolling_stock_profiles.json` maps Swiss train categories to their physical characteristics. This is a **hand-curated reference file** that is version-controlled. It includes profiles for:

| Category | Full Name | Type | Max Speed | Weight | Gauge |
|----------|-----------|------|-----------|--------|-------|
| ICE | InterCity Express | High-speed | 250 km/h | 450 t | 1435 mm |
| TGV | Train à Grande Vitesse | High-speed | 320 km/h | 380 t | 1435 mm |
| RJX | Railjet Xpress | High-speed | 230 km/h | 420 t | 1435 mm |
| IC | InterCity | Long-distance | 200 km/h | 400 t | 1435 mm |
| EC | EuroCity | Long-distance | 200 km/h | 400 t | 1435 mm |
| IR | InterRegio | Long-distance | 160 km/h | 350 t | 1435 mm |
| RE | RegioExpress | Regional | 160 km/h | 250 t | 1435 mm |
| S | S-Bahn | Regional | 120 km/h | 150 t | 1435 mm |
| R | Regio | Regional | 100 km/h | 100 t | 1435 mm |
| PE | Panorama Express | Tourist | 90 km/h | 200 t | 1000 mm |
| TER | Transport Express Régional | Regional | 160 km/h | 200 t | 1435 mm |
| DEFAULT | Standard Train | Regional | 120 km/h | 200 t | 1435 mm |

---

## ⚠️ Why is the `data/` folder mostly missing from GitHub?

The generated data files are excluded from version control via `.gitignore` because:

1. **File size:** The raw GTFS and OSM files alone exceed 3.8 GB — far beyond GitHub's 100 MB per-file limit.
2. **Reproducibility:** All data can be regenerated deterministically by running the pipeline scripts in order.
3. **Freshness:** Transport data changes frequently; it's better to re-download current data than commit stale snapshots.

The one exception is `data/rolling_stock_profiles.json`, which is a small (3.5 KB) hand-curated configuration file that the pipeline depends on and cannot be regenerated by code.

---

## 🔑 Environment Variables

The project uses a `.env` file (gitignored) for API credentials:

| Variable | Description |
|----------|-------------|
| `OJP_API_TOKEN` | Token for the Swiss Open Journey Planner (OJP) 2.0 API. Obtain one from [opentransportdata.swiss](https://opentransportdata.swiss/). Quota: 20,000 calls/day, rate limit: 50 calls/minute. |

> **Note:** The current pipeline scripts (Steps 1–7) use the free, unauthenticated `transport.opendata.ch` API for schedule data. The OJP token is reserved for future enhancements that may require the more detailed OJP 2.0 endpoint.

---

## 🔗 Data Sources

| Source | URL | Used By |
|--------|-----|---------|
| Geofabrik OSM Extracts | https://download.geofabrik.de/europe/switzerland.html | Step 1 |
| Swiss Open Transport API | https://transport.opendata.ch/ | Step 3 |
| Swiss GTFS Feed | https://opentransportdata.swiss/ | Step 6 |

---

## 🚀 How to Run the Pipeline

### Prerequisites

- **Python 3.8+**
- **~6 GB free disk space** (for raw downloads + processed outputs)
- **~2 GB RAM** minimum (Step 6 processes large files in chunks)
- **Stable internet connection** (downloads ~760 MB of data)

### Install Dependencies

```bash
pip install requests pandas geopandas pyrosm networkx matplotlib shapely
```

### Execute the Pipeline

Run the scripts in order from the project root:

```bash
python data_preparation/01_download_infrastructure.py
python data_preparation/02_extract_tracks_and_stations.py
python data_preparation/03_fetch_schedules.py
python data_preparation/04_visualize_network.py
python data_preparation/05_build_network_graph.py
python data_preparation/06_download_gtfs.py
python data_preparation/07_create_master_dataset.py
```

> **⏱️ Expected runtime:** Steps 1 and 6 involve large downloads and may take 10–30 minutes depending on your connection. Step 6 also requires significant processing time for the 3 GB `stop_times.txt` file.

---

## 🛡️ Scope & Limitations

- **Passenger trains only.** The GTFS feed and transport API cover scheduled passenger rail services. Freight trains are not included as their schedules are not publicly available.
- **Estimated rolling stock data.** Physical train properties (weight, speed, carriages) are approximations based on category, not per-vehicle telemetry.
- **Point-in-time API snapshots.** The `switzerland_schedules.csv` captures whatever is on the departure board at the moment the script runs. Running it at different times/days will yield different results.
- **Standard and narrow gauge only.** The OSM extraction filters for `rail` and `narrow_gauge` types. Funiculars, tramways, and rack railways are not included.
