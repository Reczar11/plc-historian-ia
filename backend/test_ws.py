import asyncio
import websockets


async def test():
    uri = 'ws://127.0.0.1:8000/ws/live?api_key=una-clave-secreta-de-desarrollo&tags=Temperature,Pressure&interval=1'
    async with websockets.connect(uri) as ws:
        for _ in range(3):
            message = await ws.recv()
            print(message)

asyncio.run(test())
