import time
import random
import uuid
from datetime import datetime
import os
from seed_data import DATA_POOLS
BASE_DIR = os.path.join(os.getcwd(), "data", "logs")

class EnterpriseLogGenerator:
    def __init__(self):
        self.hosts = DATA_POOLS["hosts"]
        self.users = DATA_POOLS["users"]
        self.internal_ips = [f"10.50.1.{i}" for i in range(10, 250)]
        
        self.destinations = {
            "http": os.path.join(BASE_DIR, "nginx", "access.log"),
            "auth": os.path.join(BASE_DIR, "auth", "secure.log"),
            "network": os.path.join(BASE_DIR, "firewall", "trace.log"),
            "system": os.path.join(BASE_DIR, "system", "syslog.log"),
            "api": os.path.join(BASE_DIR, "apps", "api.log"),
        }

    def write(self, category, log):
        target_file = self.destinations.get(category)
        with open(target_file, "a") as f:
            f.write(log + "\n")

    # --- ENHANCED GENERATORS ---

    # FIXED: Added ip, status, and path arguments back in
    def gen_4002_http(self, ip=None, status=None, path=None):
        ip = ip or random.choice(self.internal_ips)
        status = status or random.choices(["200", "404", "500", "302", "401"], weights=[75, 10, 5, 5, 5])[0]
        path = path or random.choice(DATA_POOLS["endpoints"])
        agent = random.choice(DATA_POOLS["user_agents"])
        size = random.randint(100, 15000)
        ts = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
        log = f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {size} "-" "{agent}"'
        self.write("http", log)

    def gen_4001_network(self):
        action = random.choices(["ALLOW", "DENY"], weights=[85, 15])[0]
        src = random.choice(self.internal_ips)
        dst = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        port = random.choice([80, 443, 22, 3306, 5432, 8080, 27017])
        ts = datetime.now().isoformat()
        log = f'{ts} fw-core-01 filter: {action} TCP {src}:{random.randint(30000, 65000)} -> {dst}:{port} (policy: Default_Drop)'
        self.write("network", log)

    def gen_3002_auth(self, success=True, user=None, ip=None):
        user = user or random.choice(self.users)
        ip = ip or random.choice(self.internal_ips)
        host = random.choice(self.hosts)
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        msg = "Accepted password" if success else "Failed password"
        pid = random.randint(100, 9999)
        log = f'{ts} {host} sshd[{pid}]: {msg} for {user} from {ip} port {random.randint(1024, 65535)} ssh2'
        self.write("auth", log)

    def gen_3001_account_change(self):
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        user = random.choice(self.users)
        actions = [f"useradd[{random.randint(100, 999)}]: new user added - name={user}_{random.randint(1, 100)}", 
                   f"passwd[{random.randint(100, 999)}]: password changed for {user}"]
        self.write("auth", f'{ts} dc-01 {random.choice(actions)}')

    def gen_1006_scheduled_job(self):
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        host = random.choice(self.hosts)
        task = random.choice(DATA_POOLS["cron_tasks"])
        log = f'{ts} {host} cron[{random.randint(100, 999)}]: (root) CMD ( {task} )'
        self.write("system", log)

    def gen_1007_process_activity(self):
            ts = datetime.now().strftime("%b %d %H:%M:%S")
            host = random.choice(self.hosts)
            # Dynamic injection into the messages
            raw_msg = random.choice(DATA_POOLS["syslog_msgs"])
            msg = raw_msg.format(
                n=random.randint(1, 4096), 
                user=random.choice(self.users),
                container_id=uuid.uuid4().hex[:12]
            )
            log = f'{ts} {host} {msg}'
            self.write("system", log)

    def gen_6003_api(self):
        ts = datetime.now().isoformat()
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        endpoint = random.choice(DATA_POOLS["api_endpoints"])
        status = random.choices([200, 201, 400, 403, 503], weights=[80, 10, 5, 3, 2])[0]
        lat = random.randint(5, 500)
        log = f'{ts} api-srv: method={method} endpoint={endpoint} status={status} latency={lat}ms'
        self.write("api", log)

    def normal_traffic(self):
        funcs = [self.gen_4002_http, self.gen_4001_network, self.gen_1006_scheduled_job, 
                 self.gen_1007_process_activity, self.gen_6003_api, self.gen_3002_auth]
        random.choice(funcs)()

    def attack_pattern_bruteforce(self, attacker_ip="185.220.101.5"):
        print(f"🔥 Injecting Brute Force from {attacker_ip}...")
        for _ in range(random.randint(5, 10)):
            self.gen_3002_auth(success=False, user=random.choice(["root", "admin", "postgres"]), ip=attacker_ip)
            self.gen_4002_http(ip=attacker_ip, status="401", path="/admin")
            time.sleep(random.uniform(0.01, 0.1))

if __name__ == "__main__":
    gen = EnterpriseLogGenerator()
    print(f"🚀 High-Variation Multi-File Simulator started.")
    try:
        while True:
            for _ in range(random.randint(10, 30)):
                gen.normal_traffic()
                if random.random() > 0.98: gen.gen_3001_account_change()
                time.sleep(random.uniform(0.05, 0.2))

            if random.random() > 0.85:
                gen.attack_pattern_bruteforce()
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped.")