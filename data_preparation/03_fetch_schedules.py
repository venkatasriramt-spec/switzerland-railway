import os
import requests
import pandas as pd
import time

def fetch_station_board(station_name, limit=50):
    """Fetches the departure board for a given Swiss station."""
    url = f"http://transport.opendata.ch/v1/stationboard?station={station_name}&limit={limit}"
    print(f"Fetching schedules for {station_name}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        stationboard = data.get('stationboard', [])
        records = []
        for entry in stationboard:
            stop = entry.get('stop', {})
            records.append({
                'station': data.get('station', {}).get('name', station_name),
                'departure_time': stop.get('departure'),
                'platform': stop.get('platform'),
                'train_category': entry.get('category'),
                'train_number': entry.get('number'),
                'operator': entry.get('operator'),
                'destination': entry.get('to')
            })
        return records
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {station_name}: {e}")
        return []

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # List of major Swiss railway hubs
    major_stations = [
        "Zürich HB", 
        "Bern", 
        "Basel SBB", 
        "Genève", 
        "Lausanne", 
        "Luzern",
        "Winterthur",
        "St. Gallen",
        "Lugano"
    ]
    
    all_schedules = []
    
    for station in major_stations:
        schedules = fetch_station_board(station, limit=50)
        all_schedules.extend(schedules)
        # Polite delay to avoid rate limiting
        time.sleep(1)
        
    if all_schedules:
        df = pd.DataFrame(all_schedules)
        output_file = os.path.join(output_dir, "switzerland_schedules.csv")
        df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(all_schedules)} schedule entries to {output_file}")
    else:
        print("No schedules were fetched.")
