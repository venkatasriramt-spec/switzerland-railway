import os
import geopandas as gpd
import matplotlib.pyplot as plt

def visualize_network(tracks_path, stations_path, output_image_path):
    print("Loading tracks...")
    tracks = gpd.read_file(tracks_path)
    
    print("Loading stations...")
    stations = gpd.read_file(stations_path)
    
    print("Creating map visualization...")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Set background color to a dark theme for a better look
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')
    
    # Plot tracks (light blue/grey lines)
    tracks.plot(ax=ax, color='#89b4fa', linewidth=0.5, alpha=0.7)
    
    # Plot stations (red/orange dots)
    stations.plot(ax=ax, color='#f38ba8', markersize=2, alpha=0.8)
    
    # Remove axes for a cleaner map look
    ax.axis('off')
    
    plt.title("Switzerland Railway Network & Stations", color='white', fontsize=16, pad=20)
    plt.tight_layout()
    
    print(f"Saving map to {output_image_path}...")
    plt.savefig(output_image_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    
    print("Visualization complete.")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    tracks_file = os.path.join(base_dir, "..", "data", "switzerland_tracks.geojson")
    stations_file = os.path.join(base_dir, "..", "data", "switzerland_stations.geojson")
    
    output_image = os.path.join(base_dir, "..", "data", "switzerland_railway_map.png")
    
    if not os.path.exists(tracks_file) or not os.path.exists(stations_file):
        print("Data files not found. Please run the extraction script first.")
    else:
        visualize_network(tracks_file, stations_file, output_image)
