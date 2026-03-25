# IPK Manager Dashboard for Yocto.
<img width="60%" alt="Screenshot 2026-03-25 012533" src="https://github.com/user-attachments/assets/00a592b4-c212-4953-87cf-02f5f44999c0" />

A dynamic repository management tool for serving Yocto-generated IPK packages, enabling seamless transitions between project-specific build directories across a local subn

### 🏗 Architecture
This application uses a **Dual-Service Architecture** to ensure the control panel stays responsive while the file server remains independent.

*   **Port 8000 (Flask/Gunicorn):** The Control Panel. Used to browse directories and select which folder to serve.
*   **Port 8001 (Python HTTP):** The IPK Server. Dynamically spawned to serve the selected directory.
*   **Worker Pattern:** A dedicated `ipk_worker.py` handles the "Kill-and-Restart" logic to ensure port 8001 is always cleared before a new server starts.
*   **Persistence:** State is saved to `serving.txt`, allowing the server to resume the last served folder automatically after a power cycle or reboot.

### 📂 Project Structure
```text
.
├── app.py              # Flask Web Server (Control UI)
├── ipk_worker.py       # Bulletproof Process Manager (The "Killer")
├── ipk-dirs/           # Root directory for your IPK folders
├── serving.txt         # Stores the currently active path (Persistence)
├── worker.log          # Action logs for process kills/spawns
├── static/             # Local Bootstrap CSS (Offline-ready)
├── templates/          # Jinja2 HTML templates (Dark Mode UI)
└── venv/               # Python Virtual Environment
```

🚀 Installation & Setup
1. Prerequisites
Ensure your Ubuntu system has the necessary tools:
```bash
sudo apt update
sudo apt install -y python3-venv psmisc lsof
```

2. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install flask gunicorn
Use code with caution.
```
3. Systemd Service Configuration
To make the app start on boot, create the service file:
```bash
sudo vim /etc/systemd/system/flaskapp.service
```
Paste the following (Replace 'kamilp' with your username):
```ini
[Unit]
Description=Gunicorn instance to serve IPK Manager
After=network.target

[Service]
User=kamilp
Group=www-data
WorkingDirectory=/home/kamilp/server-apps
Environment="PATH=/home/kamilp/server-apps/venv/bin"
ExecStart=/home/kamilp/server-apps/venv/bin/gunicorn --workers 1 --bind 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

4. Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable flaskapp
sudo systemctl start flaskapp
```
5. Adding and ipk-folders:
```bash
mkdir ipk-dirs/your-ipk-directory
```
Edit your Yocto **vim conf/local.conf** to ensure you build puts ipks into that folder.
Using absolute paths is recommended.
```local.conf
DEPLOY_DIR_IPK = "~/server-apps/ipk-dirs/var-som-wifi"
```
🛠 Management Commands
* **Check UI Status:** sudo systemctl status flaskapp
* **View Web Logs:** journalctl -u flaskapp -f
* **View Worker Logs:** tail -f worker.log
* **Verify Active IPK Server:** ps aux | grep http.server
🛡 Security Features
* **Absolute Pathing:** All internal commands use absolute paths to avoid environment mismatches.
* **Jail Logic:** Users are locked into the ipk-dirs folder and cannot navigate up into the system root.
* **Force Kill:** The worker uses SIGKILL on PIDs found via pgrep and fuser to prevent "Address already in use" errors.
