use std::sync::Arc;

use rust_api::config::Config;
use rust_api::consumer::parquet_worker;
use rust_api::services::ParquetService;

#[tokio::main]
async fn main() {
    let config = Config::from_env();
    let parquet_service = Arc::new(ParquetService::new(&config));

    println!("🧊 Parquet cold-storage worker starting...");
    parquet_worker::start_recording(config, parquet_service).await;
}
