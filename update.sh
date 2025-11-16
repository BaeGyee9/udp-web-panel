#!/bin/bash

echo "🔄 ZIVPN Smart Updater"
echo "======================"

# Check if ZIVPN is already installed
if [ ! -f "/etc/zivpn/zivpn.db" ]; then
    echo "🚀 First-time installation detected..."
    bash <(curl -fsSL https://raw.githubusercontent.com/Baegyee9/udp-web-panel/main/udp.sh)
    exit 0
fi

echo "📦 Existing installation detected - preserving users..."

# 1. Stop services
systemctl stop zivpn-web zivpn-bot 2>/dev/null

# 2. Backup current database and configs
BACKUP_DIR="/tmp/zivpn_update_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

if [ -f "/etc/zivpn/zivpn.db" ]; then
    cp /etc/zivpn/zivpn.db $BACKUP_DIR/
    echo "✅ Database backed up: $BACKUP_DIR/zivpn.db"
fi

cp /etc/zivpn/*.py $BACKUP_DIR/ 2>/dev/null
cp /etc/zivpn/*.json $BACKUP_DIR/ 2>/dev/null

# 3. Run the main installation script
echo "📥 Downloading and installing updates..."
bash <(curl -fsSL https://raw.githubusercontent.com/Baegyee9/udp-web-panel/main/udp.sh)

# 4. Restore user database
if [ -f "$BACKUP_DIR/zivpn.db" ]; then
    cp $BACKUP_DIR/zivpn.db /etc/zivpn/
    chown root:root /etc/zivpn/zivpn.db
    chmod 644 /etc/zivpn/zivpn.db
    echo "✅ User database restored"
fi

# 5. Merge config files (preserve custom settings)
for file in $BACKUP_DIR/*.py $BACKUP_DIR/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        # Only restore if file doesn't exist in new installation
        if [ ! -f "/etc/zivpn/$filename" ]; then
            cp "$file" "/etc/zivpn/$filename"
            echo "✅ Restored: $filename"
        fi
    fi
done

# 6. Restart services
systemctl start zivpn-web zivpn-bot 2>/dev/null

# 7. Cleanup
rm -rf $BACKUP_DIR

echo ""
echo "✅ Update completed successfully!"
echo "📊 User accounts: Preserved"
echo "🆕 Features: Updated" 
echo "🌐 Panel: Ready"
echo ""
echo "Check panel: http://$(curl -4 -s ifconfig.me):8080"
