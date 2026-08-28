#!/usr/bin/env python3
"""
Garena Account Management Telegram Bot
Original: SenkuCodex (Modified by SOURAV / ALPHA)
TG Bot conversion: auto-generated
"""

import json
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ── Bot token ──────────────────────────────────────────────────────────────────
BOT_TOKEN = "8831298751:AAEQJXRLalC5SHnkBwM6dwDpv2y_yggnbbo"  # Set a NEW token from @BotFather

# ── PRIVATE BOT + OWNER APPROVAL CONFIG ─────────────────────────────────────
# Edit ONLY these values.
# The bot will work ONLY in private chat after the owner approves the user.

OWNER_USER_ID = 7612364424, 8334738134
OWNER_USERNAME = "@mithuntsk"
OWNER_NAME = "MITHUN"

# Optional: set a separate owner contact username shown to users.
# Approval is controlled by OWNER_USER_ID, not by username text.

APPROVED_USERS = set()

def is_owner(update: Update) -> bool:
    user = update.effective_user
    return user is not None and user.id == OWNER_USER_ID

def is_private_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type == "private"

def is_approved(update: Update) -> bool:
    user = update.effective_user
    return user is not None and user.id in APPROVED_USERS

async def private_access_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # Absolutely reject groups/channels.
    if not is_private_chat(update):
        if update.effective_message:
            await update.effective_message.reply_text(
                "⛔ This bot works in private chat only."
            )
        return False

    # Owner always has access.
    if is_owner(update):
        return True

    # Everyone else needs owner approval.
    if not is_approved(update):
        if update.effective_message:
            await update.effective_message.reply_text(
                "🔒 Access denied.\n\n"
                f"👑 Owner: {OWNER_USERNAME}\n"
                "Send /request to ask the owner for access."
            )
        return False

    return True

