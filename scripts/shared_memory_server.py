import json
import redis
import time
import os

print("Starting Shared Memory Server (Redis)...")

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Successfully connected to Redis.")
except redis.ConnectionError:
    print("ERROR: Cannot connect to Redis. Is the redis-server running?")
    exit(1)

file_path = "data/compiled_routes.json"
print(f"Loading {file_path} into memory...")
if not os.path.exists(file_path):
    print(f"ERROR: {file_path} not found.")
    exit(1)

start_time = time.time()
with open(file_path, "r") as f:
    compiled_routes = json.load(f)
print(f"File parsed in {time.time() - start_time:.2f} seconds.")

print("Injecting data into Redis (this may take a minute)...")
start_time = time.time()

# Use pipeline for massive speedup
pipe = r.pipeline()
count = 0

for trip_id, route_edges in compiled_routes.items():
    # Store each trip's route as a separate key to avoid one massive JSON blob
    # Convert list to JSON string for storage
    pipe.set(f"route:{trip_id}", json.dumps(route_edges))
    count += 1
    
    # Execute pipeline in batches of 1000
    if count % 1000 == 0:
        pipe.execute()
        print(f"Injected {count} routes...")

# Execute remaining
pipe.execute()
print(f"Successfully injected {count} routes into Redis in {time.time() - start_time:.2f} seconds!")
print("The topology graph is now available in shared memory for all Dispatcher parallel CPU cores.")
print("You can leave this script running or exit; Redis will keep the data in memory.")
