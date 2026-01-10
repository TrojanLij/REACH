import asyncio
import websockets

async def hello():
    # The 'async with' statement ensures the connection is closed properly
    uri = "wss://localhost:8443" # Replace with your WebSocket server URI (ws:// for standard, wss:// for secure)
    try:
        async with websockets.connect(uri) as websocket:
            # Send a message
            message_to_send = "Hello, World!"
            await websocket.send(message_to_send)
            print(f"Sent: {message_to_send}")

            # Receive a message
            received_message = await websocket.recv()
            print(f"Received: {received_message}")
    except ConnectionRefusedError:
        print(f"Connection failed. Make sure a server is running at {uri}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Run the asyncio event loop
    asyncio.run(hello())
