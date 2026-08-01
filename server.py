import asyncio
from websockets.asyncio.server import serve
import json
import random
import string
import os
from http import HTTPStatus

# Active rooms: room_code -> [host_ws, guest_ws]
rooms = {}

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ── HTTP Health Check (for Render / cloud platforms) ──────────
def health_check(connection, request):
    """Respond to HTTP health checks so Render knows the server is alive."""
    if request.path in ("/health", "/healthz"):
        return connection.respond(HTTPStatus.OK, "OK\n")


async def handle_client(websocket):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except Exception:
                continue

            msg_type = data.get('type')

            if msg_type == 'create':
                room_code = generate_code()
                while room_code in rooms:
                    room_code = generate_code()
                
                rooms[room_code] = [websocket]
                await websocket.send(json.dumps({'type': 'created', 'room': room_code}))
                print(f"Room Created: {room_code}")

            elif msg_type == 'join':
                room_code = data.get('room')
                if room_code in rooms and len(rooms[room_code]) == 1:
                    rooms[room_code].append(websocket)
                    host_ws = rooms[room_code][0]
                    # Tell guest they joined as Black
                    await websocket.send(json.dumps({'type': 'joined', 'color': 'black'}))
                    # Tell host an opponent joined
                    await host_ws.send(json.dumps({'type': 'opponent_joined'}))
                    print(f"Room Joined: {room_code}")
                else:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Room not found or full.'}))

            elif msg_type == 'move':
                room_code = data.get('room')
                move_data = data.get('move')
                if room_code in rooms:
                    for ws in rooms[room_code]:
                        if ws != websocket: # Send to the other person
                            try:
                                await ws.send(json.dumps({'type': 'move', 'move': move_data}))
                            except:
                                pass

    except Exception:
        pass
    finally:
        # Cleanup disconnected clients
        for code, clients in list(rooms.items()):
            if websocket in clients:
                clients.remove(websocket)
                for other_ws in clients:
                    try:
                        await other_ws.send(json.dumps({'type': 'opponent_disconnected'}))
                    except:
                        pass
                if not clients and code in rooms:
                    del rooms[code]

async def main():
    # Use PORT env var (set by Render/Railway/etc.) or default to 8765 for local dev
    port = int(os.environ.get("PORT", 8765))
    
    print(f"Listening for WebSockets on ws://0.0.0.0:{port}...")
    async with serve(
        handle_client,
        "0.0.0.0",
        port,
        process_request=health_check,
    ) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
