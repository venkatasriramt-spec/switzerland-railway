import os
import json
import networkx as nx
import geopandas as gpd
from shapely.geometry import MultiLineString, LineString

def coord_to_node_id(coord):
    """Converts a (lon, lat) coordinate to a full-precision string ID."""
    # Using full precision as specified in the project report
    return f"{coord[0]:.15f},{coord[1]:.15f}"

def build_graph(tracks_path, output_graphml_path):
    print(f"Loading tracks from {tracks_path}...")
    try:
        tracks = gpd.read_file(tracks_path)
    except Exception as e:
        print(f"Error loading tracks: {e}")
        return

    print("Building directed network graph...")
    G = nx.DiGraph()

    # Explode MultiLineStrings into individual LineStrings to preserve connectivity
    print("Exploding MultiLineString geometries...")
    exploded_tracks = tracks.explode(index_parts=True)
    
    # Only keep LineStrings
    lines = exploded_tracks[exploded_tracks.geometry.type == 'LineString']
    print(f"Processing {len(lines)} LineString segments...")

    for idx, row in lines.iterrows():
        coords = list(row.geometry.coords)
        if len(coords) < 2:
            continue
            
        # Add edges between consecutive coordinates in the LineString
        for i in range(len(coords) - 1):
            u_coord = coords[i]
            v_coord = coords[i+1]
            
            u_id = coord_to_node_id(u_coord)
            v_id = coord_to_node_id(v_coord)
            
            # Add nodes with their coordinates as attributes
            if u_id not in G:
                G.add_node(u_id, x=u_coord[0], y=u_coord[1])
            if v_id not in G:
                G.add_node(v_id, x=v_coord[0], y=v_coord[1])
            
            # Extract basic edge attributes from the nested 'tags' dictionary
            edge_attrs = {}
            if 'tags' in row and not pd.isna(row['tags']) and isinstance(row['tags'], dict):
                tags_dict = row['tags']
                for col in ['maxspeed', 'gauge', 'electrified', 'railway', 'tracks']:
                    if col in tags_dict:
                        edge_attrs[col] = str(tags_dict[col])
                        
            # Add bidirectional edges for railway tracks
            G.add_edge(u_id, v_id, **edge_attrs)
            G.add_edge(v_id, u_id, **edge_attrs)

    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    print(f"Exporting to {output_graphml_path}...")
    nx.write_graphml(G, output_graphml_path)
    print("Export complete.")

if __name__ == "__main__":
    import pandas as pd # Needed for pd.isna
    base_dir = os.path.dirname(__file__)
    tracks_file = os.path.join(base_dir, "..", "data", "switzerland_tracks.geojson")
    output_file = os.path.join(base_dir, "..", "data", "switzerland.graphml")
    
    if not os.path.exists(tracks_file):
        print(f"Tracks file not found at {tracks_file}. Please run extraction script first.")
    else:
        build_graph(tracks_file, output_file)
