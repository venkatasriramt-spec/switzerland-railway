import os
import requests

def download_file(url, output_path):
    print(f"Downloading {url} to {output_path}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 # 1 Megabyte
    downloaded = 0
    with open(output_path, 'wb') as f:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            f.write(data)
            if total_size > 0:
                percent = int((downloaded / total_size) * 100)
                print(f"Downloaded: {percent}%", end='\r')
    print("\nDownload complete.")

if __name__ == "__main__":
    url = "https://download.geofabrik.de/europe/switzerland-latest.osm.pbf"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "switzerland-latest.osm.pbf")
    
    if os.path.exists(output_file):
        print(f"File {output_file} already exists. Skipping download.")
    else:
        download_file(url, output_file)
