use std::fs::{self, File};
use std::path::PathBuf;
use std::sync::Arc;

use arrow_array::{ArrayRef, RecordBatch, StringArray, TimestampMicrosecondArray};
use arrow_schema::{DataType, Field, Schema, TimeUnit};
use chrono::{DateTime, Utc};
use parquet::arrow::ArrowWriter;
use uuid::Uuid;

use crate::config::Config;

#[derive(Debug, Clone)]
pub struct ColdStorageRecord {
    pub event_time: Option<String>,
    pub ingested_at: DateTime<Utc>,
    pub topic: String,
    pub dataset: String,
    pub payload: String,
}

pub struct ParquetService {
    base_path: PathBuf,
    schema: Arc<Schema>,
}

impl ParquetService {
    pub fn new(config: &Config) -> Self {
        Self {
            base_path: PathBuf::from(&config.parquet_storage_path),
            schema: Arc::new(Schema::new(vec![
                Field::new("event_time", DataType::Utf8, true),
                Field::new(
                    "ingested_at",
                    DataType::Timestamp(TimeUnit::Microsecond, Some("UTC".into())),
                    false,
                ),
                Field::new("topic", DataType::Utf8, false),
                Field::new("dataset", DataType::Utf8, false),
                Field::new("payload", DataType::Utf8, false),
            ])),
        }
    }

    pub fn write_records(
        &self,
        dataset: &str,
        records: &[ColdStorageRecord],
    ) -> Result<PathBuf, String> {
        if records.is_empty() {
            return Err("cannot write an empty Parquet record batch".to_string());
        }

        let partition_time = Utc::now();
        let dir = self.partition_dir(dataset, partition_time);
        fs::create_dir_all(&dir).map_err(|err| {
            format!(
                "failed to create Parquet partition directory {}: {}",
                dir.display(),
                err
            )
        })?;

        let file_path = dir.join(format!("part-{}.parquet", Uuid::new_v4()));
        let file = File::create(&file_path)
            .map_err(|err| format!("failed to create {}: {}", file_path.display(), err))?;

        let batch = self.record_batch(records)?;
        let mut writer = ArrowWriter::try_new(file, Arc::clone(&self.schema), None)
            .map_err(|err| format!("failed to create Parquet writer: {}", err))?;

        writer
            .write(&batch)
            .map_err(|err| format!("failed to write Parquet batch: {}", err))?;
        writer
            .close()
            .map_err(|err| format!("failed to close Parquet writer: {}", err))?;

        Ok(file_path)
    }

    fn partition_dir(&self, dataset: &str, partition_time: DateTime<Utc>) -> PathBuf {
        self.base_path
            .join(format!("dataset={}", sanitize_partition_value(dataset)))
            .join(format!("date={}", partition_time.format("%Y-%m-%d")))
            .join(format!("hour={}", partition_time.format("%H")))
    }

    fn record_batch(&self, records: &[ColdStorageRecord]) -> Result<RecordBatch, String> {
        let event_time = StringArray::from(
            records
                .iter()
                .map(|record| record.event_time.as_deref())
                .collect::<Vec<_>>(),
        );
        let ingested_at = TimestampMicrosecondArray::from_iter_values(
            records
                .iter()
                .map(|record| record.ingested_at.timestamp_micros()),
        )
        .with_timezone("UTC");
        let topic = StringArray::from(
            records
                .iter()
                .map(|record| record.topic.as_str())
                .collect::<Vec<_>>(),
        );
        let dataset = StringArray::from(
            records
                .iter()
                .map(|record| record.dataset.as_str())
                .collect::<Vec<_>>(),
        );
        let payload = StringArray::from(
            records
                .iter()
                .map(|record| record.payload.as_str())
                .collect::<Vec<_>>(),
        );

        RecordBatch::try_new(
            Arc::clone(&self.schema),
            vec![
                Arc::new(event_time) as ArrayRef,
                Arc::new(ingested_at) as ArrayRef,
                Arc::new(topic) as ArrayRef,
                Arc::new(dataset) as ArrayRef,
                Arc::new(payload) as ArrayRef,
            ],
        )
        .map_err(|err| format!("failed to build Parquet record batch: {}", err))
    }
}

fn sanitize_partition_value(value: &str) -> String {
    value
        .chars()
        .map(|ch| match ch {
            'a'..='z' | 'A'..='Z' | '0'..='9' | '-' | '_' => ch,
            _ => '_',
        })
        .collect()
}
