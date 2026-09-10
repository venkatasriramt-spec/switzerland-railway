import pandas as pd
import os

def create_master_dataset():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    api_csv_path = os.path.join(data_dir, "switzerland_schedules.csv")
    gtfs_csv_path = os.path.join(data_dir, "in_depth_schedules.csv")
    output_path = os.path.join(data_dir, "master_dataset.csv")

    print("Loading datasets...")
    api_df = pd.read_csv(api_csv_path)
    gtfs_df = pd.read_csv(gtfs_csv_path)

    print("Preparing mapping keys for API dataset...")
    # Clean column names (remove padding)
    api_df.columns = api_df.columns.str.strip()
    
    # 1. Clean station names (stripping extra whitespace)
    api_df['station'] = api_df['station'].str.strip()
    api_df['destination'] = api_df['destination'].str.strip()
    
    # 2. Extract HH:MM:SS from departure_time string (e.g. '2026-09-07T17:55:00+0200' -> '17:55:00')
    api_df['departure_time_clean'] = api_df['departure_time'].str.extract(r'T(\d{2}:\d{2}:\d{2})')
    
    # 3. Create route_short_name by combining category and number
    api_df['route_short_name_match'] = api_df['train_category'].str.strip() + api_df['train_number'].astype(str).str.strip()

    print("Preparing mapping keys for GTFS dataset...")
    # Ensure no leading/trailing spaces in GTFS matching columns
    gtfs_df['stop_name'] = gtfs_df['stop_name'].str.strip()
    gtfs_df['trip_headsign'] = gtfs_df['trip_headsign'].str.strip()
    gtfs_df['route_short_name'] = gtfs_df['route_short_name'].astype(str).str.strip()

    print("Mapping API snapshots to full GTFS journeys...")
    # Perform a left join to attach GTFS trip information to the original API rows
    master_df = api_df.merge(
        gtfs_df,
        how='inner',
        left_on=['station', 'destination', 'departure_time_clean', 'route_short_name_match'],
        right_on=['stop_name', 'trip_headsign', 'departure_time', 'route_short_name']
    )

    # After finding the trip_id for each train in the API snapshot, we can optionally
    # extract the FULL journey for each of those matched trains.
    matched_trip_ids = master_df['trip_id'].unique()
    
    print(f"Successfully matched {len(matched_trip_ids)} unique trains.")
    print("Extracting full journey details for matched trains...")
    
    final_master_df = gtfs_df[gtfs_df['trip_id'].isin(matched_trip_ids)].copy()
    final_master_df.sort_values(by=['trip_id', 'stop_sequence'], inplace=True)

    print(f"Exporting master dataset ({len(final_master_df)} rows) to {output_path}...")
    final_master_df.to_csv(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    create_master_dataset()
