import psutil
import asyncio
import websockets
import argparse
import random
import platform
import json
import time

random_default_identifier = random.randint(100000000000, 999999999999)
parser = argparse.ArgumentParser(description="WebSocket client for system monitoring.")
parser.add_argument("--identifier", type=str, default=str(random_default_identifier), help="Unique identifier for the system.")
parser.add_argument("--server", type=str, default="ws://<YOUR_SERVER_IP>:6789", help="WebSocket server URI")
args = parser.parse_args()

async def send_system_data():
    while True:
        try:
            async with websockets.connect(args.server) as websocket:
                while True:
                    cpu = psutil.cpu_percent(interval=1)
                    per_core = psutil.cpu_percent(interval=None, percpu=True)
                    memory = psutil.virtual_memory()
                    swap = psutil.swap_memory()
                    disk = psutil.disk_usage('/')
                    net = psutil.net_io_counters()
                    processes = len(psutil.pids())

                    data = {
                        "identifier": args.identifier,
                        "timestamp": int(time.time()),
                        "cpu_total": cpu,
                        "cpu_per_core": per_core,
                        "memory_percent": memory.percent,
                        "swap_percent": swap.percent,
                        "disk_percent": disk.percent,
                        "bytes_sent": net.bytes_sent,
                        "bytes_recv": net.bytes_recv,
                        "process_count": processes,
                        "system": {
                            "platform": platform.system(),
                            "platform_version": platform.version(),
                            "boot_time": psutil.boot_time()
                        }
                    }

                    await websocket.send(json.dumps(data))
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Connection error: {e}, retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(send_system_data())
