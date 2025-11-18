#!/usr/bin/env python3
"""
ZIVPN Telegram Bot - GitHub Version
"""
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
import logging
import os
from datetime import datetime, timedelta
import random
import string
import socket

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/etc/zivpn/zivpn.db")
BOT_TOKEN = "8561180756:AAHVoCuaWhZ4kjKMNK7NKutA_YXJr0eoSYs"

# Admin configuration
ADMIN_IDS = [7240495054]  # ညီ့ Telegram ID

def get_server_ip():
    """Get server IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "43.249.33.233"  # fallback IP

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

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
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    
    welcome_text = """
🤖 *ZIVPN Management Bot*"""
    
    if is_user_admin:
        welcome_text += f"""
*🛠️ Admin Commands:*
/admin - Admin panel
/adduser <user> <pass> [days] - Add user
/deluser <username> - Delete user
/suspend <username> - Suspend user
/activate <username> - Activate user
/ban <username> - Ban user
/unban <username> - Unban user
/renew <username> <days> - Renew user
/users - List all users
/stats - Server statistics
/myinfo <username> - User details
"""
    
    welcome_text += """
*📋 User Commands:*
/start - Show this welcome message  
/stats - Server statistics
/users - List all users
/myinfo <username> - Get user information
/help - Show help message
    """
    update.message.reply_text(welcome_text, parse_mode='Markdown')

def help_command(update, context):
    """Show help message"""
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    
    help_text = """
*Bot Commands:*"""
    
    if is_user_admin:
        help_text += """
🛠️ *Admin:*
/admin - Admin panel
/adduser <user> <pass> [days] - Add user
/deluser <username> - Delete user
/suspend <username> - Suspend user
/activate <username> - Activate user
/ban <username> - Ban user
/unban <username> - Unban user
/renew <username> <days> - Renew user
"""
    
    help_text += """
📊 /stats - Show server statistics
👥 /users - List all VPN users  
🔍 /myinfo <username> - Get detailed user information
🆘 /help - Show this help message
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def admin_command(update, context):
    """Admin panel"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    admin_text = f"""
🛠️ *Admin Panel*
🌐 Server IP: `{get_server_ip()}`

*User Management:*
• /adduser <user> <pass> [days] - Add new user
• /deluser <username> - Delete user
• /suspend <username> - Suspend user  
• /activate <username> - Activate user
• /ban <username> - Ban user
• /unban <username> - Unban user
• /renew <username> <days> - Renew user

