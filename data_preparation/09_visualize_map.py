import os
import pandas as pd
import json

def get_api_key():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    return line.strip().split("=")[1].strip()
    return None

def generate_map():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "..", "data")
    master_path = os.path.join(data_dir, "master_dataset.csv")
    html_output_path = os.path.join(data_dir, "verification_map.html")
    
    api_key = get_api_key()
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY not found in .env")
        return

    print(f"Loading master dataset from {master_path}...")
    master_df = pd.read_csv(master_path)
    
    print("Extracting all unique train stations and metadata...")
    # Drop duplicates by stop_name to get a unique list of stations
    unique_stations_df = master_df.drop_duplicates(subset=['stop_name'])
    
    stations_to_plot = []
    
    for _, row in unique_stations_df.iterrows():
        stop_name = row['stop_name']
        lat = row['stop_lat']
        lon = row['stop_lon']
        platforms = row['platform_count']
        
        if pd.notna(lat) and pd.notna(lon):
            stations_to_plot.append({
                "lat": float(lat), 
                "lng": float(lon), 
                "title": f"{stop_name} | Platforms: {int(platforms)}",
                "name": stop_name,
                "platforms": int(platforms)
            })
            
    print(f"Extracted {len(stations_to_plot)} unique stations with metadata to plot.")
    
    # Center map on Switzerland
    center_lat = 46.8
    center_lng = 8.2

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARTEMIS Data Verification Map - Stations</title>
        <style>
            #map {{ height: 100vh; width: 100%; }}
            html, body {{ height: 100%; margin: 0; padding: 0; }}
            .info-window {{ font-family: Arial, sans-serif; padding: 5px; }}
            .info-window h3 {{ margin: 0 0 5px 0; font-size: 16px; color: #333; }}
            .info-window p {{ margin: 0; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                const map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 8,
                    center: {{ lat: {center_lat}, lng: {center_lng} }},
                    mapTypeId: 'terrain'
                }});
                
                // Load GeoJSON for world borders to dim out other countries and highlight Switzerland
                map.data.loadGeoJson('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson');
                map.data.setStyle(function(feature) {{
                    if (feature.getProperty('ADMIN') === 'Switzerland') {{
                        return {{
                            fillColor: 'transparent',
                            strokeColor: '#000000',
                            strokeWeight: 3,
                            zIndex: 10
                        }};
                    }} else {{
                        return {{
                            fillColor: '#000000',
                            fillOpacity: 0.4,
                            strokeWeight: 0,
                            zIndex: 1
                        }};
                    }}
                }});

                const stations = {json.dumps(stations_to_plot)};
                const infoWindow = new google.maps.InfoWindow();

                // Plot stations as lightweight SVG markers
                stations.forEach(loc => {{
                    const marker = new google.maps.Marker({{
                        position: loc,
                        map: map,
                        title: loc.title,
                        icon: {{
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 5,
                            fillColor: '#FF0000',
                            fillOpacity: 0.9,
                            strokeWeight: 1,
                            strokeColor: '#FFFFFF'
                        }}
                    }});
                    
                    // Add hover effect to open an InfoWindow with details
                    marker.addListener('mouseover', () => {{
                        const contentString = `
                            <div class="info-window">
                                <h3>${{loc.name}}</h3>
                                <p><strong>Platforms:</strong> ${{loc.platforms}}</p>
                            </div>
                        `;
                        infoWindow.setContent(contentString);
                        infoWindow.open(map, marker);
                    }});
                    
                    // Close the InfoWindow when the mouse leaves
                    marker.addListener('mouseout', () => {{
                        infoWindow.close();
                    }});
                }});
            }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
    </body>
    </html>
    """

    with open(html_output_path, 'w') as f:
        f.write(html_content)
        
    print(f"Station map with hover details generated successfully at: {html_output_path}")

if __name__ == "__main__":
    generate_map()
