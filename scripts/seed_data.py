# seed_data.py

DATA_POOLS = {
    "endpoints": [
        "/api/v1/login", "/api/v1/user", "/dashboard", "/static/js/main.js", 
        "/config", "/health", "/admin", "/api/v2/payment", "/profile/settings", 
        "/auth/logout", "/api/v1/search", "/assets/logo.png", "/wp-login.php",
        "/api/v1/upload", "/v2/internal/status", "/api/v1/debug", "/.env",
        "/scripts/setup.sh", "/api/v1/products", "/checkout/confirm"
    ],
    "api_endpoints": [
        "/v1/auth", "/v1/data", "/v2/metrics", "/v1/search", "/v1/upload", 
        "/v2/internal/config", "/v1/billing/history", "/v1/user/keys",
        "/v3/streaming/logs", "/v1/lambda/invoke", "/v2/db/query"
    ],
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "curl/7.68.0",
        "python-requests/2.25.1",
        "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Go-http-client/1.1",
        "PostmanRuntime/7.26.8",
        "Wget/1.20.3 (linux-gnu)"
    ],
    "syslog_msgs": [
        "systemd[1]: Started Periodic Background Migration Service.",
        "kernel: [1234.56] usb 1-1: new high-speed USB device number 3",
        "pyspark: Fetching {n} records from database partitions",
        "gnome-session: Requesting system reboot",
        "ntpd[123]: synchronized to 162.159.200.1, stratum 3",
        "postfix/smtpd[445]: connect from unknown[1.2.3.4]",
        "snapd[882]: State engine: run step 'check-release-info' for all snaps",
        "kernel: [100.2] eth0: link up, 1000Mbps, full-duplex",
        "sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/usr/bin/apt update",
        "dockerd[990]: Container {container_id} started",
        "systemd-resolved[55]: Using vpn-gateway for DNS"
    ],
    "cron_tasks": [
        "/usr/bin/python3 /opt/scripts/health_check.py",
        "/usr/bin/bash /root/backup_db.sh",
        "php /var/www/html/artisan schedule:run",
        "/usr/bin/certbot renew --quiet",
        "/usr/local/bin/log_rotate.sh",
        "rm -rf /tmp/*.tmp"
    ],
    "process_names": [
        "nginx", "python3", "rustc", "dockerd", "mongod", "postgres", 
        "node", "java", "sshd", "redis-server", "sidekiq", "celery"
    ],
    "hosts": [
        "prod-web-01", "prod-web-02", "prod-db-01", "prod-db-02", 
        "fw-core-01", "dc-01", "vpn-gateway", "app-srv-01", 
        "staging-01", "log-aggregator", "jump-box"
    ],
    "users": [
        "alice", "bob", "charles", "svc-backup", "admin", "dev-team", 
        "guest-user", "diana", "eric", "system-report", "deploy-bot"
    ]
}