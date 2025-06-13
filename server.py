import asyncio
import websockets
import json
import redis

# Connexion à Redis (localhost par défaut)
r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)

async def handler(websocket):
    identifier = None
    try:
        async for message in websocket:
            data = json.loads(message)
            identifier = data.get("identifier", "unknown")
            # Stockage dans Redis sous la clé "client:<identifier>"
            r.set(f"client:{identifier}", json.dumps(data))
            print(f"[{identifier}] Received data and stored in Redis.")
    except websockets.exceptions.ConnectionClosed:
        print(f"[{identifier}] Disconnected")
    finally:
        if identifier:
            r.delete(f"client:{identifier}")
            print(f"[{identifier}] Data removed from Redis.")

async def main():
    print("Server listening on ws://0.0.0.0:6789")
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()  # Keep server running forever

if __name__ == "__main__":
    asyncio.run(main())
