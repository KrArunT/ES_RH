import asyncio
import pika
import threading
import websockets
import subprocess

# RabbitMQ connection settings
RABBITMQ_HOST = '10.216.179.127'
RABBITMQ_USER = 'admin'
RABBITMQ_PASSWORD = 'Infobell@123'
QUEUE_NAMES = ['ES_AMD', 'ES_INTEL']

# Global queue for RabbitMQ -> WebSocket
ws_queue = asyncio.Queue()

# Event to control consumer start
start_event = asyncio.Event()

# Connected clients set
connected_clients = set()

# WebSocket server handler (websockets >= 11)
async def websocket_handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received from client: {message}")
            if message.strip().upper() == "START":
                if not start_event.is_set():
                    start_event.set()
                    print("✅ START command received. Starting consumers and publishers...")
                    # Run pub1.py and pub2.py in parallel
                    subprocess.Popen(["python3", "pub1.py"])
                    subprocess.Popen(["python3", "pub2.py"])
                else:
                    await websocket.send("ℹ Consumers already running.")
            else:
                await websocket.send("❌ Unknown command received")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

# RabbitMQ Consumer function (runs in background thread per queue)
def rabbitmq_consumer(loop, queue_name):
    def on_message(channel, method_frame, header_frame, body):
        message = f"[{queue_name}] {body.decode()}"
        print(f"Received from RabbitMQ: {message}")
        asyncio.run_coroutine_threadsafe(ws_queue.put(message), loop)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    print(f"Starting RabbitMQ consumer for queue: {queue_name}")
    try:
        channel.start_consuming()
    except Exception as e:
        print(f"Consumer for {queue_name} stopped: {e}")
    finally:
        connection.close()
'''
# Task to broadcast messages from ws_queue to connected clients
async def ws_broadcaster():
    while True:
        message = await ws_queue.get()
        if connected_clients:
            await asyncio.gather(*(client.send(message) for client in connected_clients if client.open))
        else:
            print("No clients connected to forward message.")
'''

async def ws_broadcaster():
    while True:
        message = await ws_queue.get()
        if connected_clients:
            await asyncio.gather(*(client.send(message) for client in connected_clients if not client.closed))
        else:
            print("No clients connected to forward message.")


# Main asyncio event loop
async def main():
    # Start WebSocket server
    print("🚀 Starting WebSocket Server on ws://0.0.0.0:8765")
    ws_server = await websockets.serve(websocket_handler, '0.0.0.0', 8765)

    # Start broadcaster task
    asyncio.create_task(ws_broadcaster())

    # Wait until START command is received
    print("⏳ Waiting for START command from any client...")
    await start_event.wait()

    # Start RabbitMQ consumers for both queues in background threads
    loop = asyncio.get_running_loop()
    for queue_name in QUEUE_NAMES:
        threading.Thread(target=rabbitmq_consumer, args=(loop, queue_name), daemon=True).start()

    # Keep the server running forever
    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
