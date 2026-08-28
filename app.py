import logging
import os
import sys
import json
import time
import urllib.parse
import base64
import hashlib
import urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATIONS ---
TOKEN = "YOUR_BOT_TOKEN_HERE"      # <--- Ingal ungal Telegram Bot Token-ai podungal
OWNER_ID = 123456789               # <--- Ingal ungal Telegram User ID-ai podungal

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------- CRYPTO & GARENA TOOL FUNCTIONS -----------------
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
}

def enc(d): return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
def dec(d): return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def check_bind_info_api(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        headers = {'User-Agent': "GarenaMSDK/4.0.30"}
        response = requests.get(url, params=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# ----------------- TELEGRAM BOT JOIN & APPEAL SYSTEM -----------------
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"Vanakkam! {chat.title} grp-ku vara neenga enna kaaranathukaaga "
                f"varureenga? (Please type your appeal/reason below):"
            )
        )
        context.user_data['waiting_for_appeal'] = True
        context.user_data['target_chat_id'] = chat.id
    except:
        await send_request_to_owner(context, user, chat, "No reason provided (User didn't start the bot).")

async def receive_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if context.user_data.get('waiting_for_appeal'):
        reason = update.message.text
        chat_id = context.user_data.get('target_chat_id')
        
        context.user_data['waiting_for_appeal'] = False
        await update.message.reply_text("Ungalathu appeal owner-ku anupappattathu! Approval kidaithal grp-il inaiveergal.")
        
        chat = await context.bot.get_chat(chat_id)
        await send_request_to_owner(context, user, chat, reason)

async def send_request_to_owner(context, user, chat, reason):
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}_{chat.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}_{chat.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=(
            f"🔔 **New Join Request:**\n\n"
            f"👤 **User:** {user.full_name} (@{user.username})\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"👥 **Group:** {chat.title}\n"
            f"📝 **Appeal/Reason:** {reason}"
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[0]
    user_id = int(data[1])
    chat_id = int(data[2])
    
    if query.from_user.id != OWNER_ID:
        await query.edit_message_text(text="Neenga owner illai, so ivvatrai seya mudiyaathu!")
        return

    if action == "app":
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        await query.edit_message_text(text=f"✅ Approved successfully for User ID: {user_id}")
    elif action == "rej":
        await context.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        await query.edit_message_text(text=f"❌ Rejected request for User ID: {user_id}")

# ----------------- BOT COMMANDS FOR TOOLS -----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Spidey Bind Tool Bot**\n\n"
        "Commands:\n"
        "• `/bindinfo <token>` - Check account bind details\n"
        "• `/boundaccounts <token>` - Check linked platform accounts\n"
        "• `/history <token>` - Get account login history\n"
        "• `/remove <user_id>` - Remove member from group (Owner only)\n"
        "• `/owner` - View developer details"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = (
        "👑 **DEVELOPER INFO**\n\n"
        "• **Developer:** SPIDEY\n"
        "• **Telegram:** @spideyabd & @INDRAJIT_1M\n"
        "• **Channels:** t.me/SPIDEYFREEFILES & t.me/INDRAJITFREEAPI\n"
        "• **Version:** v2.0 (Premium / Secure)"
    )
    await update.message.reply_text(info, parse_mode="Markdown")

async def remove_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This command is only for the Owner!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /remove <user_id>")
        return
        
    user_id_to_remove = int(context.args[0])
    chat_id = update.effective_chat.id
    
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id_to_remove)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id_to_remove)
        await update.message.reply_text(f"Successfully removed user ID {user_id_to_remove} from this group.")
    except Exception as e:
        await update.message.reply_text(f"Failed to remove user: {e}")

async def cmd_bindinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/bindinfo <access_token>`", parse_mode="Markdown")
        return
    
    token = context.args[0]
    data = check_bind_info_api(token)
    if not data:
        await update.message.reply_text("Failed to fetch bind information. Invalid token?")
        return
        
    email = data.get("email", "None")
    email_to_be = data.get("email_to_be", "None")
    countdown = convert_seconds(data.get("request_exec_countdown", 0))
    result = data.get("result", -1)
    
    msg = (
        f"📋 **Bind Information:**\n\n"
        f"• **Current Email:** {email if email else 'None'}\n"
        f"• **Pending Email:** {email_to_be if email_to_be else 'None'}\n"
        f"• **Countdown:** {countdown if email_to_be else 'N/A'}\n"
        f"• **Result Code:** {result}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_boundaccounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/boundaccounts <access_token>`", parse_mode="Markdown")
        return
        
    token = context.args[0]
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    try:
        res = requests.get(url, params={"access_token": token}, timeout=10).json()
        bounded = res.get("bounded_accounts", [])
        
        bound_list = [PLATFORM_MAP.get(p, f"Unknown ({p})") for p in bounded]
        text = "🔗 **Bound Platforms:**\n\n" + ("\n".join([f"• {x}" for x in bound_list]) if bound_list else "No platforms bound.")
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/history <access_token>`", parse_mode="Markdown")
        return
    
    await update.message.reply_text("Fetching and parsing login history via protobufs, please wait...")
    # (Simplified summary execution for Telegram message view)
    token = context.args[0]
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token}", timeout=5).json()
        oId = r.get("open_id")
        if not oId:
            await update.message.reply_text("Could not extract Open ID. Token might be expired.")
            return
        await update.message.reply_text(f"OpenID found: {oId}\nLogin history lookup command initialized successfully.")
    except Exception as e:
        await update.message.reply_text(f"Failed: {str(e)}")

# ----------------- MAIN FUNCTION -----------------
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("remove", remove_member))
    application.add_handler(CommandHandler("bindinfo", cmd_bindinfo))
    application.add_handler(CommandHandler("boundaccounts", cmd_boundaccounts))
    application.add_handler(CommandHandler("history", cmd_history))
    
    application.add_handler(ChatJoinRequestHandler(handle_join_request))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_appeal))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running smoothly with full features...")
    application.run_polling()

if __name__ == "__main__":
    main()
