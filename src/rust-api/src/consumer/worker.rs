use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::message::Message;
use rdkafka::ClientConfig;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::time::{self, Duration};

use crate::config::Config;
use crate::services::QuickwitService;

const TOPICS: &[&str] = &[
    "ocsf-events",
    "siem-alerts",
    "metrics-raw",
    "raw-api",
    "raw-auth",
    "raw-firewall",
    "raw-nginx",
    "raw-syslog",
];

const INDEXES: &[&str] = &["ocsf-events", "siem-alerts", "metrics-raw", "raw-logs"];

const CHANNEL_CAPACITY: usize = 10_000;
const BATCH_SIZE: usize = 500;
const FLUSH_INTERVAL: Duration = Duration::from_millis(500);
const LOG_FIRST_N_PER_TOPIC: u64 = 5;
const LOG_EVERY_N_PER_TOPIC: u64 = 100;

pub async fn start_recording(config: Config, qw_service: Arc<QuickwitService>) {
    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "rust-siem-worker")
        .set("bootstrap.servers", &config.kafka_brokers)
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "6000")
        .set("enable.auto.commit", "true")
        .set("auto.offset.reset", "earliest")
        .create()
        .expect("Consumer creation failed");

    consumer
        .subscribe(TOPICS)
        .expect("Can't subscribe to specified topics");

    let senders = start_index_workers(qw_service);

    println!("🧵 Worker Thread: Monitoring Redpanda topics: {:?}", TOPICS);

    let mut consumed_by_topic = HashMap::<String, u64>::new();

    loop {
        let msg = match consumer.recv().await {
            Ok(msg) => msg,
            Err(err) => {
                eprintln!("Redpanda consume error: {}", err);
                continue;
            }
        };

        let topic = msg.topic();
        let payload = match msg.payload_view::<str>() {
            None => "",
            Some(Ok(payload)) => payload,
            Some(Err(err)) => {
                eprintln!(
                    "Payload decode failed topic={} partition={} offset={}: {}",
                    topic,
                    msg.partition(),
                    msg.offset(),
                    err
                );
                continue;
            }
        };

        if payload.is_empty() {
            println!(
                "Consumed empty payload topic={} partition={} offset={}",
                topic,
                msg.partition(),
                msg.offset()
            );
            continue;
        }

        let index = match index_for_topic(topic) {
            Some(index) => index,
            None => {
                println!("Unknown topic: {}", topic);
                continue;
            }
        };

        let consumed_count = consumed_by_topic.entry(topic.to_string()).or_default();
        *consumed_count += 1;

        if *consumed_count <= LOG_FIRST_N_PER_TOPIC || *consumed_count % LOG_EVERY_N_PER_TOPIC == 0
        {
            println!(
                "Consumed #{} topic={} partition={} offset={} -> index={} payload={}",
                consumed_count,
                topic,
                msg.partition(),
                msg.offset(),
                index,
                truncate_payload(payload, 240)
            );
        }

        match serde_json::from_str::<Value>(payload) {
            Ok(document) => {
                let Some(sender) = senders.get(index) else {
                    eprintln!("No Quickwit worker configured for index: {}", index);
                    continue;
                };

                if let Err(err) = sender.send(document).await {
                    eprintln!(
                        "Quickwit ingest channel closed for topic {} -> {}: {}",
                        topic, index, err
                    );
                    break;
                }
            }
            Err(err) => {
                eprintln!(
                    "JSON parse failed for topic {}: {} payload={}",
                    topic,
                    err,
                    truncate_payload(payload, 240)
                );
            }
        }
    }
}

fn start_index_workers(
    qw_service: Arc<QuickwitService>,
) -> HashMap<&'static str, mpsc::Sender<Value>> {
    let mut senders = HashMap::new();

    for index in INDEXES {
        let (tx, rx) = mpsc::channel(CHANNEL_CAPACITY);
        senders.insert(*index, tx);

        let worker_service = Arc::clone(&qw_service);
        tokio::spawn(async move {
            run_index_worker(*index, worker_service, rx).await;
        });
    }

    senders
}

async fn run_index_worker(
    index: &'static str,
    qw_service: Arc<QuickwitService>,
    mut rx: mpsc::Receiver<Value>,
) {
    let mut batch = Vec::with_capacity(BATCH_SIZE);
    let mut flush_interval = time::interval(FLUSH_INTERVAL);

    loop {
        tokio::select! {
            received = rx.recv() => {
                match received {
                    Some(document) => {
                        batch.push(document);

                        if batch.len() >= BATCH_SIZE {
                            flush_batch(index, &qw_service, &mut batch).await;
                        }
                    }
                    None => {
                        flush_batch(index, &qw_service, &mut batch).await;
                        break;
                    }
                }
            }
            _ = flush_interval.tick() => {
                flush_batch(index, &qw_service, &mut batch).await;
            }
        }
    }
}

async fn flush_batch(index: &str, qw_service: &QuickwitService, batch: &mut Vec<Value>) {
    if batch.is_empty() {
        return;
    }

    let documents = std::mem::take(batch);
    let count = documents.len();

    match qw_service.ingest_documents(index, &documents).await {
        Ok(()) => println!("Ingested {} documents into index: {}", count, index),
        Err(err) => eprintln!(
            "Quickwit ingest failed for index {} batch_size={}: {}",
            index, count, err
        ),
    }
}

fn index_for_topic(topic: &str) -> Option<&'static str> {
    match topic {
        "ocsf-events" => Some("ocsf-events"),
        "siem-alerts" => Some("siem-alerts"),
        "metrics-raw" => Some("metrics-raw"),
        "raw-api" | "raw-auth" | "raw-firewall" | "raw-nginx" | "raw-syslog" => Some("raw-logs"),
        _ => None,
    }
}

fn truncate_payload(payload: &str, max_len: usize) -> String {
    if payload.len() <= max_len {
        return payload.to_string();
    }

    let mut truncated = payload.chars().take(max_len).collect::<String>();
    truncated.push_str("...");
    truncated
}
