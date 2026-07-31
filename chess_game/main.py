import sys
import os
from utils import clear_screen
from ui import InteractiveGame, ClassicGame, SinglePlayerGame

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
    print('  ║     [4]  Single Player (vs Computer)              ║')
    print('  ║          Play offline against the built-in AI!    ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()

    while True:
        try:
            choice = input('  Enter mode (1, 2, 3, or 4): ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == '1':
            ClassicGame().run()
            break
        elif choice == '2':
            tc = _get_time_control()
            if tc is not None:
                InteractiveGame(time_limit=tc[0], increment=tc[1]).run()
            break
        elif choice == '3':
            _start_online()
            break
        elif choice == '4':
            _start_single_player()
            break
        else:
            print('  Please enter 1, 2, 3, or 4!')

    print()
    print('  Thanks for playing! Now go crush that teacher! ;)')
    print()


def _get_time_control():
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║           TIME CONTROL                            ║')
    print('  ╠═══════════════════════════════════════════════════╣')
    print('  ║                                                   ║')
    print('  ║   [1] No Timer (Unlimited)                        ║')
    print('  ║   [2] Bullet (1|1)  - 1 min + 1s                  ║')
    print('  ║   [3] Blitz  (3|3)  - 3 min + 3s                  ║')
    print('  ║   [4] Blitz  (5|5)  - 5 min + 5s                  ║')
    print('  ║   [5] Rapid  (10|10)- 10 min + 10s                ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()
    while True:
        try:
            choice = input('  Choose time control (1-5): ').strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice == '1': return None, 0
        if choice == '2': return 60, 1
        if choice == '3': return 180, 3
        if choice == '4': return 300, 5
        if choice == '5': return 600, 10
        print('  Please enter 1, 2, 3, 4, or 5!')


def _start_single_player():
    tc = _get_time_control()
    if tc is None: return
    time_limit, increment = tc
    
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║           SINGLE PLAYER (VS AI)                   ║')
    print('  ╠═══════════════════════════════════════════════════╣')
    print('  ║                                                   ║')
    print('  ║   Select AI Difficulty:                           ║')
    print('  ║     [1] Beginner (Depth 1)                        ║')
    print('  ║     [2] Intermediate (Depth 2)                    ║')
    print('  ║     [3] Advanced (Depth 3 - Slow)                 ║')
    print('  ║                                                   ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()
    while True:
        try:
            level = input('  Choose level (1, 2, or 3): ').strip()
        except (EOFError, KeyboardInterrupt):
            return
        if level in ('1', '2', '3'):
            break
        print('  Please enter 1, 2, or 3!')
        
    level = int(level)
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║   What color do you want to play as?              ║')
    print('  ║     [W] White                                     ║')
    print('  ║     [B] Black                                     ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()
    while True:
        try:
            color_choice = input('  Choose color (W/B): ').strip().upper()
        except (EOFError, KeyboardInterrupt):
            return
        if color_choice in ('W', 'B'):
            break
        print('  Please enter W or B!')
    
    player_color = 'white' if color_choice == 'W' else 'black'
    print(f"  Starting game... You are {player_color.upper()} against Level {level} AI.")
    SinglePlayerGame(player_color=player_color, level=level, time_limit=time_limit, increment=increment).run()


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
    from ui import OnlineGame
    from network import NetworkClient
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

    tc = _get_time_control()
    if tc is None: return
    time_limit, increment = tc

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

        print("\n  ⚠️ NOTE: Please ensure both players selected the same time control!")
        time.sleep(1)
        OnlineGame(client, room_code, my_color='white', time_limit=time_limit, increment=increment).run()

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
        print("  ⚠️ NOTE: Please ensure both players selected the same time control!")
        time.sleep(2)
        OnlineGame(client, code, my_color, time_limit=time_limit, increment=increment).run()
    else:
        print("  Invalid choice.")
        client.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
