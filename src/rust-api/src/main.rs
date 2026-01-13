use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::ClientConfig;
use rdkafka::message::Message;
use reqwest::Client;
use serde_json::Value;



#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    
    let quickwit_url = "http://localhost:7280/api/v1/ocsf-events/ingest";
    let http_client = Client::new();

    let consumer: StreamConsumer = ClientConfig::new()
        .set("group.id", "rust-storage-group")
        .set("bootstrap.servers", "localhost:19092")
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "6000")
        .set("enable.auto.commit", "true")
        .create()?;


    consumer.subscribe(&["ocsf-events"]);

    println!("🦀 Rust Storage API started. Monitoring Redpanda for OCSF events...");        

    while let Ok(msg) = consumer.recv().await {
        let payload = match msg.payload_view::<str>() {
            None => "",
            Some(Ok(s)) => s,
            Some(Err(_)) => continue,
        };

        // Parse to ensure it's valid OCSF JSON
        if let Ok(ocsf_json) = serde_json::from_str::<Value>(payload) {
            println!("📥 Processing event: Class {}", ocsf_json["class_uid"]);

            // 2. Forward to Quickwit
            let res = http_client
                .post(quickwit_url)
                .json(&ocsf_json)
                .send()
                .await;

            match res {
                Ok(_) => println!("Successfully indexed in Quickwit"),
                Err(e) => eprintln!("Quickwit Ingest Error: {}", e),
            }
        }
    }

    Ok(())
    
}
