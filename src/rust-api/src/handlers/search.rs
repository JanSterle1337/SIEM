use std::sync::Arc;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::services::{QuickwitSearchResponse, QuickwitService};

const DEFAULT_LIMIT: usize = 50;
const MAX_LIMIT: usize = 500;

#[derive(Debug, Deserialize)]
pub struct LogsQuery {
    pub query: Option<String>,
    pub host: Option<String>,
    pub source_type: Option<String>,
    pub limit: Option<usize>,
}

#[derive(Debug, Deserialize)]
pub struct MetricsQuery {
    pub host: Option<String>,
    pub metric_name: Option<String>,
    pub limit: Option<usize>,
}

#[derive(Debug, Deserialize)]
pub struct AlertsQuery {
    pub query: Option<String>,
    pub severity: Option<String>,
    pub detection_type: Option<String>,
    pub status: Option<String>,
    pub host: Option<String>,
    pub limit: Option<usize>,
}

#[derive(Debug, Serialize)]
pub struct ApiListResponse {
    pub items: Vec<Value>,
    pub total: u64,
    pub elapsed_ms: u64,
}

#[derive(Debug, Serialize)]
pub struct OverviewResponse {
    pub alert_count: u64,
    pub event_counts: Value,
    pub alerts_by_severity: Value,
    pub alerts_by_type: Value,
    pub top_hosts: Vec<HostCount>,
    pub recent_alerts: Vec<Value>,
}

#[derive(Debug, Serialize)]
pub struct HostCount {
    pub host: String,
    pub count: u64,
}

type ApiResult<T> = Result<Json<T>, (StatusCode, Json<Value>)>;

pub async fn handle_get_logs(
    State(qw): State<Arc<QuickwitService>>,
    Query(params): Query<LogsQuery>,
) -> ApiResult<ApiListResponse> {
    let mut clauses = Vec::new();
    push_text_query(&mut clauses, params.query.as_deref());
    push_field_clause(&mut clauses, "host", params.host.as_deref());
    push_field_clause(&mut clauses, "source_type", params.source_type.as_deref());

    search_list(&qw, "raw-logs", clauses, params.limit).await
}

pub async fn handle_get_metrics(
    State(qw): State<Arc<QuickwitService>>,
    Query(params): Query<MetricsQuery>,
) -> ApiResult<ApiListResponse> {
    let mut clauses = Vec::new();
    push_field_clause(&mut clauses, "host", params.host.as_deref());
    push_field_clause(&mut clauses, "metric_name", params.metric_name.as_deref());

    search_list(&qw, "metrics-raw", clauses, params.limit).await
}

pub async fn handle_get_alerts(
    State(qw): State<Arc<QuickwitService>>,
    Query(params): Query<AlertsQuery>,
) -> ApiResult<ApiListResponse> {
    let mut clauses = Vec::new();
    push_text_query(&mut clauses, params.query.as_deref());
    push_field_clause(&mut clauses, "severity", params.severity.as_deref());
    push_field_clause(
        &mut clauses,
        "detection_type",
        params.detection_type.as_deref(),
    );
    push_field_clause(&mut clauses, "status", params.status.as_deref());
    push_field_clause(&mut clauses, "host", params.host.as_deref());

    search_list(&qw, "siem-alerts", clauses, params.limit).await
}

pub async fn handle_get_overview(
    State(qw): State<Arc<QuickwitService>>,
) -> ApiResult<OverviewResponse> {
    let ocsf_count = search_quickwit_optional(&qw, "ocsf-events", "*", 1)
        .await
        .num_hits;
    let metrics_count = search_quickwit_optional(&qw, "metrics-raw", "*", 1)
        .await
        .num_hits;
    let raw_count = search_quickwit_optional(&qw, "raw-logs", "*", 1)
        .await
        .num_hits;
    let alerts = search_quickwit_optional(&qw, "siem-alerts", "*", 100).await;
    let recent_alerts = alerts.hits.iter().take(10).cloned().collect::<Vec<_>>();

    Ok(Json(OverviewResponse {
        alert_count: alerts.num_hits,
        event_counts: json!({
            "ocsf_events": ocsf_count,
            "metrics_raw": metrics_count,
            "raw_logs": raw_count,
            "siem_alerts": alerts.num_hits,
        }),
        alerts_by_severity: count_by_field(&alerts.hits, "severity"),
        alerts_by_type: count_by_field(&alerts.hits, "detection_type"),
        top_hosts: top_hosts(&alerts.hits),
        recent_alerts,
    }))
}

