use std::sync::Arc;

use axum::http::Method;
use rust_api::config::Config;
use rust_api::handlers;
use rust_api::services::QuickwitService;
use tower_http::cors::{Any, CorsLayer};

#[tokio::main]
async fn main() {
    let config = Config::from_env();
    let qw_service = Arc::new(QuickwitService::new(&config));

    println!("SIEM API starting...");

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST])
        .allow_headers(Any);

    let addr = format!("0.0.0.0:{}", config.server_port);
    println!("🌐 Web server listening on {}", addr);

    let app = handlers::create_router(Arc::clone(&qw_service)).layer(cors);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();

    axum::serve(listener, app).await.unwrap();
}
