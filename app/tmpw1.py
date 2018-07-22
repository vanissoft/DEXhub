import asyncio
import websockets
import time

async def hello(uri):
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello world!")

asyncio.get_event_loop().run_until_complete(
    hello('ws://127.0.0.1:8808/feed'))
