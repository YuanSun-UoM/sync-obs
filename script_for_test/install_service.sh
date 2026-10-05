#!/bin/bash

sudo tee /etc/systemd/system/sync_obs.service > /dev/null <<'EOF'
[Unit]
Description=sync_obs Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=yuansun
WorkingDirectory=/home/yuansun/src/sync-obs
ExecStart=/usr/bin/python3 /home/yuansun/src/sync-obs/sync.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/sync_obs.service
sudo systemctl daemon-reload
sudo systemctl enable sync_obs.service
sudo systemctl restart sync_obs.service