import asyncio
import websockets

async def start_and_listen():
    uri = "ws://localhost:8765"  # Change to your server's IP if needed
    async with websockets.connect(uri) as websocket:
        # Send START command
        await websocket.send("START")
        print("✅ Sent START command to server.")

        # Listen for messages from the server
        try:
            while True:
                message = await websocket.recv()
                print(f"📩 Received message from server: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server.")

# Run the client
if __name__ == "__main__":
    asyncio.run(start_and_listen())
