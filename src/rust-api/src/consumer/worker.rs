use rdkafka::ClientConfig;
use std::sync::Arc;
use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::message::Message;
use serde_json::Value;


use crate::config::Config;
use crate::services::QuickwitService;
use crate::models::{OcsfLog, SiemAlert};

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

    consumer.subscribe(&["ocsf-events", "siem-alerts"])
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

        match topic {
            "ocsf-events" => {
                if let Ok(log) = serde_json::from_str::<OcsfLog>(payload) {
                    let _ = qw_service.ingest_log(&log).await;
                }
            },
            "siem-alerts" => {
                // For alerts, we can use a more direct Value approach or the SiemAlert struct
                if let Ok(alert) = serde_json::from_str::<SiemAlert>(payload) {
                    // We'll add a generic ingest method to service later if needed
                    let _ = qw_service.search("siem-alerts", "TODO").await;
                    // For now, let's just log it to console to verify
                    println!("🚨 Alert Worker: Received {}", alert.alert_type);
                }
            },
            _ => println!("Unknown topic: {}", topic),
        }
    }

}