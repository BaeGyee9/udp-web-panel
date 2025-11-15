#!/usr/bin/env python3
"""
ZIVPN Telegram Bot - GitHub Version
Downloaded from: https://github.com/BaeGyee9/udp-web-panel/main/telegram/bot.py
"""

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/etc/zivpn/zivpn.db")
BOT_TOKEN = os.environ.get("8561180756:AAHVoCuaWhZ4kjKMNK7NKutA_YXJr0eoSYs", "")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def format_bytes(size):
    """Format bytes to human readable format"""
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def start(update, context):
    """Send welcome message"""
    welcome_text = """
🤖 *ZIVPN Management Bot*

*Available Commands:*
/start - Show this welcome message
/stats - Server statistics
/users - List all users
/myinfo <username> - Get user information
/help - Show help message

*ဖွင့်သောအမိန့်များ:*
/start - ကြိုဆိုစာကိုပြပါ
/stats - ဆာဗာစာရင်းဇယား
/users - အသုံးပြုသူအားလုံးကိုပြပါ
/myinfo <username> - အသုံးပြုသူအချက်အလက်ရယူရန်
/help - အကူအညီစာကိုပြပါ
    """
    update.message.reply_text(welcome_text, parse_mode='Markdown')

def help_command(update, context):
    """Show help message"""
    help_text = """
*Bot Commands:*

📊 /stats - Show server statistics
👥 /users - List all VPN users
🔍 /myinfo <username> - Get detailed user information
🆘 /help - Show this help message

*အသုံးပြုနည်းများ:*

📊 /stats - ဆာဗာစာရင်းဇယားများကိုကြည့်ရန်
👥 /users - VPN အသုံးပြုသူအားလုံးကိုကြည့်ရန်
🔍 /myinfo <username> - အသုံးပြုသူအသေးစိတ်အချက်အလက်ရယူရန်
🆘 /help - အကူအညီစာကိုကြည့်ရန်
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def stats_command(update, context):
    """Show server statistics"""
    db = get_db()
    try:
        # Get total statistics
        stats = db.execute('''
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN status = "active" AND (expires IS NULL OR expires >= date('now')) THEN 1 ELSE 0 END) as active_users,
                SUM(bandwidth_used) as total_bandwidth
            FROM users
        ''').fetchone()

        # Get today's new users
        today_users = db.execute('''
            SELECT COUNT(*) as today_users 
            FROM users 
            WHERE date(created_at) = date('now')
        ''').fetchone()

        total_users = stats['total_users'] or 0
        active_users = stats['active_users'] or 0
        total_bandwidth = stats['total_bandwidth'] or 0
        today_new_users = today_users['today_users'] or 0

        stats_text = f"""
📊 *Server Statistics*

👥 Total Users: *{total_users}*
🟢 Active Users: *{active_users}*
🆕 Today's New Users: *{today_new_users}*
📦 Total Bandwidth Used: *{format_bytes(total_bandwidth)}*

*ဆာဗာစာရင်းဇယား*