async fn search_list(
    qw: &QuickwitService,
    index: &str,
    clauses: Vec<String>,
    limit: Option<usize>,
) -> ApiResult<ApiListResponse> {
    let query = if clauses.is_empty() {
        "*".to_string()
    } else {
        clauses.join(" AND ")
    };

    let response = search_quickwit(qw, index, &query, normalized_limit(limit)).await?;
    Ok(Json(ApiListResponse {
        items: response.hits,
        total: response.num_hits,
        elapsed_ms: response.elapsed_time_micros / 1_000,
    }))
}

async fn search_quickwit(
    qw: &QuickwitService,
    index: &str,
    query: &str,
    limit: usize,
) -> Result<QuickwitSearchResponse, (StatusCode, Json<Value>)> {
    qw.search(index, query, limit)
        .await
        .map_err(|err| api_error(StatusCode::BAD_GATEWAY, err))
}

async fn search_quickwit_optional(
    qw: &QuickwitService,
    index: &str,
    query: &str,
    limit: usize,
) -> QuickwitSearchResponse {
    match qw.search(index, query, limit).await {
        Ok(response) => response,
        Err(err) => {
            eprintln!("Overview search failed for index {}: {}", index, err);
            QuickwitSearchResponse {
                num_hits: 0,
                elapsed_time_micros: 0,
                hits: Vec::new(),
            }
        }
    }
}

fn normalized_limit(limit: Option<usize>) -> usize {
    limit.unwrap_or(DEFAULT_LIMIT).clamp(1, MAX_LIMIT)
}

fn push_text_query(clauses: &mut Vec<String>, value: Option<&str>) {
    let Some(value) = clean_param(value) else {
        return;
    };

    if value != "*" {
        clauses.push(escape_query_value(value));
    }
}

fn push_field_clause(clauses: &mut Vec<String>, field: &str, value: Option<&str>) {
    let Some(value) = clean_param(value) else {
        return;
    };

    clauses.push(format!("{}:{}", field, escape_query_value(value)));
}

fn clean_param(value: Option<&str>) -> Option<&str> {
    value.map(str::trim).filter(|value| !value.is_empty())
}

fn escape_query_value(value: &str) -> String {
    if value == "*" {
        return value.to_string();
    }

    if value
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_' | '.' | '/'))
    {
        value.to_string()
    } else {
        format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
    }
}

fn count_by_field(items: &[Value], field: &str) -> Value {
    let mut counts = serde_json::Map::new();

    for item in items {
        let key = item
            .get(field)
            .and_then(Value::as_str)
            .unwrap_or("unknown")
            .to_string();
        let count = counts.get(&key).and_then(Value::as_u64).unwrap_or(0) + 1;
        counts.insert(key, Value::from(count));
    }

    Value::Object(counts)
}

fn top_hosts(items: &[Value]) -> Vec<HostCount> {
    let mut counts = serde_json::Map::new();

    for item in items {
        let Some(host) = item.get("host").and_then(Value::as_str) else {
            continue;
        };

        if host.is_empty() {
            continue;
        }

        let count = counts.get(host).and_then(Value::as_u64).unwrap_or(0) + 1;
        counts.insert(host.to_string(), Value::from(count));
    }

    let mut hosts = counts
        .into_iter()
        .map(|(host, count)| HostCount {
            host,
            count: count.as_u64().unwrap_or(0),
        })
        .collect::<Vec<_>>();
    hosts.sort_by(|left, right| right.count.cmp(&left.count));
    hosts.truncate(5);
    hosts
}

fn api_error(status: StatusCode, message: String) -> (StatusCode, Json<Value>) {
    (status, Json(json!({ "error": message })))
}
