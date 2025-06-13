import asyncio
import websockets
import json

clients = {}

async def handler(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            identifier = data.get("identifier", "unknown")
            clients[identifier] = data  # Stocke les dernières données reçues
            print(f"[{identifier}] CPU: {data['cpu_total']}% | RAM: {data['memory_percent']}%")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        if identifier in clients:
            del clients[identifier]

async def main():
    print("Server listening on ws://0.0.0.0:6789")
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()  # run forever

asyncio.run(main())
