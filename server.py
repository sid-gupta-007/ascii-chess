import asyncio
import websockets
import json
import random
import string

# Active rooms: room_code -> [host_ws, guest_ws]
rooms = {}

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

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

    except websockets.exceptions.ConnectionClosed:
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
    print("Listing for WebSockets on ws://0.0.0.0:8765...")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
