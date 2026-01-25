use reqwest::{Client, StatusCode};
use serde_json::Value;
use crate::config::Config;
use crate::models::OcsfLog;

pub struct QuickwitService {
    client: Client,
    base_url: String
}

impl QuickwitService {
    pub fn new(config: &Config) -> Self {
        Self {
            client: Client::new(),
            base_url: config.quickwit_url.clone()
        }
    }

    pub async fn ingest_log(&self, log: &OcsfLog) -> Result<(), String> {
        let url = format!("{}/api/v1/ocsf-events/ingest", self.base_url);

        let response = self.client.post(url)
            .json(log)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        if (response.status().is_success()) {
            Ok(())
        } else {
            Err(format!("Quickwit error: {}", response.status()))
        }
    }

    pub async fn search(&self, index: &str, query: &str) -> Result<Value, String> {
        let url = format!("{}/api/v1/{}/search?query={}&max_hits=50", self.base_url, index, query);

        let response = self.client.get(url)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        response.json::<Value>().await.map_err(|e| e.to_string())

    }
}