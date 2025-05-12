import pandas as pd
import pika
import json

# RabbitMQ connection configuration
RABBITMQ_HOST = '10.216.179.127'
RABBITMQ_USER = 'admin'
RABBITMQ_PASSWORD = 'Infobell@123'

QUEUE_NAME = 'ES_AMD'

# RabbitMQ credentials and connection parameters
CREDENTIALS = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
CONNECTION_PARAMS = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=CREDENTIALS)

# Connect to RabbitMQ
connection = pika.BlockingConnection(CONNECTION_PARAMS)
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME, durable=True)

# Read Excel file
data_amd = 'data/amd.csv'  # Provide your Excel file path here
df = pd.read_csv(data_amd)

# Publish each row as JSON message
for index, row in df.iterrows():
    message = row.to_dict()
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    print(f"Published: {message}")

# Close connection
connection.close()

print("✅ All data published successfully.")
