import asyncio
import websockets
import json
import redis
import rx
from rx.subject import Subject
from rx.scheduler.eventloop import AsyncIOScheduler

r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
data_subject = Subject()
clients = set()

async def connection_handler(websocket):
    """
    Handles all connections.
    Expects clients to send a JSON message with a 'type' key on connection to identify themselves.
    """
    try:
        # Wait for the first message to identify connection type
        message = await websocket.recv()
        data = json.loads(message)
        conn_type = data.get("type")

        if conn_type == "client":
            identifier = data.get("identifier", "unknown")
            print(f"[Client connected] {identifier}")
            r.set(f"client:{identifier}", json.dumps(data))
            data_subject.on_next(data)

            # Listen for further messages from this client
            async for msg in websocket:
                data = json.loads(msg)
                r.set(f"client:{identifier}", json.dumps(data))
                data_subject.on_next(data)

            # On disconnect
            r.delete(f"client:{identifier}")
            print(f"[Client disconnected] {identifier}")

        elif conn_type == "dashboard":
            clients.add(websocket)
            print("[Dashboard connected]")
            await websocket.wait_closed()
            clients.remove(websocket)
            print("[Dashboard disconnected]")

        else:
            print(f"Unknown connection type: {conn_type}, closing connection")
            await websocket.close()

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    except Exception as e:
        print(f"Error in connection_handler: {e}")

async def safe_send(client, message):
    try:
        await client.send(message)
    except:
        clients.discard(client)

def push_to_clients(data):
    message = json.dumps(data)
    for client in list(clients):
        asyncio.create_task(safe_send(client, message))

async def main():
    print("Server listening on ws://0.0.0.0:6789")

    data_subject.subscribe(
        on_next=push_to_clients,
        scheduler=AsyncIOScheduler(asyncio.get_event_loop())
    )

    async with websockets.serve(connection_handler, "0.0.0.0", 6789):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
