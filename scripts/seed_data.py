# seed_data.py

DATA_POOLS = {
    "endpoints": [
        "/api/v1/login", "/api/v1/user", "/dashboard", "/static/js/main.js", 
        "/config", "/health", "/admin", "/api/v2/payment", "/profile/settings", 
        "/auth/logout", "/api/v1/search", "/assets/logo.png", "/wp-login.php",
        "/api/v1/upload", "/v2/internal/status", "/api/v1/debug", "/.env",
        "/scripts/setup.sh", "/api/v1/products", "/checkout/confirm",
        "/favicon.ico", "/robots.txt", "/sitemap.xml", "/api/v1/inventory",
        "/v1/billing/portal", "/assets/js/vendor/jquery.min.js", "/api/v1/report/download",
        "/phpmyadmin/index.php", "/.git/config", "/.aws/credentials", "/.ssh/id_rsa",
        "/cgi-bin/test-cgi", "/server-status", "/api/v1/internal/debug_vars"
    ],
    "api_endpoints": [
        "/v1/auth", "/v1/data", "/v2/metrics", "/v1/search", "/v1/upload", 
        "/v2/internal/config", "/v1/billing/history", "/v1/user/keys",
        "/v3/streaming/logs", "/v1/lambda/invoke", "/v2/db/query",
        "/v1/customer/profile", "/v2/analytics/event", "/v1/payment/stripe/webhook",
        "/v2/cache/flush", "/v1/k8s/proxy", "/v1/vault/secret", "/v3/inventory/update"
    ],
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "curl/7.68.0",
        "python-requests/2.25.1",
        "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Go-http-client/1.1",
        "PostmanRuntime/7.26.8",
        "Wget/1.20.3 (linux-gnu)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        "Amazon CloudFront",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Zgrab/0.x (Scanning for research)",
        "Nmap Scripting Engine",
        "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)"
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
        "systemd-resolved[55]: Using vpn-gateway for DNS",
        "sshd[{n}]: Received disconnect from 192.168.1.50: 11: Bye Bye [preauth]",
        "postgres[45]: [2-1] LOG: checkpoint starting: time",
        "mongod[202]: [conn12] context: {user} authenticated successfully",
        "kernel: [7721.05] Out of memory: Kill process {n} (java) score 800 or sacrifice child",
        "ufw: [UFW BLOCK] IN=eth0 OUT= MAC=... SRC=45.33.2.11 DST=10.50.1.5",
        "libvirtd[12]: Starting guest VM: prod-worker-node-{n}"
    ],
    "cron_tasks": [
        "/usr/bin/python3 /opt/scripts/health_check.py",
        "/usr/bin/bash /root/backup_db.sh",
        "php /var/www/html/artisan schedule:run",
        "/usr/bin/certbot renew --quiet",
        "/usr/local/bin/log_rotate.sh",
        "rm -rf /tmp/*.tmp",
        "/usr/bin/updatedb",
        "/usr/local/bin/clamav-scan.sh",
        "rsync -avz /var/www/html/ backup-srv:/mnt/backups/",
        "curl -s http://internal-telemetry.local/heartbeat"
    ],
    "process_names": [
        "nginx", "python3", "rustc", "dockerd", "mongod", "postgres", 
        "node", "java", "sshd", "redis-server", "sidekiq", "celery",
        "kubelet", "containerd", "aws-cli", "systemd", "rsyslogd", "splunkd"
    ],
    "hosts": [
        "prod-web-01", "prod-web-02", "prod-db-01", "prod-db-02", 
        "fw-core-01", "dc-01", "vpn-gateway", "app-srv-01", 
        "staging-01", "log-aggregator", "jump-box", "mail-01", 
        "k8s-master", "k8s-worker-01", "k8s-worker-02", "nas-backup"
    ],
    "users": [
        "alice", "bob", "charles", "svc-backup", "admin", "dev-team", 
        "guest-user", "diana", "eric", "system-report", "deploy-bot",
        "postgres", "www-data", "root", "ubuntu", "ansible-worker"
    ],
    "subnets": [
        "10.50.1",   # Servers
        "10.50.2",   # Database Tier
        "192.168.1", # Internal Management
        "172.16.0"   # VPN Users
    ]
}