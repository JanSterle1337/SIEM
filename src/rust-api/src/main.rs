use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::ClientConfig;
use rdkafka::message::Message;
use reqwest::Client;
use serde_json::Value;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    let http_client = Client::new();

    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "rust-storage-group")
        .set("bootstrap.servers", "localhost:19092")
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "6000")
        .set("enable.auto.commit", "true")
        .create()?;


    consumer.subscribe(&["ocsf-events", "siem-alerts"]);

    println!("Rust Storage API started. Monitoring 'ocsf-events' and 'siem-alerts'...");

    while let Ok(msg) = consumer.recv().await {

        let topic = msg.topic();

        let payload = match msg.payload_view::<str>() {
            None => "",
            Some(Ok(s)) => s,
            Some(Err(_)) => continue,
        };

        // Parse to ensure it's valid OCSF JSON
        if let Ok(json_data) = serde_json::from_str::<Value>(payload) {

            let ingest_url = match topic {
                "siem-alerts" => {
                    println!("📥 Processing ALERT: {}", json_data["alert_type"]);
                    "http://localhost:7280/api/v1/siem-alerts/ingest"
                },
                _ => {
                    println!("📥 Processing LOG: Class {}", json_data["class_uid"]);
                    "http://localhost:7280/api/v1/ocsf-events/ingest"
                },
            };

            println!("Recieved from topic [{}]. Forwarding to Quickwit...", topic);

            // 2. Forward to Quickwit
            let res = http_client
                .post(ingest_url)
                .timeout(std::time::Duration::from_secs(5))
                .json(&json_data)
                .send()
                .await;

            match res {
                Ok(response) => {
                    if response.status().is_success() {
                        println!("Successfully indexed Class {} in Quickwit", json_data["class_uid"]);
                    } else {
                        let error_text = response.text().await.unwrap_or_default();
                        eprintln!("Quickwit rejected event: {}", error_text);
                    }
                }
                Err(e) => eprintln!("❌ Network Error: {}", e),
            }
        }
    }

    Ok(())
    
}
