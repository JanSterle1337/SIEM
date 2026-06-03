pub mod search;
pub use search::{
    handle_get_alerts, handle_get_logs, handle_get_metrics, handle_get_overview, AlertsQuery,
    ApiListResponse, LogsQuery, MetricsQuery, OverviewResponse,
};

use crate::services::QuickwitService;
use axum::{routing::get, Router};
use std::sync::Arc;

pub fn create_router(qw_service: Arc<QuickwitService>) -> Router {
    Router::new()
        .route("/api/logs", get(handle_get_logs))
        .route("/api/metrics", get(handle_get_metrics))
        .route("/api/alerts", get(handle_get_alerts))
        .route("/api/overview", get(handle_get_overview))
        .with_state(qw_service)
}
