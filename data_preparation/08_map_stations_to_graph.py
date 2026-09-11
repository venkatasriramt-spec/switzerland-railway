import os
import pandas as pd
import networkx as nx
from scipy.spatial import cKDTree
import numpy as np
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def map_stations_to_graph():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "..", "data")
    graph_path = os.path.join(data_dir, "switzerland.graphml")
    stops_path = os.path.join(data_dir, "raw", "gtfs", "stops.txt")
    master_csv_path = os.path.join(data_dir, "master_dataset.csv")
    mapping_csv_path = os.path.join(data_dir, "station_to_node_mapping.csv")

    print(f"Loading track graph from {graph_path} (this may take a minute)...")
    # Using NetworkX to load the graph
    G = nx.read_graphml(graph_path)
    
    print(f"Graph loaded with {G.number_of_nodes()} nodes.")
    
    # Extract node coordinates
    node_ids = []
    coords_lon_lat = []
    
    for node, data in G.nodes(data=True):
        if 'x' in data and 'y' in data:
            node_ids.append(node)
            coords_lon_lat.append([float(data['x']), float(data['y'])])
            
    coords_lon_lat = np.array(coords_lon_lat)
    
    print("Building spatial KDTree...")
    # cKDTree on (lon, lat) is an approximation, but perfectly fine for finding the nearest neighbor over short distances
    tree = cKDTree(coords_lon_lat)
    
    print(f"Loading GTFS stops from {stops_path}...")
    stops = pd.read_csv(stops_path)
    # Some GTFS feeds have station hierarchies. We just need unique stop coordinates.
    # We will map each stop_id and stop_name.
    
    print("Snapping stations to nearest graph node...")
    
    mapped_nodes = []
    distances = []
    
    for idx, row in stops.iterrows():
        lon, lat = row['stop_lon'], row['stop_lat']
        # Query KDTree for nearest node
        dist_approx, neighbor_idx = tree.query([lon, lat])
        nearest_node_id = node_ids[neighbor_idx]
        nearest_lon, nearest_lat = coords_lon_lat[neighbor_idx]
        
        # Calculate true haversine distance in meters
        dist_meters = haversine(lat, lon, nearest_lat, nearest_lon)
        mapped_nodes.append(nearest_node_id)
        distances.append(dist_meters)
        
    stops['graph_node_id'] = mapped_nodes
    stops['snap_distance_meters'] = distances
    
    # Do not filter out any stops based on distance. Keep everything.
    valid_stops = stops.copy()
    
    print(f"Mapped all {len(valid_stops)} stations.")
    
    print(f"Exporting mapping to {mapping_csv_path}...")
    valid_stops.to_csv(mapping_csv_path, index=False)
    
    print(f"Updating {master_csv_path} with graph node IDs...")
    master_df = pd.read_csv(master_csv_path)
    
    mapping_dict = valid_stops.groupby('stop_name').first()['graph_node_id'].to_dict()
    master_df['graph_node_id'] = master_df['stop_name'].map(mapping_dict)
    
    # We are no longer dropping any rows, even if they failed to map or snapped far away.
    master_df.to_csv(master_csv_path, index=False)
    print("Done! Master dataset is now linked to the track graph with its original size intact.")

if __name__ == "__main__":
    map_stations_to_graph()
