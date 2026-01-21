pub struct Config {
    pub quickwit_url: String,
    pub kafka_brokers: String,
    pub server_port: u16
}

impl Config {
    pub fn from_env() -> Self {

        dotenvy::dotenv().ok();

        Self {
            quickwit_url: std::env::var("QUICKWIT_URL")
                .unwrap_or_else(|_| "http://localhost:7280".to_string()),
            kafka_brokers: std::env::var("KAFKA_BROKERS")
                .unwrap_or_else(|_| "localhost:19092".to_string()),
            server_port: std::env::var("SERVER_PORT")
                .unwrap_or_else(|_| "3000".to_string())
                .parse()
                .expect("SERVER_PORT must be a number"),
        }
    }
}