async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_private_chat(update):
        return ConversationHandler.END

    if is_owner(update):
        await update.message.reply_text("👑 You are the owner.")
        return MENU

    user = update.effective_user
    await context.bot.send_message(
        chat_id=OWNER_USER_ID,
        text=(
            "🔔 *Access Request*\\n\\n"
            f"Name: {user.full_name}\\n"
            f"Username: @{user.username if user.username else 'N/A'}\\n"
            f"User ID: `{user.id}`\\n\\n"
            "Approve with:\n"
            f"`/approve {user.id}`\\n"
            "Reject/remove with:\n"
            f"`/revoke {user.id}`"
        ),
        parse_mode="Markdown",
    )
    await update.message.reply_text(
        f"📨 Request sent to owner ({OWNER_USERNAME}).\\n"
        "Wait for owner approval."
    )
    return ConversationHandler.END

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_owner(update) or not is_private_chat(update):
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text("Usage: /approve USER_ID")
        return MENU

    try:
        user_id = int(context.args[0])
        APPROVED_USERS.add(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` approved.", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Owner approved your access. Send /start to use the bot."
            )
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("❌ Invalid USER_ID.")
    return MENU

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_owner(update) or not is_private_chat(update):
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text("Usage: /revoke USER_ID")
        return MENU

    try:
        user_id = int(context.args[0])
        APPROVED_USERS.discard(user_id)
        await update.message.reply_text(f"🚫 User `{user_id}` access revoked.", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🚫 Owner revoked your bot access."
            )
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("❌ Invalid USER_ID.")
    return MENU

async def owner_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_private_chat(update) or not is_owner(update):
        return ConversationHandler.END

    keyboard = ReplyKeyboardMarkup(
        [["👑 Owner Details", "👥 Approved Users"]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        f"👑 *Owner Panel*\\n\\n"
        f"Name: {OWNER_NAME}\\n"
        f"Username: {OWNER_USERNAME}\\n"
        f"User ID: `{OWNER_USER_ID}`\\n\\n"
        "Use /approve USER_ID or /revoke USER_ID to manage access.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return MENU

async def approved_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_private_chat(update) or not is_owner(update):
        return ConversationHandler.END

    if not APPROVED_USERS:
        msg = "👥 No approved users."
    else:
        msg = "👥 *Approved Users*\\n\\n" + "\\n".join(
            f"• `{uid}`" for uid in sorted(APPROVED_USERS)
        )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return MENU


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ────────────────────────────────────────────────────────
MENU = 0

# Bind Recovery Email
BR_EMAIL, BR_TOKEN, BR_SECONDARY, BR_OTP = range(10, 14)

# Change Bind Email
CB_TOKEN, CB_OLD_EMAIL, CB_NEW_EMAIL, CB_OTP_OLD, CB_OTP_NEW = range(20, 25)

# Unbind Email
UB_EMAIL, UB_TOKEN, UB_OTP = range(30, 33)

# Cancel Bind
CA_TOKEN = 40

# Bind Info
BI_TOKEN = 50

# EAT to Access
EA_TOKEN = 60

# ── Shared constants ───────────────────────────────────────────────────────────
APP_ID = "100067"
BASE_URL = "https://100067.connect.garena.com/game/account_security"
GARENA_HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}
DEFAULT_SECONDARY = "3A43F5AE7A96BAE91481F6225AC98A378CA08EBE92DAC680AAABE41E82102179"

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["1️⃣ Bind Recovery Email", "2️⃣ Change Bind Email"],
        ["3️⃣ Unbind Email", "4️⃣ Cancel Bind Request"],
        ["5️⃣ Bind Info", "6️⃣ EAT to Access"],
        ["👑 Owner Details"],
    ],
    resize_keyboard=True,
)

# ── Helper functions ───────────────────────────────────────────────────────────

def fmt_json(data: dict) -> str:
    """Return a pretty-printed JSON string, safe for Telegram."""
    return f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"


def result_line(data: dict) -> str:
    if data.get("result") == 0 or data.get("error") == 0:
        return "✅ *SUCCESS*"
    return f"❌ *FAILED* (result: {data.get('result', '?')})"


def check_bind_info(access_token: str) -> str:
    """Fetch bind info and return a formatted string."""
    url = f"https://bind-info-senku.vercel.app/bind_info?access_token={access_token}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                info = data.get("data", {})
                lines = [
                    "📋 *Bind Info*",
                    f"📧 Current Email: `{info.get('current_email', 'N/A')}`",
                ]
                if info.get("pending_email"):
                    lines.append(f"⏳ Pending Email: `{info.get('pending_email')}`")
                lines.append(
                    f"⏱ Countdown: `{info.get('countdown_human', '0')}` "
                    f"({info.get('countdown_seconds', 0)} s)"
                )
                if data.get("summary"):
                    lines.append(f"📝 Summary: {data['summary']}")
                return "\n".join(lines)
            return f"❌ API error: {data.get('message', 'Unknown')}"
        return f"❌ HTTP {r.status_code}"
    except Exception as e:
        return f"❌ Error: {e}"


async def send_menu(update: Update, text: str = "Choose an option:") -> int:
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KEYBOARD,
    )
    return MENU


# ── /start & main menu ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data.clear()
    return await send_menu(
        update,
        "🎮 *ALPHA — Garena Account Manager*\n\nSelect an option below:",
    )


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    text = update.message.text
    if text == "👑 Owner Details":
        return await owner_details(update, context)
    if text == "👥 Approved Users":
        return await approved_users(update, context)
    if "1" in text:
        await update.message.reply_text(
            "📧 *Bind Recovery Email*\n\nEnter the email to bind:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return BR_EMAIL
    elif "2" in text:
        await update.message.reply_text(
            "🔄 *Change Bind Email*\n\nEnter your Access Token:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return CB_TOKEN
    elif "3" in text:
        await update.message.reply_text(
            "🔓 *Unbind Email*\n\nEnter the bound email:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return UB_EMAIL
    elif "4" in text:
        await update.message.reply_text(
            "❌ *Cancel Bind Request*\n\nEnter your Access Token:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return CA_TOKEN
    elif "5" in text:
        await update.message.reply_text(
            "ℹ️ *Bind Info*\n\nEnter your Access Token:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return BI_TOKEN
    elif "6" in text:
        await update.message.reply_text(
            "🔑 *EAT to Access*\n\nEnter your EAT token:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return EA_TOKEN
    else:
        return await send_menu(update, "⚠️ Please choose a valid option.")


# ── 1. Bind Recovery Email ─────────────────────────────────────────────────────

async def br_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["br_email"] = update.message.text.strip()
    await update.message.reply_text("Enter your Access Token:")
    return BR_TOKEN


async def br_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["br_token"] = update.message.text.strip()
    await update.message.reply_text(
        f"Enter secondary password\n_(leave blank to use default)_:",
        parse_mode="Markdown",
    )
    return BR_SECONDARY


async def br_secondary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    sec = update.message.text.strip()
    context.user_data["br_secondary"] = sec if sec else DEFAULT_SECONDARY

    email = context.user_data["br_email"]
    access_token = context.user_data["br_token"]

    # Send OTP via GarenaAccountBinder logic
    await update.message.reply_text("⏳ Sending OTP...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "GarenaMSDK/4.0.39(GFY-LX3 ;Android 13;en;HK;)",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "datadome=XjUykstNTPfQcRhQ6hLhjpqgsuvxVM8gvP59Zsfahr4DRCkZSSQzvYZUmslLlknS9AS3aPFG3S3Z_~SMn7ulGH9cawYoziogCS5sTm6hoW35ctShDcf7U90fYTkaSEaA",
    })
    context.user_data["br_session"] = session

    try:
        r = session.post(
            f"{BASE_URL}/bind:send_otp",
            data={"app_id": APP_ID, "access_token": access_token, "email": email, "locale": "en_HK"},
        )
        data = r.json()
        if r.status_code == 200 and (data.get("result") == 0 or data.get("error") == 0):
            await update.message.reply_text(
                f"✅ OTP sent to `{email}`\n\nEnter the OTP you received:",
                parse_mode="Markdown",
            )
            return BR_OTP
        else:
            await update.message.reply_text(
                f"❌ Failed to send OTP:\n{fmt_json(data)}",
                parse_mode="Markdown",
            )
            return await send_menu(update)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await send_menu(update)


async def br_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    otp = update.message.text.strip()
    email = context.user_data["br_email"]
    access_token = context.user_data["br_token"]
    secondary = context.user_data["br_secondary"]
    session = context.user_data["br_session"]

    await update.message.reply_text("⏳ Verifying OTP...")
    try:
        r = session.post(
            f"{BASE_URL}/bind:verify_otp",
            data={"app_id": APP_ID, "access_token": access_token, "otp": otp, "email": email},
        )
        data = r.json()
        verifier_token = (
            data.get("data", {}).get("verifier_token")
            or data.get("verifier_token")
            or data.get("token")
        )
        if not verifier_token:
            await update.message.reply_text(
                f"❌ No verifier token:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)

        await update.message.reply_text("✅ OTP verified! Creating bind request...")

        r2 = session.post(
            f"{BASE_URL}/bind:create_bind_request",
            data={
                "app_id": APP_ID,
                "access_token": access_token,
                "verifier_token": verifier_token,
                "secondary_password": secondary,
                "email": email,
            },
        )
        data2 = r2.json()
        status = result_line(data2)
        await update.message.reply_text(
            f"{status}\n\n{fmt_json(data2)}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── 2. Change Bind Email ───────────────────────────────────────────────────────

async def cb_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["cb_token"] = update.message.text.strip()
    await update.message.reply_text("Enter your Old (current bound) Email:")
    return CB_OLD_EMAIL


async def cb_old_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["cb_old_email"] = update.message.text.strip()
    await update.message.reply_text("Enter your New Email:")
    return CB_NEW_EMAIL


async def cb_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["cb_new_email"] = update.message.text.strip()
    access_token = context.user_data["cb_token"]
    old_email = context.user_data["cb_old_email"]

    # Show bind info then send OTP to old email
    bind_msg = check_bind_info(access_token)
    await update.message.reply_text(bind_msg, parse_mode="Markdown")
    await update.message.reply_text(f"⏳ Sending OTP to `{old_email}`...", parse_mode="Markdown")

    try:
        r = requests.post(
            f"{BASE_URL}/bind:send_otp",
            headers=GARENA_HEADERS,
            data={"email": old_email, "locale": "en_PK", "region": "PK",
                  "app_id": APP_ID, "access_token": access_token},
        )
        data = r.json()
        if r.status_code == 200 and data.get("result") == 0:
            await update.message.reply_text(
                f"✅ OTP sent to `{old_email}`\n\nEnter the OTP from your old email:",
                parse_mode="Markdown",
            )
            return CB_OTP_OLD
        else:
            await update.message.reply_text(
                f"❌ Failed to send OTP:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await send_menu(update)


async def cb_otp_old(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    otp_old = update.message.text.strip()
    access_token = context.user_data["cb_token"]
    old_email = context.user_data["cb_old_email"]
    new_email = context.user_data["cb_new_email"]

    await update.message.reply_text("⏳ Verifying old email OTP...")
    try:
        r = requests.post(
            f"{BASE_URL}/bind:verify_identity",
            headers=GARENA_HEADERS,
            data={"email": old_email, "app_id": APP_ID, "access_token": access_token, "otp": otp_old},
        )
        data = r.json()
        identity_token = data.get("identity_token")
        if not identity_token:
            await update.message.reply_text(
                f"❌ No identity token:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)

        context.user_data["cb_identity_token"] = identity_token
        await update.message.reply_text(f"✅ Verified! Now sending OTP to `{new_email}`...", parse_mode="Markdown")

        r2 = requests.post(
            f"{BASE_URL}/bind:send_otp",
            headers=GARENA_HEADERS,
            data={"email": new_email, "locale": "en_PK", "region": "PK",
                  "app_id": APP_ID, "access_token": access_token},
        )
        data2 = r2.json()
        if r2.status_code == 200 and data2.get("result") == 0:
            await update.message.reply_text(
                f"✅ OTP sent to `{new_email}`\n\nEnter the OTP from your new email:",
                parse_mode="Markdown",
            )
            return CB_OTP_NEW
        else:
            await update.message.reply_text(
                f"❌ Failed to send OTP to new email:\n{fmt_json(data2)}", parse_mode="Markdown"
            )
            return await send_menu(update)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await send_menu(update)


async def cb_otp_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    otp_new = update.message.text.strip()
    access_token = context.user_data["cb_token"]
    new_email = context.user_data["cb_new_email"]
    identity_token = context.user_data["cb_identity_token"]

    await update.message.reply_text("⏳ Verifying new email OTP...")
    try:
        r = requests.post(
            f"{BASE_URL}/bind:verify_otp",
            headers=GARENA_HEADERS,
            data={"email": new_email, "app_id": APP_ID, "access_token": access_token, "otp": otp_new},
        )
        data = r.json()
        verifier_token = data.get("verifier_token")
        if not verifier_token:
            await update.message.reply_text(
                f"❌ No verifier token:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)

        await update.message.reply_text("⏳ Creating rebind request...")
        r2 = requests.post(
            f"{BASE_URL}/bind:create_rebind_request",
            headers=GARENA_HEADERS,
            data={
                "identity_token": identity_token,
                "email": new_email,
                "app_id": APP_ID,
                "verifier_token": verifier_token,
                "access_token": access_token,
            },
        )
        data2 = r2.json()
        status = result_line(data2)
        await update.message.reply_text(
            f"{status}\n\n{fmt_json(data2)}", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── 3. Unbind Email ────────────────────────────────────────────────────────────

async def ub_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data["ub_email"] = update.message.text.strip()
    await update.message.reply_text("Enter your Access Token:")
    return UB_TOKEN


async def ub_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    access_token = update.message.text.strip()
    context.user_data["ub_token"] = access_token
    email = context.user_data["ub_email"]

    bind_msg = check_bind_info(access_token)
    await update.message.reply_text(bind_msg, parse_mode="Markdown")
    await update.message.reply_text(f"⏳ Sending OTP to `{email}`...", parse_mode="Markdown")

    try:
        r = requests.post(
            f"{BASE_URL}/bind:send_otp",
            headers=GARENA_HEADERS,
            data={"email": email, "locale": "en_PK", "region": "PK",
                  "app_id": APP_ID, "access_token": access_token},
        )
        data = r.json()
        if r.status_code == 200 and data.get("result") == 0:
            await update.message.reply_text(
                f"✅ OTP sent!\n\nEnter the OTP from `{email}`:", parse_mode="Markdown"
            )
            return UB_OTP
        else:
            await update.message.reply_text(
                f"❌ Failed to send OTP:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await send_menu(update)


async def ub_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    otp = update.message.text.strip()
    email = context.user_data["ub_email"]
    access_token = context.user_data["ub_token"]

    await update.message.reply_text("⏳ Verifying OTP...")
    try:
        r = requests.post(
            f"{BASE_URL}/bind:verify_identity",
            headers=GARENA_HEADERS,
            data={"email": email, "app_id": APP_ID, "access_token": access_token, "otp": otp},
        )
        data = r.json()
        identity_token = data.get("identity_token")
        if not identity_token:
            await update.message.reply_text(
                f"❌ No identity token:\n{fmt_json(data)}", parse_mode="Markdown"
            )
            return await send_menu(update)

        await update.message.reply_text("⏳ Creating unbind request...")
        r2 = requests.post(
            f"{BASE_URL}/bind:create_unbind_request",
            headers=GARENA_HEADERS,
            data={"app_id": APP_ID, "access_token": access_token, "identity_token": identity_token},
        )
        data2 = r2.json()
        status = result_line(data2)
        await update.message.reply_text(
            f"{status}\n\n{fmt_json(data2)}", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── 4. Cancel Bind Request ─────────────────────────────────────────────────────

async def ca_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    access_token = update.message.text.strip()

    bind_msg = check_bind_info(access_token)
    await update.message.reply_text(bind_msg, parse_mode="Markdown")
    await update.message.reply_text("⏳ Cancelling bind request...")

    try:
        r = requests.post(
            "https://100067.connect.gopapi.io/game/account_security/bind:cancel_request",
            headers=GARENA_HEADERS,
            data={"app_id": APP_ID, "access_token": access_token},
        )
        data = r.json()
        status = result_line(data)
        await update.message.reply_text(
            f"{status}\n\n{fmt_json(data)}", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── 5. Bind Info ───────────────────────────────────────────────────────────────

async def bi_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    access_token = update.message.text.strip()
    await update.message.reply_text("⏳ Fetching bind info...")

    url = f"https://bind-info-senku.vercel.app/bind_info?access_token={access_token}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                info = data.get("data", {})
                lines = [
                    "📋 *Account Bind Information*",
                    f"📧 Current Email: `{info.get('current_email', 'N/A')}`",
                ]
                if info.get("pending_email"):
                    lines.append(f"⏳ Pending Email: `{info.get('pending_email')}`")
                lines.append(
                    f"⏱ Countdown: `{info.get('countdown_human', '0')}` "
                    f"({info.get('countdown_seconds', 0)} s)"
                )
                if data.get("summary"):
                    lines.append(f"📝 Summary: {data['summary']}")
                if info.get("raw_response"):
                    lines.append(f"\n🔍 Raw Response:\n{fmt_json(info['raw_response'])}")
                await update.message.reply_text(
                    "\n".join(lines), parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ API error: {data.get('message', 'Unknown')}"
                )
        else:
            await update.message.reply_text(f"❌ HTTP {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── 6. EAT to Access ──────────────────────────────────────────────────────────

async def ea_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    eat_token = update.message.text.strip()
    await update.message.reply_text("⏳ Converting EAT token...")

    try:
        r = requests.get(
            f"https://eat-to-access-beta.vercel.app/eat_to_access?eat_token={eat_token}",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success" and "access_token" in data:
            lines = [
                "✅ *Success!*",
                f"🔑 Access Token: `{data['access_token']}`",
            ]
            if data.get("region"):
                lines.append(f"🌏 Region: `{data['region']}`")
            if data.get("game_uid"):
                lines.append(f"🎮 Game UID: `{data['game_uid']}`")
            if data.get("nickname"):
                lines.append(f"👤 Nickname: `{data['nickname']}`")
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"❌ Failed:\n{fmt_json(data)}", parse_mode="Markdown"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return await send_menu(update)


# ── Cancel / fallback ──────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await private_access_guard(update, context):
        return ConversationHandler.END
    context.user_data.clear()
    return await send_menu(update, "❎ Cancelled. Back to main menu.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", start),
            CommandHandler("request", request_access),
            CommandHandler("approve", approve_user),
            CommandHandler("revoke", revoke_user),
            CommandHandler("owner", owner_details),
        ],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router)],

            # Bind Recovery Email
            BR_EMAIL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, br_email)],
            BR_TOKEN:     [MessageHandler(filters.TEXT & ~filters.COMMAND, br_token)],
            BR_SECONDARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, br_secondary)],
            BR_OTP:       [MessageHandler(filters.TEXT & ~filters.COMMAND, br_otp)],

            # Change Bind Email
            CB_TOKEN:     [MessageHandler(filters.TEXT & ~filters.COMMAND, cb_token)],
            CB_OLD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, cb_old_email)],
            CB_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, cb_new_email)],
            CB_OTP_OLD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, cb_otp_old)],
            CB_OTP_NEW:   [MessageHandler(filters.TEXT & ~filters.COMMAND, cb_otp_new)],

            # Unbind Email
            UB_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ub_email)],
            UB_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ub_token)],
            UB_OTP:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ub_otp)],

            # Cancel Bind
            CA_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ca_token)],

            # Bind Info
            BI_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bi_token)],

            # EAT to Access
            EA_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ea_token)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv)
    logger.info("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
