import json
import time
from kafka import KafkaConsumer, KafkaProducer
from collections import defaultdict, deque


BROKERS = ['localhost:19092']
INPUT_TOPIC = 'ocsf-events'
OUTPUT_TOPIC = 'siem-alerts'
WINDOW_SIZE = 30
THRESHOLD = 5


attack_tracker = defaultdict(lambda: deque())


consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=BROKERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest'
)

producer = KafkaProducer(
    bootstrap_servers=BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"🛡️  SIEM Detection Engine active. Monitoring '{INPUT_TOPIC}'...")


for message in consumer:
    event = message.value

    if event.get('class_uid') == 300201 and event.get('disposition_id') == 2:
        ip = event.get('src_endpoint', {}).get('ip', 'unknown')
        now = time.time()

        attack_tracker[ip].append(now)

        while attack_tracker[ip] and attack_tracker[ip][0] < now - WINDOW_SIZE:
            attack_tracker[ip].popleft()
        
        print(f"🕵️  Failure detected from {ip}. (Count: {len(attack_tracker[ip])})")

        if len(attack_tracker[ip]) >= THRESHOLD:
            alert = {
                "alert_type": "Brute Force Attempt",
                "severity": "High",
                "source_ip": ip,
                "event_count": len(attack_tracker[ip]),
                "window_seconds": WINDOW_SIZE,
                "timestamp": now,
                "msg": f"Detected {len(attack_tracker[ip])} failed logins in {WINDOW_SIZE}s" 
            }
            producer.send(OUTPUT_TOPIC, alert)
            print(f"🚨 ALERT SENT: Brute force from {ip}!")





