import os
import json
import pika
from datetime import datetime, timezone
from pymongo import MongoClient
from netmiko import ConnectHandler


MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:secretpassword@mongo:27017/")
DB_NAME = os.environ.get("DB_NAME", "ipa2026_db")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
interfaces_collection = db["router_interfaces"]


RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "guest")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

def process_message(ch, method, properties, body):
    try:
        raw_data = json.loads(body.decode('utf-8'))
        
        # Clean up keys by stripping leading/trailing whitespace
        data = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_data.items()}
        
        # Check for 'ip', 'host', or 'router_ip'
        router_ip = data.get("ip") or data.get("host") or data.get("router_ip")
        username = data.get("username")
        password = data.get("password")

        if not router_ip:
            print(f"[!] Invalid message payload (missing IP/Host): {raw_data}", flush=True)
            # Acknowledge and discard invalid messages so they don't block the queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"[*] Connecting to Router: {router_ip}...", flush=True)

        device = {
            'device_type': 'cisco_ios',
            'host': router_ip,
            'username': username,
            'password': password,
        }

        with ConnectHandler(**device) as net_connect:
            parsed_output = net_connect.send_command("show ip interface brief", use_textfsm=True)

        print(f"Received job for router {router_ip}", flush=True)

        print(json.dumps(parsed_output, indent=2), flush=True)

        # Strip any unwanted spaces when extracting router_ip
        router_ip = (data.get("ip") or data.get("host") or data.get("router_ip", "")).strip()

        record = {
            "router_ip": router_ip,
            "interfaces": parsed_output,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
        }

        insert_result = interfaces_collection.insert_one(record)
        print(f"[+] Successfully saved data for {router_ip} (ID: {insert_result.inserted_id})", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[!] Error processing message: {e}", flush=True)
        # Ack invalid/unparseable messages to prevent infinite processing loops
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="jobs", exchange_type="direct")
    channel.queue_declare(queue="router_jobs")
    channel.queue_bind(queue="router_jobs", exchange="jobs", routing_key="check_interfaces")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="router_jobs", on_message_callback=process_message)

    print("[*] Worker1 waiting for messages. To exit press CTRL+C", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()