use std::sync::Arc;

use rust_api::config::Config;
use rust_api::consumer::worker;
use rust_api::services::QuickwitService;

#[tokio::main]
async fn main() {
    let config = Config::from_env();
    let qw_service = Arc::new(QuickwitService::new(&config));

    println!("🔥 Quickwit ingestion worker starting...");
    worker::start_recording(config, qw_service).await;
}
