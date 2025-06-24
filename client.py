import psutil
import asyncio
import websockets
import argparse
import random
import platform
import json
import time

random_default_identifier = random.randint(100000000000, 999999999999)

parser = argparse.ArgumentParser()
parser.add_argument("--identifier", type=str, default=str(random_default_identifier))
parser.add_argument("--server", type=str, default="ws://localhost:6789")
args = parser.parse_args()

# To track data sent and speed
last_bytes_sent = 0
last_time = time.time()

def get_system_data(identifier):
    try:
        swap_percent = psutil.swap_memory().percent
    except Exception as e:
        print(f"[Warning] Could not retrieve swap memory: {e}")
        swap_percent = None

    return {
        "type": "client",
        "identifier": identifier,
        "timestamp": int(time.time()),
        "cpu_total": psutil.cpu_percent(interval=None),
        "cpu_per_core": psutil.cpu_percent(interval=None, percpu=True),
        "memory_percent": psutil.virtual_memory().percent,
        "swap_percent": swap_percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "bytes_sent": psutil.net_io_counters().bytes_sent,
        "bytes_recv": psutil.net_io_counters().bytes_recv,
        "process_count": len(psutil.pids()),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "boot_time": psutil.boot_time()
        }
    }

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
                        break
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Connection error: {e}, retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
