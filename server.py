import psutil
import asyncio
import websockets
import json
import redis
import time
import os

r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)

clients = set()
data_queue = asyncio.Queue()

last_bytes_received = 0
last_time_received = time.time()

imperative_start_time = 0

current_process = psutil.Process(os.getpid())

async def get_program_usage(script_name="server.py"):
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
            # Check if the process is the one we're looking for
            if 'python' in proc.info['name'] and any(script_name in cmd for cmd in proc.info['cmdline']):
                program_usage['cpu_percent'] += proc.cpu_percent(interval=1.0)
                program_usage['memory_usage'] += proc.memory_info().rss  # Using 'rss' for resident set size
                # Do not access 'swap' directly for individual processes
                # swap memory is system-wide and should not be accessed like this
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Convert bytes to MB (if needed)
    program_usage['memory_usage'] /= 1024 ** 2  # In MB
    program_usage['swap_usage'] = psutil.swap_memory().used / (1024 ** 2)  # Total used swap in MB

    return program_usage


async def get_server_metrics():
    total_memory = psutil.virtual_memory().total
    swap_memory = psutil.swap_memory()

    program_usage = await get_program_usage("server.py")

    return {
        "cpu_percent": program_usage['cpu_percent'],
        "cpu_total": psutil.cpu_count(logical=False),
        "memory_usage": program_usage['memory_usage'],
        "memory_total": total_memory / (1024 ** 2),
        "swap_usage": program_usage['swap_usage'],
        "swap_total": swap_memory.total / (1024 ** 2),
        "imperative_time": imperative_start_time  # Add the imperative time here
    }

async def connection_handler(websocket):
    global imperative_start_time
    try:
        message = await websocket.recv()
        data = json.loads(message)
        conn_type = data.get("type")

        start_time = time.time()  # Start the time when the request comes in
        if conn_type == "client":
            identifier = data.get("identifier", "unknown")
            print(f"[Client connected] {identifier}")
            r.set(f"client:{identifier}", json.dumps(data))
            await data_queue.put(data)

            try:
                # Handle incoming messages from the client
                async for msg in websocket:
                    data = json.loads(msg)
                    r.set(f"client:{identifier}", json.dumps(data))
                    await data_queue.put(data)

                    end_time = time.time()  # End time when the request is processed
                    imperative_start_time = end_time - start_time  # Calculate the imperative time

                    # Network usage stats
                    current_bytes_received = psutil.net_io_counters().bytes_recv
                    current_time = time.time()

                    bytes_received = current_bytes_received - last_bytes_received
                    time_elapsed = current_time - last_time_received

                    if time_elapsed > 0:
                        speed_kb_per_sec = bytes_received / time_elapsed / 1024
                        print(f"Data Received: {bytes_received / 1024:.2f} KB in {time_elapsed:.2f} seconds -> Speed: {speed_kb_per_sec:.2f} KB/s")

                    last_bytes_received = current_bytes_received
                    last_time_received = current_time

            finally:
                # Cleanup after client disconnects
                r.delete(f"client:{identifier}")
                print(f"[Client disconnected] {identifier}")

        elif conn_type == "dashboard":
            clients.add(websocket)
            print("[Dashboard connected]")
            try:
                await websocket.wait_closed()
            finally:
                clients.remove(websocket)
                print("[Dashboard disconnected]")

        else:
            print(f"Unknown connection type: {conn_type}, closing connection")
            await websocket.close()

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    except Exception as e:
        print(f"Error in connection_handler: {e}")

async def data_dispatcher():
    while True:
        data = await data_queue.get()
        message = json.dumps(data)
        disconnected = set()

        for client in clients:
            try:
                await client.send(message)
            except:
                disconnected.add(client)

        for dc in disconnected:
            clients.discard(dc)

async def send_server_metrics():
    while True:
        # Get the server metrics, including imperative time
        server_metrics = await get_server_metrics()
        server_metrics["imperative_time"] = imperative_start_time  # Add imperative processing time
        
        message = json.dumps({
            "type": "server",
            "metrics": server_metrics
        })

        # Send metrics to all connected dashboards
        for client in clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosedError:
                print("Dashboard disconnected unexpectedly.")
                clients.discard(client)

        await asyncio.sleep(1)  # Send updates every second



async def main():
    print("Server listening on ws://0.0.0.0:6789")
    asyncio.create_task(data_dispatcher())
    asyncio.create_task(send_server_metrics())
    async with websockets.serve(connection_handler, "0.0.0.0", 6789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
