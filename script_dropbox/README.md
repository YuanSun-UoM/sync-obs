# DEADME
Due to NUS internet firewall, cloud storage is an alternative approach.

## Install Dropbox on Raspberry Pi
- install rclone
  ```
  sudo apt update
  sudo apt install rclone
  ```
- configuration
  ```
  rclone config
  ```
  Follow the interactive prompts:
1. Select n to create a new remote.
2. Enter dropbox as the remote name.
3. Select Dropbox as the storage type.
4. Follow the browser authentication instructions to authorize your Dropbox account.
5. Save the configuration.
In case of:
```
Option client_id.
OAuth Client Id.
Leave blank normally.
Enter a value. Press Enter to leave empty.
client_id>
```
and
```
client_secret>
```
press Enter. 

In case of:
```
Edit advanced config?
y) Yes
n) No (default)
y/n> n
```
select No.

## Test rclone
- Check
  ```
  which rclone
  ```
- Test
```
echo "Hello from Raspberry Pi" > test.txt
rclone copy test.txt dropbox:
```
then check:
```
rclone ls dropbox:
```
Check the Dropbox remote:
```
rclone about dropbox:
```
## Sync script
- `sync_dropbox.py`
- `sync_config_dropbox.json`
- `install_service.sh`
To test the Python script:
```
python3 sync_dropbox.py \
  --config_file sync_config_dropbox.json \
  --once
```
To validate JSON:
```
python3 -m json.tool sync_config_dropbox.json
```

## Run the service `sync_obs_dropbox`
- Install the service
  ```
  chmod +x install_service.sh
  ./install_service.sh
  ```
  
- Check whether the old service is currently runing (optional):
  ```
  sudo systemctl status sync_obs.service
  ```
  and/or
  ```
  sudo systemctl status sync_obs_dropbox.service
  ```
- Stop old service:
  ```
  sudo systemctl stop sync_obs.service
  ```
  and/or
  ```
  sudo systemctl stop sync_obs_dropbox.service
  ```
- Prevent old service from automatically starting after reboot:
  ```
  sudo systemctl disable sync_obs.service
  ```
  and/or
  ```
  sudo systemctl disable sync_obs_dropbox.service
  ```
- Check recent logs
  ```
  journalctl -u sync_obs_dropbox.service -n 30 --no-pager
  ```
  or
  ```
  journalctl -u sync_obs_dropbox.service -f
  ```
- Check the service status
  ```
  sudo systemctl status sync_obs_dropbox.service
  
  ```
