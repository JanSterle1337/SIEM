use crate::config::Config;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize, Serialize)]
pub struct QuickwitSearchResponse {
    #[serde(default)]
    pub num_hits: u64,
    #[serde(default)]
    pub elapsed_time_micros: u64,
    #[serde(default)]
    pub hits: Vec<Value>,
}

pub struct QuickwitService {
    client: Client,
    base_url: String,
}

impl QuickwitService {
    pub fn new(config: &Config) -> Self {
        Self {
            client: Client::new(),
            base_url: config.quickwit_url.clone(),
        }
    }

    pub async fn ingest_documents(&self, index: &str, documents: &[Value]) -> Result<(), String> {
        if documents.is_empty() {
            return Ok(());
        }

        let url = format!(
            "{}/api/v1/{}/ingest?commit=auto&detailed_response=true",
            self.base_url, index
        );
        let mut payload = String::new();

        for document in documents {
            let line =
                serde_json::to_string(document).map_err(|e| format!("serialize error: {}", e))?;
            payload.push_str(&line);
            payload.push('\n');
        }

        let response = self
            .client
            .post(url)
            .header("Content-Type", "application/json")
            .body(payload)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let status = response.status();
        let body = response
            .text()
            .await
            .unwrap_or_else(|_| "<failed to read body>".to_string());

        if !status.is_success() {
            Err(format!("Quickwit error: {} body: {}", status, body))
        } else {
            let ingest_response = serde_json::from_str::<Value>(&body)
                .map_err(|e| format!("Quickwit response parse error: {} body: {}", e, body))?;
            let rejected_docs = ingest_response
                .get("num_rejected_docs")
                .and_then(Value::as_u64)
                .unwrap_or(0);

            if rejected_docs > 0 {
                Err(format!(
                    "Quickwit rejected {} documents for index {} body: {}",
                    rejected_docs, index, body
                ))
            } else {
                Ok(())
            }
        }
    }

    pub async fn search(
        &self,
        index: &str,
        query: &str,
        max_hits: usize,
    ) -> Result<QuickwitSearchResponse, String> {
        let url = format!("{}/api/v1/{}/search", self.base_url, index);
        let max_hits = max_hits.to_string();

        let response = self
            .client
            .get(url)
            .query(&[("query", query), ("max_hits", max_hits.as_str())])
            .send()
            .await
            .map_err(|e| e.to_string())?;

        response
            .json::<QuickwitSearchResponse>()
            .await
            .map_err(|e| e.to_string())
    }
}
