import json
import pickle
import sys

with open("data/compiled_routes.json", "r") as f:
    routes = json.load(f)
    
train_data = []
for k in list(routes.keys())[:500]:
    train_data.append(routes[k].get('segments', []))

p = pickle.dumps(train_data)
print(f"Size of 500 trains segments: {len(p) / 1024 / 1024:.2f} MB")
