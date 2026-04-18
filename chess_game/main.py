import sys
from .utils import clear_screen
from .ui import InteractiveGame, ClassicGame

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
            from .ui import OnlineGame
            from .network import NetworkClient
            import time
            
            print("\n  [1] Create Room")
            print("  [2] Join Room")
            net_choice = input("  Choice: ").strip()
            
            client = NetworkClient(uri="ws://localhost:8765")
            print("\n  Connecting to relay server...")
            client.start()
            
            # Wait for connection
            timeout = 3.0
            start = time.time()
            while not client.connected and time.time() - start < timeout:
                time.sleep(0.1)
                
            if not client.connected:
                print("  Failed to connect to server. Ensure server is running.")
                client.stop()
                return

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
                
                print(f"\n  Room created! Code: {room_code}")
                print("  Waiting for opponent to join...")
                
                while True:
                    msg = client.receive()
                    if msg and msg.get('type') == 'opponent_joined':
                        print("  Opponent joined! You play as WHITE.")
                        time.sleep(1)
                        break
                    time.sleep(0.1)
                
                OnlineGame(client, room_code, my_color='white').run()
                break

            elif net_choice == '2':
                code = input("\n  Enter Room Code: ").strip().upper()
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
                            print(f"  Error: {msg.get('message')}")
                            client.stop()
                            return
                    time.sleep(0.1)
                
                print(f"  Joined successfully! You play as {my_color.upper()}.")
                time.sleep(1)
                OnlineGame(client, code, my_color).run()
                break
            else:
                print("  Invalid choice.")
                client.stop()
                return
        else:
            print('  Please enter 1, 2, or 3!')

    print()
    print('  Thanks for playing! Now go crush that teacher! ;)')
    print()

