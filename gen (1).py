import subprocess
import csv
import time
import os

def generate_traffic(url, num_requests, concurrency):
    """
    Generate traffic using the 'hey' tool and collect the output.

    :param url: The URL to generate traffic for.
    :param num_requests: The total number of requests to make.
    :param concurrency: The number of concurrent requests.
    :return: A dictionary with parsed metrics.
    """
    # Run the hey command to generate traffic
    command = f"hey -n {num_requests} -c {concurrency} {url}"
    
    # Capture the output of the command
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error generating traffic")
        print(result.stderr)
        return None
    
    # Parse the output and extract key metrics
    output = result.stdout
    metrics = parse_output(output)
    
    # Add concurrent requests value
    metrics['Concurrent requests'] = concurrency
    
    # Remove Timestamp and Number of requests
    metrics.pop('Timestamp', None)
    metrics.pop('Number of requests', None)
    
    # Add Status 500 handling like Status 200
    if 'Status 500' not in metrics:
        metrics['Status 500'] = 0  # Default to 0 if no Status 500 found
    
    return metrics

def parse_output(output):
    """
    Parse the output of the 'hey' command and extract only the specific requested metrics.

    :param output: The output text from the 'hey' tool.
    :return: A dictionary containing the requested metrics.
    """
    metrics = {
        'Requests/sec': 0,
        'Size/request': 0,
        'Status 200': 0,
        'Status 500': 0,
        'Concurrent requests': 0,
        '10th percentile': 0,
        '50th percentile': 0,
        '75th percentile': 0,
        '90th percentile': 0,
        '99th percentile': 0
    }
    
    lines = output.splitlines()
    
    # Find and extract specific metrics the user wants
    for line in lines:
        line = line.strip()
        
        # Extract Requests/sec
        if "Requests/sec:" in line:
            metrics['Requests/sec'] = line.split("Requests/sec:")[1].strip()
        
        # Extract Size/request
        elif "Size/request:" in line:
            metrics['Size/request'] = line.split("Size/request:")[1].strip()
        
        # Extract Number of requests (this is shown as a summary at the bottom)
        elif line.startswith("[") and "responses" in line:
            status_code = line.split("]")[0].replace("[", "").strip()
            count = line.split("]")[1].split("responses")[0].strip()
            metrics[f'Status {status_code}'] = count  # Save status code distribution
        
        # Extract specific percentiles (10th, 50th, 75th, 90th, 99th)
        elif "% in" in line and "secs" in line:
            parts = line.strip().split("%")
            if len(parts) > 1:
                percentile = parts[0].strip()
                if percentile in ['10', '50', '75', '90', '99']:  # Only capture these specific percentiles
                    value = parts[1].split("in")[1].split("secs")[0].strip()
                    metrics[f'{percentile}th percentile'] = value
    
    return metrics

def get_hpa_replicas(namespace="openfaas-fn"):
    """
    Get the number of replicas from the Horizontal Pod Autoscaler (HPA) in a given namespace.
    
    :param namespace: The namespace to check the HPA for.
    :return: The number of replicas.
    """
    # Run the kubectl command to get HPA information
    command = f"kubectl get hpa -n {namespace}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error fetching HPA data")
        print(result.stderr)
        return None
    
    # Parse the result to extract the number of replicas
    output = result.stdout
    replicas = parse_hpa_output(output)
    return replicas

def parse_hpa_output(output):
    """
    Parse the output of the kubectl get hpa command and extract the number of replicas.
    
    :param output: The output text from the kubectl get hpa command.
    :return: The number of replicas.
    """
    replicas = {}
    lines = output.splitlines()
    
    # Skip the header line
    if len(lines) > 1:
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                current_replicas = parts[6]
                
                replicas[name] = {
                    'current': current_replicas
                }
    
    return replicas

def store_metrics(metrics, file_path="data2.csv"):
    """
    Store the collected metrics into a CSV file.

    :param metrics: A dictionary containing the metrics.
    :param file_path: The path to the CSV file.
    """
    # Check if file exists, to write headers
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=metrics.keys())
        
        # Write header if the file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Write the data
        writer.writerow(metrics)

def run_traffic_and_collect_data():
    """
    Main function: loops through request and concurrency values, collects and stores metrics.
    """
    url = "http://192.168.49.2:31112/function/hello"  # Replace with your service URL
    num_requests_list = [400, 800, 1000, 1500, 1600, 1800, 2000, 2400, 2700, 3600, 4000, 4500, 5000,5500,6000,6500,7000,8000,9000,10000,15000,20000,25000]
    concurrency_list = [10, 20, 50, 70, 80, 100, 125, 135, 160, 180, 200,300,400,500,1000]

    for num_requests in num_requests_list:
        for concurrency in concurrency_list:
            print(f"\nRunning test with {num_requests} requests and concurrency {concurrency}")

            metrics = generate_traffic(url, num_requests, concurrency)

            if metrics:
                replicas_data = get_hpa_replicas(namespace="openfaas-fn")
                if replicas_data:
                    for name, data in replicas_data.items():
                        metrics[f'{name} - Current replicas'] = data['current']

                store_metrics(metrics)
                print("Metrics recorded.")
            else:
                print("Failed to generate traffic data.")

            # Optional: delay to allow autoscaling to respond
            time.sleep(10)

if __name__ == "__main__":
    run_traffic_and_collect_data()