*Information:*
• /users - List all users
• /stats - Server statistics
• /myinfo <username> - User details
    """
    update.message.reply_text(admin_text, parse_mode='Markdown')

def adduser_command(update, context):
    """Add new user"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 2:
        update.message.reply_text("Usage: /adduser <username> <password> [days]\nExample: /adduser john pass123 30")
        return
    
    username = context.args[0]
    password = context.args[1]
    days = 30  # default 30 days
    
    if len(context.args) > 2:
        try:
            days = int(context.args[2])
        except:
            update.message.reply_text("❌ Invalid days format")
            return
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    server_ip = get_server_ip()
    
    db = get_db()
    try:
        # Check if user exists
        existing = db.execute('SELECT username FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            update.message.reply_text(f"❌ User `{username}` already exists")
            return
        
        # Add user to database
        db.execute('''
            INSERT INTO users (username, password, status, expires, concurrent_conn, created_at)
            VALUES (?, ?, 'active', ?, 1, datetime('now'))
        ''', (username, password, expiry_date))
        db.commit()
        
        success_text = f"""
✅ *User Added Successfully*

🌐 Server: `{server_ip}`
👤 Username: `{username}`
🔐 Password: `{password}`
📊 Status: Active
⏰ Expires: {expiry_date}
🔗 Connections: 1

*အောင်မြင်စွာထည့်ပြီးပါပြီ*
🌐 ဆာဗာ: `{server_ip}`
👤 အသုံးပြုသူအမည်: `{username}`
🔐 လျှို့ဝှက်နံပါတ်: `{password}`
📊 အခြေအနေ: ဖွင့်ပြီး
⏰ သက်တမ်းကုန်: {expiry_date}
🔗 အများဆုံးချိတ်ဆက်မှု: 1
        """
        update.message.reply_text(success_text, parse_mode='Markdown')
        logger.info(f"User {username} added by admin {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        update.message.reply_text("❌ Error adding user")
    finally:
        db.close()

def deluser_command(update, context):
    """Delete user"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /deluser <username>")
        return
    
    username = context.args[0]
    db = get_db()
    try:
        # Check if user exists
        existing = db.execute('SELECT username FROM users WHERE username = ?', (username,)).fetchone()
        if not existing:
            update.message.reply_text(f"❌ User `{username}` not found")
            return
        
        # Delete user
        db.execute('DELETE FROM users WHERE username = ?', (username,))
        db.commit()
        
        update.message.reply_text(f"✅ User `{username}` deleted\n✅ အသုံးပြုသူ `{username}` ကိုဖျက်ပြီးပါပြီ")
        logger.info(f"User {username} deleted by admin {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        update.message.reply_text("❌ Error deleting user")
    finally:
        db.close()

def suspend_command(update, context):
    """Suspend user (temporary disable)"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /suspend <username>\nအသုံးပြုနည်း: /suspend <username>")
        return
    
    username = context.args[0]
    db = get_db()
    try:
        db.execute('UPDATE users SET status = "suspended" WHERE username = ?', (username,))
        db.commit()
        update.message.reply_text(f"✅ User *{username}* suspended\n✅ အသုံးပြုသူ *{username}* ကိုယာယီပိတ်ထားပါပြီ\n\n🔓 ပြန်ဖွင့်ရန်: /activate {username}")
        logger.info(f"User {username} suspended by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error suspending user: {e}")
        update.message.reply_text("❌ Error suspending user")
    finally:
        db.close()

def activate_command(update, context):
    """Activate suspended user"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /activate <username>\nအသုံးပြုနည်း: /activate <username>")
        return
    
    username = context.args[0]
    db = get_db()
    try:
        db.execute('UPDATE users SET status = "active" WHERE username = ?', (username,))
        db.commit()
        update.message.reply_text(f"✅ User *{username}* activated\n✅ အသုံးပြုသူ *{username}* ကိုပြန်ဖွင့်ပြီးပါပြီ")
        logger.info(f"User {username} activated by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        update.message.reply_text("❌ Error activating user")
    finally:
        db.close()

def ban_user(update, context):
    """Ban user (permanent disable)"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /ban <username>\nအသုံးပြုနည်း: /ban <username>")
        return
    
    username = context.args[0]
    db = get_db()
    try:
        db.execute('UPDATE users SET status = "banned" WHERE username = ?', (username,))
        db.commit()
        update.message.reply_text(f"✅ User *{username}* banned\n✅ အသုံးပြုသူ *{username}* ကိုအပြီးပိတ်ပြီးပါပြီ\n\n🔓 ပြန်ဖွင့်ရန်: /unban {username}")
        logger.info(f"User {username} banned by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        update.message.reply_text("❌ Error banning user")
    finally:
        db.close()

def unban_user(update, context):
    """Unban user"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /unban <username>\nအသုံးပြုနည်း: /unban <username>")
        return
    
    username = context.args[0]
    db = get_db()
    try:
        db.execute('UPDATE users SET status = "active" WHERE username = ?', (username,))
        db.commit()
        update.message.reply_text(f"✅ User *{username}* unbanned\n✅ အသုံးပြုသူ *{username}* ကိုပြန်ဖွင့်ပြီးပါပြီ")
        logger.info(f"User {username} unbanned by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        update.message.reply_text("❌ Error unbanning user")
    finally:
        db.close()

def renew_command(update, context):
    """Renew user subscription"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Admin only command")
        return
    
    if len(context.args) < 2:
        update.message.reply_text("Usage: /renew <username> <days>\nExample: /renew john 30\nအသုံးပြုနည်း: /renew <username> <days>")
        return
    
    username = context.args[0]
    try:
        days = int(context.args[1])
    except:
        update.message.reply_text("❌ Invalid days format")
        return
    
    db = get_db()
    try:
        # Check if user exists
        user = db.execute('SELECT username, expires FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            update.message.reply_text(f"❌ User `{username}` not found")
            return
        
        # Calculate new expiry date
        if user['expires']:
            current_expiry = datetime.strptime(user['expires'], '%Y-%m-%d')
            new_expiry = current_expiry + timedelta(days=days)
        else:
            new_expiry = datetime.now() + timedelta(days=days)
        
        new_expiry_str = new_expiry.strftime('%Y-%m-%d')
        
        # Update expiry date
        db.execute('UPDATE users SET expires = ? WHERE username = ?', (new_expiry_str, username))
        db.commit()
        
        update.message.reply_text(f"✅ User *{username}* renewed for {days} days\n✅ အသုံးပြုသူ *{username}* ကို {days} ရက်သက်တမ်းတိုးပြီးပါပြီ\n\n⏰ New expiry: {new_expiry_str}")
        logger.info(f"User {username} renewed for {days} days by admin {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error renewing user: {e}")
        update.message.reply_text("❌ Error renewing user")
    finally:
        db.close()

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
🔴 Inactive Users: *{total_users - active_users}*
🆕 Today's New Users: *{today_new_users}*
📦 Total Bandwidth Used: *{format_bytes(total_bandwidth)}*

*ဆာဗာစာရင်းဇယား*
👥 စုစုပေါင်းအသုံးပြုသူ: *{total_users}*
🟢 အွန်လိုင်းအသုံးပြုသူ: *{active_users}*
🔴 ပိတ်ထားသူ: *{total_users - active_users}*
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
        
        # Add admin commands
        dp.add_handler(CommandHandler("admin", admin_command))
        dp.add_handler(CommandHandler("adduser", adduser_command))
        dp.add_handler(CommandHandler("deluser", deluser_command))
        dp.add_handler(CommandHandler("suspend", suspend_command))
        dp.add_handler(CommandHandler("activate", activate_command))
        dp.add_handler(CommandHandler("ban", ban_user))
        dp.add_handler(CommandHandler("unban", unban_user))
        dp.add_handler(CommandHandler("renew", renew_command))

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
    
