import json
import pandas as pd
import os

def main():
    print("Starting data preprocessing...")
    
    # 1. Load the master dataset to get the first 500 trip IDs
    master_df = pd.read_csv('data/master_dataset.csv')
    unique_trips = master_df['trip_id'].unique()
    
    # The training script is hardcoded to 500 trains right now
    num_trains = 500
    target_trips = unique_trips[:num_trains]
    print(f"Extracting route data for {num_trains} specific trips out of {len(unique_trips)}...")
    
    # 2. Load the massive 1.6GB JSON file ONCE
    print("Loading 1.6GB compiled_routes.json into memory (this will take ~20 seconds)...")
    with open('data/compiled_routes.json', 'r') as f:
        routes = json.load(f)
        
    print("JSON loaded successfully. Extracting mini-dataset...")
    
    # 3. Create the mini dictionary
    mini_routes = {}
    for trip_id in target_trips:
        if trip_id in routes:
            # We only need 'total_distance_m' and 'segments'
            mini_routes[trip_id] = {
                'total_distance_m': routes[trip_id].get('total_distance_m', 100000.0),
                'segments': routes[trip_id].get('segments', [])
            }
            
    # 4. Save to a much smaller JSON file
    print("Writing data/mini_routes.json...")
    with open('data/mini_routes.json', 'w') as f:
        json.dump(mini_routes, f)
        
    print(f"Data preprocessing complete! Extracted {len(mini_routes)} routes.")

if __name__ == "__main__":
    main()
