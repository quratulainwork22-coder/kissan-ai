"""Virtual ESP32 sensor node.
Sends SYNTHETIC readings to Kissan AI for demonstration without hardware.

Usage:
    python iot/simulator.py --scenario normal
    python iot/simulator.py --scenario humid   (triggers whitefly/leaf curl risk alert)
    python iot/simulator.py --scenario dry     (triggers low soil moisture alert)
"""
import argparse
import random
import time

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:5000/api/readings")
parser.add_argument("--key", default="demo-key-123")
parser.add_argument("--interval", type=float, default=5)
parser.add_argument("--scenario", choices=["normal", "humid", "dry"], default="normal")
args = parser.parse_args()

temp, hum, soil = 30.0, 55.0, 45.0
targets = {"normal": (31, 55, 45), "humid": (32, 88, 50), "dry": (36, 35, 12)}

print(f"Sending synthetic '{args.scenario}' readings to {args.url} (Ctrl+C to stop)")
while True:
    t_target, h_target, s_target = targets[args.scenario]
    temp += (t_target - temp) * 0.3 + random.uniform(-0.5, 0.5)
    hum += (h_target - hum) * 0.3 + random.uniform(-2, 2)
    soil += (s_target - soil) * 0.3 + random.uniform(-1, 1)
    hum = max(0, min(100, hum))
    soil = max(0, min(100, soil))
    payload = {"temperature": round(temp, 1), "humidity": round(hum, 1),
               "soil_moisture": round(soil, 1)}
    try:
        r = requests.post(args.url, json=payload, headers={"X-API-Key": args.key}, timeout=5)
        print(r.status_code, payload)
    except requests.RequestException as e:
        print("Server not reachable:", e)
    time.sleep(args.interval)
