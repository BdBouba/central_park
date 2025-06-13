import asyncio
import websockets

async def test():
    uri = "ws://localhost:6789"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"Received: {data}")

asyncio.run(test())
