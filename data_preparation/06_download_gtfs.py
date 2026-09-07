import os
import requests
import zipfile
import pandas as pd
import json

def download_and_extract_gtfs(url, data_dir):
    zip_path = os.path.join(data_dir, "raw", "ch_gtfs.zip")
    extract_dir = os.path.join(data_dir, "raw", "gtfs")
    
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)
    
    if not os.path.exists(zip_path):
        print(f"Downloading GTFS feed from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    else:
        print("GTFS zip already exists.")
        
    print("Extracting GTFS files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return extract_dir

def process_gtfs(gtfs_dir, output_file, rolling_stock_file):
    print("Loading Rolling Stock Profiles...")
    with open(rolling_stock_file, 'r') as f:
        rolling_stock = json.load(f)['profiles']
        
    print("Loading GTFS routes and identifying trains...")
    routes = pd.read_csv(os.path.join(gtfs_dir, "routes.txt"))
    # GTFS route_type: 2 is Rail, 100 is Railway Service (extended)
    train_routes = routes[routes['route_type'].isin([2, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109])]
    
    print("Loading trips...")
    trips = pd.read_csv(os.path.join(gtfs_dir, "trips.txt"))
    train_trips = trips[trips['route_id'].isin(train_routes['route_id'])]
    
    print("Loading stops...")
    stops = pd.read_csv(os.path.join(gtfs_dir, "stops.txt"))
    
    print("Processing stop times (this might take a while)...")
    # Process stop_times in chunks to save memory
    stop_times_iter = pd.read_csv(os.path.join(gtfs_dir, "stop_times.txt"), chunksize=500000)
    processed_chunks = []
    
    for chunk in stop_times_iter:
        # Keep only stop times for our train trips
        train_stop_times = chunk[chunk['trip_id'].isin(train_trips['trip_id'])]
        processed_chunks.append(train_stop_times)
        
    all_stop_times = pd.concat(processed_chunks)
    
    print("Merging data...")
    # Merge stop times with trips
    merged = all_stop_times.merge(train_trips, on="trip_id")
    # Merge with routes
    merged = merged.merge(train_routes, on="route_id")
    # Merge with stops
    merged = merged.merge(stops, on="stop_id")
    
    # Map the train physics based on the route short name (e.g. 'IC', 'IR', 'S')
    def get_physics(short_name, key):
        if pd.isna(short_name):
            return rolling_stock['DEFAULT'][key]
        for prefix in rolling_stock.keys():
            if str(short_name).startswith(prefix):
                return rolling_stock[prefix][key]
        return rolling_stock['DEFAULT'][key]

    print("Mapping physical properties...")
    merged['weight_tons'] = merged['route_short_name'].apply(lambda x: get_physics(x, 'weight_tons'))
    merged['carriages'] = merged['route_short_name'].apply(lambda x: get_physics(x, 'carriages'))
    merged['max_speed_kmh'] = merged['route_short_name'].apply(lambda x: get_physics(x, 'max_speed_kmh'))
    merged['power_supply'] = merged['route_short_name'].apply(lambda x: get_physics(x, 'power'))
    merged['gauge'] = merged['route_short_name'].apply(lambda x: get_physics(x, 'gauge'))
    
    # Select relevant columns for the in-depth schedule
    final_df = merged[[
        'route_short_name', 'route_long_name', 'trip_headsign', 
        'stop_name', 'arrival_time', 'departure_time', 'stop_sequence',
        'weight_tons', 'carriages', 'max_speed_kmh', 'power_supply', 'gauge'
    ]]
    
    final_df.sort_values(by=['route_short_name', 'arrival_time'], inplace=True)
    
    print(f"Exporting {len(final_df)} records to {output_file}...")
    final_df.to_csv(output_file, index=False)
    print("Done!")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "..", "data")
    rolling_stock = os.path.join(data_dir, "rolling_stock_profiles.json")
    output = os.path.join(data_dir, "in_depth_schedules.csv")
    
    # Official Swiss GTFS Permalink
    gtfs_url = "https://data.opentransportdata.swiss/en/dataset/timetable-2026-gtfs2020/permalink"
    
    # Note: Downloading the real GTFS takes several minutes and uses >1GB memory.
    # We will simulate the download logic here if the user's connection fails.
    try:
        extract_dir = download_and_extract_gtfs(gtfs_url, data_dir)
        process_gtfs(extract_dir, output, rolling_stock)
    except Exception as e:
        print(f"GTFS Download/Processing Failed: {e}")
        print("Note: The full Swiss GTFS feed is very large. If the download times out, manually download the ZIP from opentransportdata.swiss, place it in data/raw/ch_gtfs.zip, and re-run this script.")
