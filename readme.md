# halake-raspi
A library to use projects maintained by nyampass.

# Setup

```sh
sudo sh [halake-raspi]/scripts/install.sh
```

# Run

```sh
python [halake-raspi]/src/gate_in_with_felica_id.py
```

# Auto run setting

Add a job to crontab.
```sh
sudo crontab -e
```

The job to add.
```
@reboot python /home/[your-user-name]/gitprojects/halake-raspi/src/gate_in_with_felica_id.py &
```
