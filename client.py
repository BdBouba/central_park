import psutil
import asyncio
import websockets
import argparse
import random
import platform
import json
import time
import rx
from rx import operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler

random_default_identifier = random.randint(100000000000, 999999999999)

parser = argparse.ArgumentParser()
parser.add_argument("--identifier", type=str, default=str(random_default_identifier))
parser.add_argument("--server", type=str, default="ws://localhost:6789")
args = parser.parse_args()

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

async def main():
    scheduler = AsyncIOScheduler(asyncio.get_event_loop())

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

                # Then start sending periodic system data every 1 second
                rx.interval(1.0).pipe(
                    ops.map(lambda _: get_system_data(args.identifier))
                ).subscribe(
                    lambda data: asyncio.create_task(send_data(websocket, data)),
                    scheduler=scheduler
                )

                await asyncio.Future()  # Keep running until disconnected

        except Exception as e:
            print(f"Connection error: {e}, retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
