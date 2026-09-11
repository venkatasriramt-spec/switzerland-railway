import os
import pandas as pd
import numpy as np

def add_station_metadata():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "..", "data")
    stops_path = os.path.join(data_dir, "raw", "gtfs", "stops.txt")
    master_path = os.path.join(data_dir, "master_dataset.csv")

    print(f"Loading raw stops from {stops_path}...")
    # Read stops.txt; ensure platform_code is read as string to handle '1', '2A', etc.
    stops = pd.read_csv(stops_path, dtype={'platform_code': str})

    print(f"Loading master dataset from {master_path}...")
    master_df = pd.read_csv(master_path)

    # 1. Extract exact coordinates for each station
    # Since multiple platforms might have slightly different coordinates, we group by stop_name 
    # and just take the first coordinate (or mean). First is fine.
    print("Extracting exact station coordinates...")
    station_coords = stops.groupby('stop_name').agg({
        'stop_lat': 'first',
        'stop_lon': 'first'
    }).reset_index()

    # 2. Extract platform counts
    print("Calculating platform counts per station...")
    # We want to count unique, non-null platform codes per stop_name
    # First, filter out nulls
    platforms_only = stops.dropna(subset=['platform_code'])
    # Count unique platform codes per stop_name
    platform_counts = platforms_only.groupby('stop_name')['platform_code'].nunique().reset_index()
    platform_counts.rename(columns={'platform_code': 'platform_count'}, inplace=True)

    # Merge coords and counts
    station_meta = pd.merge(station_coords, platform_counts, on='stop_name', how='left')
    
    # If a station had no platforms explicitly defined in GTFS, it has at least 1 platform
    station_meta['platform_count'] = station_meta['platform_count'].fillna(1).astype(int)

    # 3. Enrich the Master Dataset
    print("Merging metadata into the master dataset...")
    # Drop them if they already exist so we can run the script safely multiple times
    for col in ['stop_lat', 'stop_lon', 'platform_count']:
        if col in master_df.columns:
            master_df = master_df.drop(columns=[col])

    master_df = pd.merge(master_df, station_meta, on='stop_name', how='left')

    # Reorder columns to put the new metadata near the stop_name and graph_node_id
    cols = master_df.columns.tolist()
    
    # We want order: ... , stop_name, stop_lat, stop_lon, platform_count, ... , graph_node_id
    if 'stop_name' in cols:
        base_idx = cols.index('stop_name')
        # Move the 3 new cols right after stop_name
        cols.remove('stop_lat')
        cols.remove('stop_lon')
        cols.remove('platform_count')
        
        cols.insert(base_idx + 1, 'stop_lat')
        cols.insert(base_idx + 2, 'stop_lon')
        cols.insert(base_idx + 3, 'platform_count')
        
        master_df = master_df[cols]

    print(f"Exporting updated master dataset ({len(master_df)} rows) back to {master_path}...")
    master_df.to_csv(master_path, index=False)
    
    print("Done! Station coordinates and platform counts have been added.")
    
if __name__ == "__main__":
    add_station_metadata()
