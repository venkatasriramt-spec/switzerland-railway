import os
import geopandas as gpd
from pyrosm import get_data, OSM

def extract_infrastructure(pbf_path, output_dir):
    print(f"Loading OSM data from {pbf_path}...")
    osm = OSM(pbf_path)
    
    print("Extracting railway tracks...")
    # Extract railway tracks (rail, narrow_gauge)
    custom_filter = {'railway': ['rail', 'narrow_gauge']}
    tracks = osm.get_data_by_custom_criteria(custom_filter=custom_filter,
                                        filter_type="keep",
                                        keep_nodes=False, 
                                        keep_ways=True, 
                                        keep_relations=False)
    
    if tracks is not None and not tracks.empty:
        tracks_file = os.path.join(output_dir, "switzerland_tracks.geojson")
        print(f"Saving {len(tracks)} track segments to {tracks_file}...")
        tracks.to_file(tracks_file, driver='GeoJSON')
    else:
        print("No tracks found.")
        
    print("Extracting train stations...")
    # Extract train stations and halts
    station_filter = {'railway': ['station', 'halt']}
    stations = osm.get_data_by_custom_criteria(custom_filter=station_filter,
                                        filter_type="keep",
                                        keep_nodes=True, 
                                        keep_ways=True, 
                                        keep_relations=False)
    
    if stations is not None and not stations.empty:
        # Convert polygons to centroids for simplicity if any
        stations['geometry'] = stations['geometry'].centroid
        stations_file = os.path.join(output_dir, "switzerland_stations.geojson")
        print(f"Saving {len(stations)} stations to {stations_file}...")
        stations.to_file(stations_file, driver='GeoJSON')
    else:
        print("No stations found.")
        
    print("Extraction complete.")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    pbf_file = os.path.join(base_dir, "..", "data", "raw", "switzerland-latest.osm.pbf")
    output_directory = os.path.join(base_dir, "..", "data")
    
    if not os.path.exists(pbf_file):
        print(f"Error: PBF file not found at {pbf_file}. Please run 01_download_infrastructure.py first.")
    else:
        extract_infrastructure(pbf_file, output_directory)
