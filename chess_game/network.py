import asyncio
import websockets
import json
import threading
import queue

class NetworkClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()
        self.loop = None
        self.ws = None
        self.thread = None
        self.connected = False

    def start(self):
        """Starts the network event loop in a background thread."""
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_run())

    async def _connect_and_run(self):
        try:
            async with websockets.connect(self.uri) as ws:
                self.ws = ws
                self.connected = True
                
                # Create tasks for reading and writing
                consumer_task = asyncio.create_task(self._consumer_handler(ws))
                producer_task = asyncio.create_task(self._producer_handler(ws))
                
                done, pending = await asyncio.wait(
                    [consumer_task, producer_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                for task in pending:
                    task.cancel()
        except Exception as e:
            self.recv_queue.put({'type': 'error', 'message': f'Connection failed: {e}'})
        finally:
            self.connected = False

    async def _consumer_handler(self, ws):
        """Receives messages from the WebSocket and puts them in recv_queue."""
        try:
            async for message in ws:
                data = json.loads(message)
                self.recv_queue.put(data)
        except websockets.exceptions.ConnectionClosed:
            self.recv_queue.put({'type': 'error', 'message': 'Disconnected from server.'})

    async def _producer_handler(self, ws):
        """Gets messages from send_queue and sends them over WebSocket."""
        while True:
            try:
                # We use a non-blocking get inside async sleep loop
                # to avoid blocking the asyncio event loop.
                try:
                    msg = self.send_queue.get_nowait()
                    await ws.send(json.dumps(msg))
                    self.send_queue.task_done()
                except queue.Empty:
                    await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Send error: {e}")
                break

    def send(self, data):
        """Called by UI thread to place a message in the send queue."""
        self.send_queue.put(data)

    def receive(self):
        """Called by UI thread to grab next message, returns None if empty."""
        try:
            return self.recv_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        self.connected = False
        if self.loop is not None:
             self.loop.call_soon_threadsafe(self.loop.stop)
