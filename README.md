# halake-raspi
A library to use projects maintained by nyampass.

# Programs
## gatein-by-felica
It scans felica id for gatein.

References
- [nfcpy](http://nfcpy.readthedocs.io/en/latest/index.html)
- [Raspberry PiでFelicaのIDmを表示する](http://qiita.com/ihgs/items/34eefd8d01c570e92984)

## receipt-print
It controls receipt printer.

References
- [python-escpos](https://python-escpos.readthedocs.io/en/latest/)
- [Commands in Code Order](https://reference.epson-biz.com/modules/ref_escpos/index.php?content_id=72)

# Setup

```sh
sudo sh [halake-raspi-dir]/scripts/install.sh
```

# Run

## All
```sh
cd [halake-raspi-dir]
./scripts/start.sh
```

## Each package
```sh
cd [halake-raspi-dir]
./src/[program-to-run]
```

# Auto run setting
Add a job to crontab.
```sh
sudo crontab -e
```

The job to add.
```
@reboot [halake-raspi-dir]/scripts/start.sh &
```
