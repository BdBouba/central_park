import psutil
import asyncio
import websockets
import json
import redis
import time

r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)

clients = set()
data_queue = asyncio.Queue()

last_bytes_received = 0
last_time_received = time.time()

imperative_start_time = 0
imperative_end_time = 0
reactive_start_time = 0
reactive_end_time = 0

async def get_server_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "bytes_sent": psutil.net_io_counters().bytes_sent,
        "bytes_recv": psutil.net_io_counters().bytes_recv,
    }

async def connection_handler(websocket):
    global last_bytes_received, last_time_received, imperative_start_time, imperative_end_time, reactive_start_time, reactive_end_time
    
    try:
        message = await websocket.recv()
        data = json.loads(message)
        conn_type = data.get("type")

        start_time = time.time()

        if conn_type == "client":
            identifier = data.get("identifier", "unknown")
            print(f"[Client connected] {identifier}")
            r.set(f"client:{identifier}", json.dumps(data))
            await data_queue.put(data)

            try:
                async for msg in websocket:
                    data = json.loads(msg)
                    r.set(f"client:{identifier}", json.dumps(data))
                    await data_queue.put(data)

                    end_time = time.time()

                    if "imperative" in data:
                        imperative_start_time = start_time
                        imperative_end_time = end_time
                    elif "reactive" in data:
                        reactive_start_time = start_time
                        reactive_end_time = end_time

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
        server_metrics = await get_server_metrics()
        server_metrics["imperative_time"] = imperative_end_time - imperative_start_time
        server_metrics["reactive_time"] = reactive_end_time - reactive_start_time
        
        message = json.dumps({
            "type": "server",
            "metrics": server_metrics
        })

        for client in clients:
            try:
                await client.send(message)
            except:
                pass

        await asyncio.sleep(1)

async def main():
    print("Server listening on ws://0.0.0.0:6789")
    asyncio.create_task(data_dispatcher())
    asyncio.create_task(send_server_metrics())
    async with websockets.serve(connection_handler, "0.0.0.0", 6789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
