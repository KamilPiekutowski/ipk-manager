import os
import sys
import subprocess
from flask import Flask, render_template, request
import time

app = Flask(__name__)
SAFE_ROOT = "/home/kamilp/server-apps/ipk-dirs"
STATE_FILE = "/home/kamilp/server-apps/serving.txt"

# Track the background process
ipk_process = None


def start_ipk_server(path):
    target = os.path.abspath(path)
    if os.path.isdir(target):
        # Call the worker script and let it detach
        worker_script = "/home/kamilp/server-apps/ipk_worker.py"
        subprocess.Popen([sys.executable, worker_script, target])

        with open(STATE_FILE, "w") as f:
            f.write(target)
        return True
    return False

# --- BOOT-UP PERSISTENCE ---
# This runs once when the systemd service starts the app
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            saved_path = f.read().strip()
            if saved_path and os.path.isdir(saved_path):
                start_ipk_server(saved_path)
                print(f"Boot: Resumed IPK server for {saved_path}")
    except Exception as e:
        print(f"Boot Error: {e}")

@app.route('/select', methods=['POST'])
def select_folder():
    target_path = request.form.get('path')
    if start_ipk_server(target_path):
        return "OK", 200
    return "Path Error", 400

@app.route('/stop', methods=['POST'])
def stop_serving():
    worker_script = "/home/kamilp/server-apps/ipk_worker.py"
    # Call the worker with the 'stop' argument
    subprocess.Popen([sys.executable, worker_script, "stop"])

    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return "Stopped", 200

@app.route('/')
def index():
    # 1. Get the subpath from the URL (e.g. ?path=project1)
    # If no path is provided, it defaults to an empty string (the root)
    requested_subpath = request.args.get('path', '')

    # 2. Safety: Join the root with the subpath and resolve it
    # This automatically ignores any "../../" attempts to escape
    full_path = os.path.abspath(os.path.join(SAFE_ROOT, requested_subpath.lstrip('/')))

    # 3. Security: If the resolved path doesn't start with SAFE_ROOT, force it back
    if not full_path.startswith(SAFE_ROOT):
        full_path = SAFE_ROOT

    # 4. Calculate a 'relative' path for the links in the HTML
    # This keeps the URLs clean (e.g. ?path=folder1 instead of the full system path)
    rel_path = os.path.relpath(full_path, SAFE_ROOT)
    if rel_path == ".":
        rel_path = ""

    try:
        items = os.listdir(full_path)
        folders = [f for f in items if os.path.isdir(os.path.join(full_path, f))]
    except Exception:
        folders = []

    # Only allow "Go Up" if we aren't already at the SAFE_ROOT
    can_go_up = full_path != SAFE_ROOT

    return render_template('index.html', 
                           folders=folders, 
                           current_path=full_path, 
                           rel_path=rel_path,
                           can_go_up=can_go_up)