👥 စုစုပေါင်းအသုံးပြုသူ: *{total_users}*
🟢 အွန်လိုင်းအသုံးပြုသူ: *{active_users}*
🆕 ယနေ့အသစ်ထည့်သူ: *{today_new_users}*
📦 စုစုပေါင်း Bandwidth: *{format_bytes(total_bandwidth)}*
        """

        update.message.reply_text(stats_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        update.message.reply_text("❌ Error retrieving statistics")
    finally:
        db.close()

def users_command(update, context):
    """List all users"""
    db = get_db()
    try:
        users = db.execute('''
            SELECT username, status, expires, bandwidth_used, concurrent_conn
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 20
        ''').fetchall()

        if not users:
            update.message.reply_text("📭 No users found")
            return

        users_text = "👥 *Recent Users (Last 20)*\n\n"
        users_text_my = "👥 *နောက်ဆုံးအသုံးပြုသူများ (၂၀ ယောက်)*\n\n"

        for user in users:
            status_icon = "🟢" if user['status'] == 'active' else "🔴"
            bandwidth = format_bytes(user['bandwidth_used'] or 0)
            
            users_text += f"{status_icon} *{user['username']}*\n"
            users_text += f"   Status: {user['status']}\n"
            users_text += f"   Bandwidth: {bandwidth}\n"
            users_text += f"   Connections: {user['concurrent_conn']}\n"
            if user['expires']:
                users_text += f"   Expires: {user['expires']}\n"
            users_text += "\n"

        # Send the message
        update.message.reply_text(users_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error getting users: {e}")
        update.message.reply_text("❌ Error retrieving users list")
    finally:
        db.close()

def myinfo_command(update, context):
    """Get user information"""
    if not context.args:
        update.message.reply_text("Usage: /myinfo <username>\nအသုံးပြုနည်း: /myinfo <username>")
        return

    username = context.args[0]
    db = get_db()
    try:
        user = db.execute('''
            SELECT username, status, expires, bandwidth_used, bandwidth_limit,
                   speed_limit_up, concurrent_conn, created_at
            FROM users WHERE username = ?
        ''', (username,)).fetchone()

        if not user:
            update.message.reply_text(f"❌ User '{username}' not found")
            return

        # Calculate days remaining if expiration date exists
        days_remaining = ""
        if user['expires']:
            try:
                exp_date = datetime.strptime(user['expires'], '%Y-%m-%d')
                today = datetime.now()
                days_left = (exp_date - today).days
                days_remaining = f" ({days_left} days remaining)" if days_left >= 0 else f" (Expired {-days_left} days ago)"
            except:
                days_remaining = ""

        user_text = f"""
🔍 *User Information: {user['username']}*

📊 Status: *{user['status'].upper()}*
⏰ Expires: *{user['expires'] or 'Never'}{days_remaining}*
📦 Bandwidth Used: *{format_bytes(user['bandwidth_used'] or 0)}*
🎯 Bandwidth Limit: *{format_bytes(user['bandwidth_limit'] or 0) if user['bandwidth_limit'] else 'Unlimited'}*
⚡ Speed Limit: *{user['speed_limit_up'] or 0} MB/s*
🔗 Max Connections: *{user['concurrent_conn']}*
📅 Created: *{user['created_at'][:10] if user['created_at'] else 'N/A'}*

*အသုံးပြုသူအချက်အလက်: {user['username']}*

📊 အခြေအနေ: *{user['status'].upper()}*
⏰ သက်တမ်းကုန်: *{user['expires'] or 'မကုန်ပါ'}{days_remaining}*
📦 အသုံးပြုပြီး Bandwidth: *{format_bytes(user['bandwidth_used'] or 0)}*
🎯 Bandwidth ကန့်သတ်ချက်: *{format_bytes(user['bandwidth_limit'] or 0) if user['bandwidth_limit'] else 'မကန့်သတ်ပါ'}*
⚡ မြန်နှုန်းကန့်သတ်ချက်: *{user['speed_limit_up'] or 0} MB/s*
🔗 အများဆုံးချိတ်ဆက်မှု: *{user['concurrent_conn']}*
📅 စတင်သည့်ရက်: *{user['created_at'][:10] if user['created_at'] else 'မသိပါ'}*
        """

        update.message.reply_text(user_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        update.message.reply_text("❌ Error retrieving user information")
    finally:
        db.close()

def error_handler(update, context):
    """Log errors"""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables")
        return

    try:
        # Create updater and dispatcher
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Add command handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("stats", stats_command))
        dp.add_handler(CommandHandler("users", users_command))
        dp.add_handler(CommandHandler("myinfo", myinfo_command))

        # Add error handler
        dp.add_error_handler(error_handler)

        # Start the bot
        logger.info("🤖 ZIVPN Telegram Bot Started Successfully")
        updater.start_polling()
        updater.idle()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
