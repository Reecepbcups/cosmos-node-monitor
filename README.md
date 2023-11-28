# Node Monitor

A script to monitor the status of your Cosmos server nodes relative to the rest of the network.

Discord notifications if there are errors:
- server is down
- node is down
- node has falled out of sync relative to other public nodes

## Supports
- Multiple personal nodes (good to test DNS & direct IP)
- Multiple references (compare against other public nodes)
- COnfigure allowed block drift / sway (5 blocks default)

## Installation

```bash
pip install -r requirements.txt  --break-system-packages
sudo pip install -r requirements.txt  --break-system-packages
```

## Usage

```bash

# edit with your discord webhook url & servers to monitor & compare against
cp config.example.json config.json

# crontab -e
# Every 15 minutes:
# */15 * * * * python3 /root/cosmos-node-monitor/main.py

```