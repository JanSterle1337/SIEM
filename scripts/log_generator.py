import time
import random
from datetime import datetime

LOG_FILE = "raw_ingest.log"

def generate_nginx_log(status_code="200", path="/index.html", ip="192.168.1.10"):
    timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{timestamp}] "GET {path} HTTP/1.1" {status_code} 512 "-" "Mozilla/5.0"\n'


def generate_auth_log(success=True, user="admin", ip="192.168.1.50"):
    timestamp = datetime.now().strftime("%b %d %H:%M:%S")
    msg = "Accepted password" if success else "Failed password"
    return f'{timestamp} my-linux-server sshd[1234]: {msg} for {user} from {ip} port 55432 ssh2\n'


print(f"Starting log generation to {LOG_FILE}...")


with open(LOG_FILE, "a") as f:
    # 1. Simulate Normal Traffic
    for _ in range(5):
        f.write(generate_nginx_log())
        f.write(generate_auth_log(success=True, user="employee1"))
        time.sleep(0.5)

    # 2. TRIGGER: Brute Force Attack (5 failed logins)
    attacker_ip = "10.0.0.99"
    for _ in range(5):
        f.write(generate_auth_log(success=False, user="root", ip=attacker_ip))
        f.write(generate_nginx_log(status_code="401", path="/admin", ip=attacker_ip))
        f.close(); f = open(LOG_FILE, "a") # Flush to file
        time.sleep(0.1)

    # 3. TRIGGER: Web Scan (Path Traversal attempt)
    f.write(generate_nginx_log(status_code="404", path="/../../etc/passwd", ip=attacker_ip))


print("Scenario logs generated successfully.")
