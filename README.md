# ASCII Chess - Terminal Edition

A fully-featured, two-player chess game played entirely in the terminal with beautifully crafted ASCII art and intuitive controls.

## Features
- **Classic Mode**: Enter your moves the old-fashioned way using coordinate notation (e.g., `e2 e4`).
- **Interactive Mode**: Use your arrow keys to navigate the board, with glowing legal move indicators and a seamless selection process!
- **Online Multiplayer**: Play with friends seamlessly over the internet! 
  - Use the `host_online.py` auto-tunnel script to play over a temporary internet link without any configuration.
  - OR deploy a free cloud relay server (using Render and the included `render.yaml`).
- **Cross-Platform**: Force-enables UTF-8 encoding and VT100 escapes so the chess pieces render beautifully on Windows, Mac, and Linux terminals.

## Installation

1. **Clone the repository:**
   - currently only the offline pass n play mode available {online mode is in the development}
   ```bash
   git clone https://github.com/sid-gupta-007/ascii-chess.git
   cd ascii-chess
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: The only dependency is `websockets`, required for online multiplayer).*

## How to Play

### Single-player / Local Two-player
Launch the game directly:
```bash
python chess.py
```
You will be prompted to choose between Classic Mode, Interactive Mode, or Online Multiplayer.

### Online Multiplayer Workflows
There are 2 ways to play online with a friend over the internet:

**Option A: Auto-Host (Easiest)**
1. The host simply runs the hosting script:
   ```bash
   python host_online.py
   ```
2. The script will automatically spin up a local server, open an internet tunnel (using Pinggy), and copy a public `wss://...` URL to your clipboard. It will then automatically launch the game for you.
3. Once in the game, choose "Create Room" and share the URL and the Room Code with your friend.
4. Your friend simply runs `python chess.py`, selects "Online Multiplayer", pastes your server URL, and joins your room.

**Option B: Cloud Deployment (Persistent Server)**
1. Simply connect this repository to Render using the provided `render.yaml`.
2. Grab your deployed secure WebSocket URL (e.g., `wss://your-app.onrender.com`).
3. Both players run `python chess.py`, choose "Online Multiplayer", and connect to the shared URL!

## File Structure

- `chess.py`: The main entry point to play the game.
- `host_online.py`: Automates firing up a local server and a Pinggy SSH tunnel for seamless peer-to-peer play.
- `server.py`: The lightweight Python WebSocket game server.
- `chess_game/`: Contains the modular game package (UI, chess logic, and network components).
- `render.yaml`: Configuration for deploying the server application to Render.
