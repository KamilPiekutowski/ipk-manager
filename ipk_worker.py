import os
import sys
import subprocess
import time
from datetime import datetime
import signal

LOG_FILE = "/home/kamilp/server-apps/worker.log"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass

def kill_existing():
    log_message("Hunting for any http.server 8001 processes...")
    
    # 1. Use absolute path for pgrep (/usr/bin/pgrep)
    try:
        pid_data = subprocess.check_output(["/usr/bin/pgrep", "-f", "http.server 8001"], stderr=subprocess.DEVNULL)
        pids = pid_data.decode().strip().split('\n')
        
        for pid_str in pids:
            if pid_str:
                pid = int(pid_str)
                log_message(f"Killing process ID: {pid}")
                os.kill(pid, signal.SIGKILL)
    except Exception as e:
        log_message(f"pgrep hunt skipped or failed: {e}")

    # 2. Use absolute path for lsof (/usr/bin/lsof) as a backup
    try:
        pid_data = subprocess.check_output(["/usr/bin/lsof", "-t", "-i:8001"], stderr=subprocess.DEVNULL)
        pids = pid_data.decode().strip().split('\n')
        for pid_str in pids:
            if pid_str:
                os.kill(int(pid_str), signal.SIGKILL)
                log_message(f"lsof found and killed PID: {pid_str}")
    except Exception:
        pass

    # 3. Final backup: fuser (/sbin/fuser)
    subprocess.run("/sbin/fuser -k 8001/tcp", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(1)

def start_ipk(target_path):
    log_message(f"--- START REQUEST: {target_path} ---")
    kill_existing()
    
    if os.path.isdir(target_path):
        try:
            # Use sys.executable to ensure we use the same Python/venv
            cmd = [sys.executable, "-m", "http.server", "8001", "--directory", target_path, "--bind", "0.0.0.0"]
            subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_message(f"Server spawned for: {target_path}")
        except Exception as e:
            log_message(f"Spawn Error: {e}")
    else:
        log_message(f"ERROR: {target_path} is not a valid directory.")

def stop_ipk():
    log_message("--- STOP REQUEST ---")
    kill_existing()
    log_message("Stop complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log_message("ERROR: Worker called without arguments.")
        sys.exit(1)
    
    action_or_path = sys.argv[1]
    
    if action_or_path == "stop":
        stop_ipk()
    else:
        start_ipk(action_or_path)

