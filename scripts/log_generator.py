import time
import random
import uuid
from datetime import datetime


LOG_FILE = "../data/raw_ingest.log"

class EnterpriseLogGenerator:
    def __init__(self):
        self.hosts = ["prod-web-01", "prod-db-01", "fw-core-01", "dc-01", "vpn-gateway"]
        self.users = ["alice", "bob", "charles", "svc-backup", "admin"]
        self.internal_ips = [f"10.50.1.{i}" for i in range(10, 250)]
        self.paths = ["/api/v1/login", "/dashboard", "/static/js/main.js", "/config", "/health"]

    def write(self, log):
        with open(LOG_FILE, "a") as f:
            f.write(log + "\n")
    

    def gen_nginx(self, ip=None, status=None, path=None):
        ip = ip or random.choice(self.internal_ips)
        status = status or random.choices(["200", "404", "500", "302"], weights=[80, 10, 5, 5])[0]
        path= path or random.choice(self.paths)
        ts = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
        return f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {random.randint(124, 5000)} "-" "Mozilla/5.0"'
    
    def gen_firewall(self, action=None):
        action = action or random.choices(["ALLOW", "DENY"], weights=[90, 10])[0]
        src = random.choice(self.internal_ips)
        dst = "8.8.8.8" if action == "ALLOW" else f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        port = random.choice([80, 443, 22, 3306, 5432])
        ts = datetime.now().isoformat()
        return f'{ts} fw-core-01 filter: {action} TCP {src}:34522 -> {dst}:{port} (policy: Default_Drop)'
    
    def gen_syslog(self, host=None):
            host = host or random.choice(self.hosts)
            ts = datetime.now().strftime("%b %d %H:%M:%S")
            msg = random.choice([
                "systemd[1]: Started Periodic Background Migration Service.",
                "kernel: [1234.56] usb 1-1: new high-speed USB device number 3",
                "cron[451]: (root) CMD ( /usr/bin/python3 /opt/scripts/health_check.py )",
                "pyspark: Fetching 512 records from database partitions"
            ])
            return f'{ts} {host} {msg}'
    
    def gen_docker(self):
        container = f"app-container-{uuid.uuid4().hex[:6]}"
        ts = datetime.now().isoformat()
        return f'{ts} dockerd[990]: Container {container} changed state to RUNNING'
    

    # --- Scenarios ---
    def normal_traffic(self):
        """Simulate a busy workday"""
        types = [self.gen_nginx, self.gen_firewall, self.gen_syslog, self.gen_docker]
        log = random.choice(types)()
        self.write(log)
    
    def attack_pattern_bruteforce(self, attacker_ip="45.33.22.11"):
        """Simulate an external IP hammering SSH"""
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        target_user = random.choice(["root", "admin", "postgres"])
        log = f'{ts} prod-db-01 sshd[99]: Failed password for {target_user} from {attacker_ip} port 49122 ssh2'
        self.write(log)


    def attack_pattern_exfiltration(self, internal_host="prod-db-01"):
        """Simulate a host talking to a suspicious destination"""
        ts = datetime.now().isoformat()
        log = f'{ts} fw-core-01 filter: ALLOW TCP 10.50.1.55:5432 -> 203.0.113.5:443 (Size: 5.2GB)'
        self.write(log)


if __name__ == "__main__":
    gen = EnterpriseLogGenerator()
    print("🚀 Enterprise Log Simulator started. Press Ctrl+C to stop.")

    attacker_ip = "185.220.101.5"

    try:
        while True:
            for _ in range(random.randint(10, 20)):
                gen.normal_traffic()
                time.sleep(random.uniform(0.1, 0.5))

            if random.random() > 0.7:
                print(f"🔥 Injecting Attack Traffic from {attacker_ip}...")
                gen.attack_pattern_bruteforce(attacker_ip)
    except KeyboardInterrupt:
        print("Simulation stopped")