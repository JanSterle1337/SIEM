use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SiemAlert {
    pub alert_type: String,
    pub severity: String,
    pub source_ip: String,
    pub event_count: u64,
    pub window_seconds: u64,
    pub timestamp: f64,
    pub msg: String
}