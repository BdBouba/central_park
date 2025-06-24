import psutil
import asyncio
import websockets
import argparse
import random
import platform
import json
import time
import os

random_default_identifier = random.randint(100000000000, 999999999999)

parser = argparse.ArgumentParser()
parser.add_argument("--identifier", type=str, default=str(random_default_identifier))
parser.add_argument("--server", type=str, default="ws://localhost:6789")
args = parser.parse_args()

# To track data sent and speed
last_bytes_sent = 0
last_time = time.time()

# Get the current Python process using psutil
current_process = psutil.Process(os.getpid())  # Current Python process

def get_system_data(identifier):
    try:
        # Get Swap memory usage percentage
        swap = psutil.swap_memory()
        swap_percent = swap.percent
        swap_used = swap.used / (1024 * 1024)  # Convert bytes to MB
    except Exception as e:
        print(f"[Warning] Could not retrieve swap memory: {e}")
        swap_percent = "N/A"
        swap_used = "N/A"

    try:
        cpu_count = psutil.cpu_count()  # Physical cores
        cpu_percent = psutil.cpu_percent()
    except Exception as e:
        print(f"[Warning] Could not retrieve CPU stats: {e}")
        cpu_count = "N/A"
        cpu_percent = "N/A"

    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024 * 1024)  # Convert bytes to MB
    except Exception as e:
        print(f"[Warning] Could not retrieve memory stats: {e}")
        memory_percent = "N/A"
        memory_used = "N/A"

    try:
        disk_percent = psutil.disk_usage('/').percent
        disk_used = psutil.disk_usage('/').used / (1024 * 1024 * 1024)  # in GB
    except Exception as e:
        print(f"[Warning] Could not retrieve disk stats: {e}")
        disk_percent = "N/A"
        disk_used = "N/A"

    # Build the system data dictionary
    data = {
        "type": "client",
        "identifier": identifier,
        "timestamp": int(time.time()),
        "cpu_total": cpu_percent if cpu_percent is not None else "N/A",
        "cpu_cores": cpu_count if cpu_count is not None else "N/A",
        "memory_percent": memory_percent if memory_percent is not None else "N/A",
        "memory_used": memory_used if memory_used is not None else "N/A",
        "swap_percent": swap_percent if swap_percent is not None else "N/A",
        "swap_used": swap_used if swap_used is not None else "N/A",
        "disk_percent": disk_percent if disk_percent is not None else "N/A",
        "disk_used": disk_used if disk_used is not None else "N/A",
        "bytes_sent": psutil.net_io_counters().bytes_sent,
        "bytes_recv": psutil.net_io_counters().bytes_recv,
        "process_count": len(psutil.pids()),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "boot_time": psutil.boot_time()
        }
    }

    return data


async def send_data(websocket, data):
    try:
        await websocket.send(json.dumps(data))
    except websockets.ConnectionClosedError as e:
        print(f"WebSocket connection closed unexpectedly: {e}")
    except Exception as e:
        print(f"Error sending data: {e}")


async def calculate_transmission_speed():
    global last_bytes_sent, last_time
    while True:
        current_bytes_sent = psutil.net_io_counters().bytes_sent
        current_time = time.time()

        # Calculate bytes sent and transmission speed in KB/s
        bytes_sent = current_bytes_sent - last_bytes_sent
        time_elapsed = current_time - last_time

        if time_elapsed > 0:
            speed_kb_per_sec = bytes_sent / time_elapsed / 1024  # KB/s
            print(f"Data Sent: {bytes_sent / 1024:.2f} KB in {time_elapsed:.2f} seconds -> Speed: {speed_kb_per_sec:.2f} KB/s")

        last_bytes_sent = current_bytes_sent
        last_time = current_time

        await asyncio.sleep(1)


async def main():
    # Start transmission speed calculation
    asyncio.create_task(calculate_transmission_speed())

    while True:
        try:
            async with websockets.connect(args.server) as websocket:
                print(f"[{args.identifier}] Connected to {args.server}")

                # Send initial message to identify as client immediately
                init_data = {
                    "type": "client",
                    "identifier": args.identifier
                }
                await websocket.send(json.dumps(init_data))

                while True:
                    data = get_system_data(args.identifier)
                    try:
                        await websocket.send(json.dumps(data))
                    except websockets.ConnectionClosedError as e:
                        print(f"WebSocket connection closed unexpectedly: {e}")
                        break
                    except Exception as e:
                        print(f"Error sending data: {e}")

                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
