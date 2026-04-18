import subprocess
import time
import re
import sys
import os

print("="*60)
print("  ASCIII CHESS — AUTO ONLINE HOST")
print("  Starting local server & generating public URL...")
print("="*60)

# 1. Start the local server in the background
server_process = subprocess.Popen([sys.executable, "server.py"])
time.sleep(2)  # Give the server a moment to start

print("\n[1] Server started locally.")

# 2. Start the Pinggy SSH tunnel to expose the server to the internet
# We run Pinggy over port 443 with SNI multiplexing. No accounts required.
print("[2] Opening internet tunnel... (this may take a moment)")
tunnel_process = subprocess.Popen(
    ["ssh", "-p", "443", "-o", "StrictHostKeyChecking=no", "-R0:localhost:8765", "a.pinggy.io"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

public_url = None

# Read the output from the SSH tunnel until we find the https URL
for line in tunnel_process.stdout:
    line = line.strip()
    if line.startswith("https://"):
        public_url = line
        break

if public_url:
    # Convert https://... to wss://...
    wss_url = public_url.replace("https://", "wss://")
    print("\n" + "="*60)
    print("  SUCCESS! YOUR SERVERS ARE LIVE!")
    print("="*60)
    print(f"\n  Your friend can now join from anywhere in the world.")
    print(f"  Tell them to select 'Online Server' and give them this exact URL:")
    print(f"\n      {wss_url}\n")
    print("="*60)
    print("\nNOTE: This is a free temporary tunnel. It will expire in 60 minutes.")
    print("      To play longer, just run this script again later.")
    
    # 3. Automatically launch the game for the host
    print("\nLaunching your game now! Please wait...")
    time.sleep(3)
    try:
        subprocess.run([sys.executable, "chess.py"])
    except KeyboardInterrupt:
        pass
else:
    print("\n[!] Failed to get a public URL. Ensure you have internet access.")

# 4. Clean up after the game is closed
print("\nShutting down servers...")
server_process.terminate()
tunnel_process.terminate()
print("Done!")
