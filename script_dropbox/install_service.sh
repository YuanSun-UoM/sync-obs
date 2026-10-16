#!/bin/bash
set -e

sudo tee /etc/systemd/system/sync_obs_dropbox.service > /dev/null <<'EOF'
[Unit]
Description=Ceilometer Dropbox Synchronization Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=yuansun
WorkingDirectory=/home/yuansun/src/sync-obs/sync-obs_dropbox
ExecStart=/usr/bin/python3 /home/yuansun/src/sync-obs/sync-obs_dropbox/sync_dropbox.py --config_file /home/yuansun/src/sync-obs/sync-obs_dropbox/sync_config_dropbox.json
Environment=PYTHONUNBUFFERED=1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/sync_obs_dropbox.service
sudo systemctl daemon-reload
sudo systemctl enable sync_obs_dropbox.service
sudo systemctl restart sync_obs_dropbox.service
