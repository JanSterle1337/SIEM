use rdkafka::ClientConfig;
use std::sync::Arc;
use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::message::Message;
use serde_json::Value;


use crate::config::Config;
use crate::services::QuickwitService;

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

    consumer.subscribe(&[
        "ocsf-events",
        "siem-alerts",
        /*"metrics-raw",
        "raw-api",
        "raw-auth",
        "raw-firewall",
        "raw-nginx",
        "raw-syslog",*/
    ])
        .expect("Can't subscribe to specified topics");

    println!("🧵 Worker Thread: Monitoring Redpanda topics...");

    while let Ok(msg) = consumer.recv().await {
        let topic = msg.topic();
        let payload = match msg.payload_view::<str>() {
            None => "",
            Some(Ok(s)) => s,
            Some(Err(_)) => continue,
        };

        if payload.is_empty() { continue; }

        let index = match index_for_topic(topic) {
            Some(index) => index,
            None => {
                println!("Unknown topic: {}", topic);
                continue;
            }
        };

        println!("Consumed topic: {} -> target index: {}", topic, index);
        println!(
            "Payload preview [{}]: {}",
            topic,
            truncate_payload(payload, 240)
        );

        match serde_json::from_str::<Value>(payload) {
            Ok(document) => {
                if let Err(err) = qw_service.ingest_document(index, &document).await {
                    eprintln!("Quickwit ingest failed for topic {} -> {}: {}", topic, index, err);
                } else {
                    println!("Ingested document into index: {}", index);
                }
            }
            Err(err) => {
                eprintln!("JSON parse failed for topic {}: {}", topic, err);
            }
        }
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
