use std::collections::HashMap;
use std::sync::Arc;

use chrono::Utc;
use rdkafka::consumer::{CommitMode, Consumer, StreamConsumer};
use rdkafka::message::Message;
use rdkafka::ClientConfig;
use serde_json::Value;
use tokio::time::{self, Duration};

use crate::config::Config;
use crate::services::{ColdStorageRecord, ParquetService};

const TOPICS: &[&str] = &[
    "ocsf-events",
    "siem-alerts",
    "metrics-raw",
    "ground-truth-events",
    "raw-api",
    "raw-auth",
    "raw-firewall",
    "raw-nginx",
    "raw-syslog",
];

const FLUSH_INTERVAL: Duration = Duration::from_secs(60);
const LOG_FIRST_N_PER_TOPIC: u64 = 5;
const LOG_EVERY_N_PER_TOPIC: u64 = 1_000;

pub async fn start_recording(config: Config, parquet_service: Arc<ParquetService>) {
    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "rust-siem-parquet-worker")
        .set("bootstrap.servers", &config.kafka_brokers)
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "6000")
        .set("enable.auto.commit", "false")
        .set("auto.offset.reset", "earliest")
        .create()
        .expect("Parquet consumer creation failed");

    consumer
        .subscribe(TOPICS)
        .expect("Can't subscribe Parquet worker to specified topics");

    println!(
        "🧊 Parquet Worker: Monitoring Redpanda topics: {:?}",
        TOPICS
    );
    println!(
        "🧊 Parquet Worker: Writing cold storage under {}",
        config.parquet_storage_path
    );

    let mut buffers = HashMap::<String, Vec<ColdStorageRecord>>::new();
    let mut consumed_by_topic = HashMap::<String, u64>::new();
    let mut flush_interval = time::interval(FLUSH_INTERVAL);

    loop {
        tokio::select! {
            received = consumer.recv() => {
                let msg = match received {
                    Ok(msg) => msg,
                    Err(err) => {
                        eprintln!("Parquet worker Redpanda consume error: {}", err);
                        continue;
                    }
                };

                let topic = msg.topic();
                let Some(dataset) = dataset_for_topic(topic) else {
                    println!("Parquet worker unknown topic: {}", topic);
                    continue;
                };

                let payload = match msg.payload_view::<str>() {
                    None => "",
                    Some(Ok(payload)) => payload,
                    Some(Err(err)) => {
                        eprintln!(
                            "Parquet worker payload decode failed topic={} partition={} offset={}: {}",
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
                        "Parquet worker consumed empty payload topic={} partition={} offset={}",
                        topic,
                        msg.partition(),
                        msg.offset()
                    );
                    continue;
                }

                let document = match serde_json::from_str::<Value>(payload) {
                    Ok(document) => document,
                    Err(err) => {
                        eprintln!(
                            "Parquet worker JSON parse failed topic={} partition={} offset={}: {} payload={}",
                            topic,
                            msg.partition(),
                            msg.offset(),
                            err,
                            truncate_payload(payload, 240)
                        );
                        continue;
                    }
                };

                let consumed_count = consumed_by_topic.entry(topic.to_string()).or_default();
                *consumed_count += 1;

                if *consumed_count <= LOG_FIRST_N_PER_TOPIC
                    || *consumed_count % LOG_EVERY_N_PER_TOPIC == 0
                {
                    println!(
                        "Parquet buffered #{} topic={} partition={} offset={} -> dataset={} payload={}",
                        consumed_count,
                        topic,
                        msg.partition(),
                        msg.offset(),
                        dataset,
                        truncate_payload(payload, 240)
                    );
                }

                buffers
                    .entry(dataset.to_string())
                    .or_default()
                    .push(ColdStorageRecord {
                        event_time: event_time_for_document(&document),
                        ingested_at: Utc::now(),
                        topic: topic.to_string(),
                        dataset: dataset.to_string(),
                        payload: serde_json::to_string(&document)
                            .unwrap_or_else(|_| payload.to_string()),
                    });
            }
            _ = flush_interval.tick() => {
                if flush_buffers(&parquet_service, &mut buffers).await {
                    if let Err(err) = consumer.commit_consumer_state(CommitMode::Async) {
                        eprintln!("Parquet worker offset commit failed: {}", err);
                    }
                }
            }
        }
    }
}

async fn flush_buffers(
    parquet_service: &Arc<ParquetService>,
    buffers: &mut HashMap<String, Vec<ColdStorageRecord>>,
) -> bool {
    let datasets = buffers.keys().cloned().collect::<Vec<_>>();
    let mut flushed_any = false;
    let mut all_flushes_succeeded = true;

    for dataset in datasets {
        let Some(records) = buffers.get_mut(&dataset) else {
            continue;
        };

        if records.is_empty() {
            continue;
        }

        let records_to_write = std::mem::take(records);
        let count = records_to_write.len();

        match parquet_service.write_records(&dataset, &records_to_write) {
            Ok(path) => {
                flushed_any = true;
                println!(
                    "Parquet wrote {} records for dataset={} file={}",
                    count,
                    dataset,
                    path.display()
                );
            }
            Err(err) => {
                all_flushes_succeeded = false;
                records.extend(records_to_write);
                eprintln!(
                    "Parquet write failed for dataset={} record_count={}: {}",
                    dataset, count, err
                );
            }
        }
    }

    flushed_any && all_flushes_succeeded
}

fn dataset_for_topic(topic: &str) -> Option<&'static str> {
    match topic {
        "ocsf-events" => Some("ocsf-events"),
        "siem-alerts" => Some("siem-alerts"),
        "metrics-raw" => Some("metrics-raw"),
        "ground-truth-events" => Some("ground-truth-events"),
        "raw-api" | "raw-auth" | "raw-firewall" | "raw-nginx" | "raw-syslog" => Some("raw-logs"),
        _ => None,
    }
}

fn event_time_for_document(document: &Value) -> Option<String> {
    ["time", "timestamp", "created_at"]
        .iter()
        .find_map(|field| document.get(*field))
        .and_then(|value| match value {
            Value::String(value) => Some(value.clone()),
            Value::Number(value) => Some(value.to_string()),
            _ => None,
        })
}

fn truncate_payload(payload: &str, max_len: usize) -> String {
    if payload.len() <= max_len {
        return payload.to_string();
    }

    let mut truncated = payload.chars().take(max_len).collect::<String>();
    truncated.push_str("...");
    truncated
}
