use reqwest::Client;
use serde_json::Value;
use crate::config::Config;

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

    pub async fn ingest_document(&self, index: &str, document: &Value) -> Result<(), String> {
        let url = format!("{}/api/v1/{}/ingest?commit=force", self.base_url, index);
        let payload = serde_json::to_string(document)
            .map_err(|e| format!("serialize error: {}", e))?
            + "\n";

        let response = self.client.post(url)
            .header("Content-Type", "application/json")
            .body(payload)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        if response.status().is_success() {
            Ok(())
        } else {
            let status = response.status();
            let body = response.text().await.unwrap_or_else(|_| "<failed to read body>".to_string());
            Err(format!("Quickwit error: {} body: {}", status, body))
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
