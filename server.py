import psutil
import json
import redis
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)

last_bytes_received = 0
last_time_received = time.time()

imperative_start_time = 0

current_process = psutil.Process(os.getpid())

def get_program_usage(script_name="server.py"):
    program_usage = {
        'cpu_percent': 0,
        'memory_usage': 0.0,
        'swap_usage': 0.0,
        'cpu_total': psutil.cpu_count(logical=False),
        'memory_total': psutil.virtual_memory().total,
        'swap_total': psutil.swap_memory().total
    }

    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'] and any(script_name in cmd for cmd in proc.info['cmdline']):
                program_usage['cpu_percent'] += proc.cpu_percent(interval=1.0)
                program_usage['memory_usage'] += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    program_usage['memory_usage'] /= 1024 ** 2  # Convert to MB
    program_usage['swap_usage'] = psutil.swap_memory().used / (1024 ** 2)  # MB

    return program_usage


def get_server_metrics():
    total_memory = psutil.virtual_memory().total
    swap_memory = psutil.swap_memory()

    program_usage = get_program_usage("server.py")

    return {
        "cpu_percent": program_usage['cpu_percent'],
        "cpu_total": psutil.cpu_count(logical=False),
        "memory_usage": program_usage['memory_usage'],
        "memory_total": total_memory / (1024 ** 2),  # MB
        "swap_usage": program_usage['swap_usage'],
        "swap_total": swap_memory.total / (1024 ** 2),  # MB
        "imperative_time": imperative_start_time  # Add imperative time here
    }

@app.route('/data', methods=['POST'])
def handle_client_data():
    try:
        data = request.json
        print(f"Received data: {data}")

        # Ensure the data contains an identifier
        identifier = data.get("identifier")
        if not identifier:
            raise ValueError("Missing identifier in the request.")
        
        print(f"[Client connected] {identifier}")
        r.set(f"client:{identifier}", json.dumps(data))

        # Process data and calculate imperative time
        start_time = time.time()
        # Simulate processing
        time.sleep(0.1)  # Simulating some processing time
        end_time = time.time()
        
        global imperative_start_time
        imperative_start_time = end_time - start_time

        # Simulate network stats (for example)
        current_bytes_received = psutil.net_io_counters().bytes_recv
        current_time = time.time()

        bytes_received = current_bytes_received - last_bytes_received
        time_elapsed = current_time - last_time_received

        if time_elapsed > 0:
            speed_kb_per_sec = bytes_received / time_elapsed / 1024
            print(f"Data Received: {bytes_received / 1024:.2f} KB in {time_elapsed:.2f} seconds -> Speed: {speed_kb_per_sec:.2f} KB/s")

        last_bytes_received = current_bytes_received
        last_time_received = current_time

        return jsonify({'status': 'success'})

    except ValueError as ve:
        print(f"ValueError: {str(ve)}")  # Log the specific error for missing identifier
        return jsonify({'error': str(ve)}), 400  # Return a 400 Bad Request

    except Exception as e:
        print(f"Error processing data: {str(e)}")  # Log any other exception
        return jsonify({'error': str(e)}), 500  # Return a 500 Internal Server Error

@app.route('/metrics', methods=['GET'])
def get_metrics():
    server_metrics = get_server_metrics()
    return jsonify({
        "type": "server",
        "metrics": server_metrics
    })

@app.route('/clients', methods=['GET'])
def get_all_clients():
    keys = r.keys("client:*")
    clients = []
    for key in keys:
        value = r.get(key)
        try:
            clients.append(json.loads(value))
        except (json.JSONDecodeError, TypeError):
            print(f"Invalid JSON in key: {key} -> {value}")
            continue
    return jsonify({"type": "clients", "data": clients})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
