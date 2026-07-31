import sys
import os
from utils import clear_screen
from ui import InteractiveGame, ClassicGame

# ═══════════════════════════════════════════════
#  Server Configuration
# ═══════════════════════════════════════════════
# Set this to your deployed Render URL after deployment.
# Example: "wss://ascii-chess-relay.onrender.com"
# Leave as None to be prompted every time.
CLOUD_SERVER_URL = None


def main():
    clear_screen()
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║                                                   ║')
    print('  ║             ░█▀▀░█░█░█▀▀░█▀▀░█▀▀                  ║')
    print('  ║             ░█░░░█▀█░█▀▀░▀▀█░▀▀█                  ║')
    print('  ║             ░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀                  ║')
    print('  ║                                                   ║')
    print('  ║          A S C I I   C H E S S                    ║')
    print('  ║            Terminal Edition v2.0                  ║')
    print('  ║              Two-Player Game                      ║')
    print('  ║                                                   ║')
    print('  ╠═══════════════════════════════════════════════════╣')
    print('  ║                                                   ║')
    print('  ║   SELECT YOUR MODE:                               ║')
    print('  ║                                                   ║')
    print('  ║     [1]  Classic Mode                             ║')
    print('  ║          Type moves like "e2 e4"                  ║')
    print('  ║          Simple and straightforward               ║')
    print('  ║                                                   ║')
    print('  ║     [2]  Interactive Mode  ★ RECOMMENDED          ║')
    print('  ║          Use arrow keys + Enter to play           ║')
    print('  ║          Legal moves glow on the board!           ║')
    print('  ║          Just navigate, select, and move!         ║')
    print('  ║     [3]  Online Multiplayer                       ║')
    print('  ║          Play with a friend over the internet!    ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()

    while True:
        try:
            choice = input('  Enter mode (1, 2, or 3): ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == '1':
            ClassicGame().run()
            break
        elif choice == '2':
            InteractiveGame().run()
            break
        elif choice == '3':
            _start_online()
            break
        else:
            print('  Please enter 1, 2, or 3!')

    print()
    print('  Thanks for playing! Now go crush that teacher! ;)')
    print()


def _get_server_uri():
    """Prompt user to choose between cloud server and local server."""
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║           SERVER CONNECTION                       ║')
    print('  ╠═══════════════════════════════════════════════════╣')
    print('  ║                                                   ║')
    print('  ║   [1]  Online Server (play over the internet)    ║')
    print('  ║        Connect to the cloud relay server          ║')
    print('  ║                                                   ║')
    print('  ║   [2]  Local Server (same network / testing)     ║')
    print('  ║        Connect to localhost:8765                  ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()

    while True:
        try:
            server_choice = input('  Choose server (1 or 2): ').strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if server_choice == '1':
            if CLOUD_SERVER_URL:
                return CLOUD_SERVER_URL
            else:
                print()
                print('  ⚠  No cloud server configured!')
                print('  Enter your deployed server URL')
                print('  (e.g. wss://ascii-chess-relay.onrender.com)')
                print()
                try:
                    url = input('  Server URL: ').strip()
                except (EOFError, KeyboardInterrupt):
                    return None
                if not url:
                    print('  No URL entered.')
                    return None
                
                # Normalize: convert http/https to ws/wss, or prepend wss:// if missing
                url = url.strip()
                if url.startswith('http://'):
                    url = url.replace('http://', 'ws://', 1)
                elif url.startswith('https://'):
                    url = url.replace('https://', 'wss://', 1)
                elif not url.startswith('ws://') and not url.startswith('wss://'):
                    url = 'wss://' + url
                    
                return url
        elif server_choice == '2':
            return 'ws://localhost:8765'
        else:
            print('  Please enter 1 or 2!')


def _start_online():
    """Handle the online multiplayer flow."""
    from .ui import OnlineGame
    from .network import NetworkClient
    import time

    # ── Choose server ──
    server_uri = _get_server_uri()
    if server_uri is None:
        return

    print("\n  [1] Create Room")
    print("  [2] Join Room")
    try:
        net_choice = input("  Choice: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    print(f"\n  Connecting to {server_uri}...")
    client = NetworkClient(uri=server_uri)
    client.start()

    # Wait for connection
    timeout = 10.0  # Longer timeout for cloud server cold starts
    start = time.time()
    while not client.connected and time.time() - start < timeout:
        time.sleep(0.1)

    if not client.connected:
        print("  ✗ Failed to connect to server.")
        if 'localhost' in server_uri:
            print("    Make sure you ran: python server.py")
        else:
            print("    The cloud server may be starting up. Try again in 30s.")
        client.stop()
        input("\n  Press Enter to continue...")
        return

    print("  ✓ Connected!")

    if net_choice == '1':
        client.send({'type': 'create'})
        print("  Requesting room code...")

        room_code = None
        while True:
            msg = client.receive()
            if msg:
                if msg.get('type') == 'created':
                    room_code = msg.get('room')
                    break
            time.sleep(0.1)

        print(f"\n  ╔══════════════════════════════════════╗")
        print(f"  ║  Room Code:  {room_code}                    ║")
        print(f"  ╠══════════════════════════════════════╣")
        print(f"  ║  Share this code with your friend!   ║")
        print(f"  ║  They select Online → Join Room      ║")
        print(f"  ║  and enter this code.                ║")
        print(f"  ╚══════════════════════════════════════╝")
        print("\n  Waiting for opponent to join...")

        while True:
            msg = client.receive()
            if msg and msg.get('type') == 'opponent_joined':
                print("  ✓ Opponent joined! You play as WHITE.")
                time.sleep(1)
                break
            time.sleep(0.1)

        OnlineGame(client, room_code, my_color='white').run()

    elif net_choice == '2':
        try:
            code = input("\n  Enter Room Code: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            client.stop()
            return
        client.send({'type': 'join', 'room': code})
        print("  Joining...")

        my_color = None
        while True:
            msg = client.receive()
            if msg:
                t = msg.get('type')
                if t == 'joined':
                    my_color = msg.get('color')
                    break
                elif t == 'error':
                    print(f"  ✗ Error: {msg.get('message')}")
                    client.stop()
                    input("\n  Press Enter to continue...")
                    return
            time.sleep(0.1)

        print(f"  ✓ Joined! You play as {my_color.upper()}.")
        time.sleep(1)
        OnlineGame(client, code, my_color).run()
    else:
        print("  Invalid choice.")
        client.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
