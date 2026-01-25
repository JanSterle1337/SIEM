import os

BASE_DIR = os.path.join(os.getcwd(), "data", "logs")

LOG_PATHS = {
    "nginx": os.path.join(BASE_DIR, "nginx", "access.log"),
    "auth": os.path.join(BASE_DIR, "auth", "ssh.log"),
    "system": os.path.join(BASE_DIR, "system", "syslog.log"),
    "firewall": os.path.join(BASE_DIR, "firewall", "traffic.log"),
    "apps": os.path.join(BASE_DIR, "apps", "application.log")
}


for path in LOG_PATHS.values():
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")