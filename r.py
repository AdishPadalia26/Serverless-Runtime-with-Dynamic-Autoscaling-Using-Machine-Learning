import subprocess
import requests
import re
import os
import csv
import time
from datetime import datetime

# --- Feature order from model training ---
features_order = [
    "Requests/sec", "Size/request", "Concurrent requests",
    "10th percentile", "50th percentile", "75th percentile",
    "90th percentile", "99th percentile", "error_rate"
]

# --- Define independent test cases ---
test_cases = [
    {"n": 500, "c": 10},
    {"n": 1000, "c": 20},
    {"n": 1500, "c": 30},
    {"n": 2000, "c": 40},
    {"n": 2500, "c": 50},
]

def run_hey(url, n, c):
    cmd = f"hey -n {n} -c {c} {url}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def parse_hey_output(output, concurrency):
    metrics = {f: 0 for f in features_order}
    metrics["Concurrent requests"] = concurrency
    s200 = s500 = 0

    for line in output.splitlines():
        if "Requests/sec:" in line:
            metrics["Requests/sec"] = float(line.split(":")[1])
        elif "Size/request:" in line:
            metrics["Size/request"] = float(line.split(":")[1].split()[0])
        elif "[200]" in line:
            s200 = int(line.split()[1])
        elif "[500]" in line:
            s500 = int(line.split()[1])
        elif "10%" in line:
            metrics["10th percentile"] = float(re.findall(r"[\d.]+", line)[0])
        elif "50%" in line:
            metrics["50th percentile"] = float(re.findall(r"[\d.]+", line)[0])
        elif "75%" in line:
            metrics["75th percentile"] = float(re.findall(r"[\d.]+", line)[0])
        elif "90%" in line:
            metrics["90th percentile"] = float(re.findall(r"[\d.]+", line)[0])
        elif "99%" in line:
            metrics["99th percentile"] = float(re.findall(r"[\d.]+", line)[0])

    total = s200 + s500
    metrics["error_rate"] = s500 / total if total > 0 else 0
    return metrics

def predict_replicas(metrics):
    res = requests.post("http://localhost:5000/predict", json=metrics)
    return int(res.json()["replicas"])

def scale_k8s(replicas):
    cmd = f"kubectl scale deployment hello --replicas={replicas} -n openfaas-fn"
    subprocess.run(cmd, shell=True)

def log_to_csv(metrics, replicas):
    metrics["replicas"] = replicas
    metrics["timestamp"] = datetime.now().isoformat()
    log_file = "log.csv"
    write_header = not os.path.exists(log_file)
    with open(log_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metrics.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(metrics)

# --- Independent Execution Loop ---
for i, case in enumerate(test_cases, start=1):
    print(f"\n🔁 Test Case {i}: {case['n']} requests @ {case['c']} concurrency")
    hey_output = run_hey("http://192.168.49.2:31112/function/hello", case["n"], case["c"])
    metrics = parse_hey_output(hey_output, case["c"])
    predicted = predict_replicas(metrics)
    scale_k8s(predicted)
    log_to_csv(metrics, predicted)
    print(f"✅ Scaled to {predicted} replicas.")
    time.sleep(30)
