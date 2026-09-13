import os
import pika
import json

rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "guest")


def produce(router_ip, username, password, device_type="cisco_ios"):
    payload = {"ip": router_ip, "username": username, "password": password}

    message_body = json.dumps(payload)

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="jobs", exchange_type="direct")
    channel.queue_declare(queue="router_jobs")
    channel.queue_bind(
        queue="router_jobs", exchange="jobs", routing_key="check_interfaces"
    )

    channel.basic_publish(
        exchange="jobs", routing_key="check_interfaces", body=message_body
    )

    connection.close()


if __name__ == "__main__":
    produce(
        router_ip="192.168.1.44",
        username="admin",
        password="your_router_password",
    )
