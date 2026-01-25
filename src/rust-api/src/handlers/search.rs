use axum::{extract::{Query, State}, Json};
use std::sync::Arc;
use crate::services::QuickwitService;
use serde_json::Value;

#[derive(serde::Deserialize)]
pub struct SearchQuery {
    pub query: Option<String>
}

pub async fn handle_get_logs(
    State(qw): State<Arc<QuickwitService>>,
    Query(params): Query<SearchQuery>
) -> Json<Value> {
    let q = params.query.unwrap_or_else(|| '*'.to_string());
    let results = qw.search("ocsf-events", &q).await.unwrap_or_default();
    Json(results)
}


pub async fn handle_get_alerts(
    State(qw): State<Arc<QuickwitService>>,
) -> Json<Value> {
    let results = qw.search("siem-alerts", "*").await.unwrap_or_default();
    Json(results)
}

