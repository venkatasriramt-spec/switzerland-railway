import pandas as pd
import json

def split_regions():
    print("Reading master_dataset.csv...")
    df = pd.read_csv("data/master_dataset.csv")
    
    # Simple bounding box logic for Switzerland
    # Center is roughly lat=46.8, lon=8.2
    center_lat = 46.8
    center_lon = 8.2
    
    def assign_region(row):
        lat = row['stop_lat']
        lon = row['stop_lon']
        if lat > center_lat and lon > center_lon:
            return "Northeast"
        elif lat > center_lat and lon <= center_lon:
            return "Northwest"
        elif lat <= center_lat and lon > center_lon:
            return "Southeast"
        else:
            return "Southwest"
            
    # Group by trip_id to get the starting station coordinates for each train
    first_stops = df.sort_values('stop_sequence').groupby('trip_id').first().reset_index()
    first_stops['region'] = first_stops.apply(assign_region, axis=1)
    
    regions = {}
    for region_name, group in first_stops.groupby('region'):
        trip_ids = group['trip_id'].tolist()
        regions[region_name] = trip_ids
        print(f"Region {region_name}: {len(trip_ids)} trains")
        
    with open("data/regions.json", "w") as f:
        json.dump(regions, f, indent=4)
        
    print("Successfully saved data/regions.json")

if __name__ == "__main__":
    split_regions()
