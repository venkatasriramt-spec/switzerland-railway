import json
import psutil
import os
import gc

process = psutil.Process(os.getpid())
print(f"Memory before load: {process.memory_info().rss / 1e9:.2f} GB")

with open("data/compiled_routes.json", "r") as f:
    routes = json.load(f)
print(f"Memory after load: {process.memory_info().rss / 1e9:.2f} GB")

train_data = []
for k in list(routes.keys())[:500]:
    train_data.append(routes[k].get('segments', []))

del routes
gc.collect()

print(f"Memory after cleanup: {process.memory_info().rss / 1e9:.2f} GB")
