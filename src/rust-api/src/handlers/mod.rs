pub mod search;
pub use search::SearchQuery;
pub use search::handle_get_logs;
pub use search::handle_get_alerts;

use axum::{routing::get, Router};
use std::sync::Arc;
use crate::services::QuickwitService;

pub fn create_router(qw_service: Arc<QuickwitService>) -> Router {
    Router::new()
        .route("/api/logs", get(handle_get_logs))
        .route("/api/alerts", get(handle_get_alerts))
        .with_state(qw_service)
}