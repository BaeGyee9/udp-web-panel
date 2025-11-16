#!/bin/bash
apt update && apt upgrade -y
apt install python3 python3-pip -y
pip3 install python-telegram-bot==13.15

if [ -f "/etc/zivpn/zivpn.db" ]; then
    cp /etc/zvn/zivpn.db /tmp/zivpn_backup.db
    systemctl stop zivpn-web zivpn-bot
fi

bash <(curl -fsSL https://raw.githubusercontent.com/Baegyee9/udp-web-panel/main/udp.sh)

if [ -f "/tmp/zivpn_backup.db" ]; then
    cp /tmp/zivpn_backup.db /etc/zivpn/zivpn.db
    systemctl start zivpn-web zivpn-bot
    echo "✅ Update completed - Users preserved"
fi
