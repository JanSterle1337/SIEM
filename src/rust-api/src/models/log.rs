use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OcsfLog {
    pub category_uid: u16,
    pub class_uid: u16,
    pub time: i64,
    pub disposition_id: u8,
    pub message: String,
    pub src_endpoint: Option<Endpoint>,
    pub metadata: Metadata
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Endpoint {
    pub ip: String
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Metadata {
    pub product: Product
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Product {
    pub name: String
}