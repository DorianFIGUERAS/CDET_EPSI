import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import requests

from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

logger = logging.getLogger("uvicorn.error")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "my-topic"
GROUP_ID = "my-group"
NUM_WORKERS = 4  # must match gunicorn/uvicorn worker count

producer: KafkaProducer | None = None
consumer: KafkaConsumer | None = None


def create_kafka_topic() -> None:
    """Create the Kafka topic if it does not already exist."""
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        existing = admin.list_topics()
        if TOPIC_NAME not in existing:
            topic = NewTopic(
                name=TOPIC_NAME,
                num_partitions=NUM_WORKERS,
                replication_factor=1,
            )
            admin.create_topics([topic])
            logger.info("Topic '%s' created with %d partitions.", TOPIC_NAME, NUM_WORKERS)
        else:
            logger.info("Topic '%s' already exists, skipping creation.", TOPIC_NAME)
    except TopicAlreadyExistsError:
        # Race condition between workers — not blocking
        logger.info("Topic '%s' was created by another worker.", TOPIC_NAME)
    except Exception as exc:
        logger.warning("Topic creation failed (non-blocking): %s", exc)
    finally:
        admin.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer

    create_kafka_topic()

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=1000,
    )

    yield

    if producer:
        producer.close()
    if consumer:
        consumer.close()


app = FastAPI(lifespan=lifespan)


@app.post("/produce")
def produce_message(message: str):
    """Produce a message to Kafka and return the partition it landed on."""
    pid = os.getpid()
    payload = {"message": message, "producer_pid": pid}
    future = producer.send(TOPIC_NAME, value=payload)
    record_metadata = future.get(timeout=10)
    return {
        "status": "sent",
        "topic": record_metadata.topic,
        "partition": record_metadata.partition,
        "offset": record_metadata.offset,
        "producer_pid": pid,
    }


@app.get("/consume")
def consume_messages():
    """Consume pending messages from Kafka and return them with partition + PID info."""
    pid = os.getpid()
    messages = []
    for msg in consumer:
        messages.append(
            {
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "value": msg.value,
                "consumer_pid": pid,
            }
        )
    return {"messages": messages, "consumer_pid": pid}


@app.get("/generate")
def stream_ollama_request(prompt: str, model: str = "ministral-3:3b"):
    """Forward a streaming generation request to the local Ollama instance."""
    url = "http://ollama:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": True}

    def event_generator():
        response = requests.post(url, json=payload, stream=True)
        for line in response.iter_lines():
            if line:
                yield line.decode("utf-8") + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


if __name__ == "__main__":
    print("Ce script doit être lancé via uvicorn pour exposer l'API.")
