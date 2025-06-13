import psutil
import asyncio
import websockets

async def send_system_data(websocket):
    while True:
        cpu = psutil.cpu_percent(interval=1)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        processes = len(psutil.pids())

        data = {
            "cpu_total": cpu,
            "cpu_per_core": per_core,
            "memory_percent": memory.percent,
            "swap_percent": swap.percent,
            "disk_percent": disk.percent,
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "process_count": processes
        }

        print(data)
        await websocket.send(str(data))
        await asyncio.sleep(1)



async def main():
    async with websockets.serve(send_system_data, "localhost", 6789):
        print("WebSocket server running on ws://localhost:6789")
        await asyncio.Future()  # run forever

asyncio.run(main())