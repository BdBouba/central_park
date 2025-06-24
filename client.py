import argparse
import json
import requests
import time

def send_data(identifier, data):
    url = "http://localhost:5000/data"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"Data sent successfully for client {identifier}")
        else:
            print(f"Failed to send data for client {identifier}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data for client {identifier}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--identifier', required=True, help="Client identifier")
    args = parser.parse_args()

    identifier = args.identifier

    while True:
        # Simulate data collection
        data = {
            "identifier": identifier,
            "cpu_percent": 30,
            "memory_percent": 50,
            "swap_percent": 10,
            "cpu_total": 8,
            "memory_usage": 4096,
            "swap_usage": 512,
            "bytes_sent": 1024,
            "bytes_recv": 2048,
            "process_count": 100,
            "timestamp": int(time.time())
        }

        send_data(identifier, data)
        time.sleep(5)  # Send data every 5 seconds

if __name__ == "__main__":
    main()
