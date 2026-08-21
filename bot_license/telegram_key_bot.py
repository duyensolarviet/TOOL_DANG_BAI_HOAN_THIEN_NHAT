import os
import sys
import json
import re
import time
import threading
import random
import string
import datetime
import html
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure parent directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.license_manager.storage_backend import CloudStorageBackend, get_network_time
from src.license_manager.crypto_token import generate_signed_license_token

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_bot_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bot_token": "",
        "admin_ids": [],
        "firebase_url": "",
        "firebase_auth_secret": ""
    }

config = load_bot_config()
BOT_TOKEN = config.get("bot_token", "").strip()
ADMIN_IDS = config.get("admin_ids", [])
FIREBASE_URL = config.get("firebase_url", "").strip()
FIREBASE_AUTH_SECRET = config.get("firebase_auth_secret", "").strip()

storage = CloudStorageBackend(firebase_url=FIREBASE_URL, auth_secret=FIREBASE_AUTH_SECRET)

if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("=" * 60)
    print("⚠ CHƯA CẤU HÌNH BOT TOKEN TELEGRAM!")
    print(f"Vui lòng mở file: {CONFIG_PATH}")
    print("Điền 'bot_token' (lấy từ @BotFather).")
    print("=" * 60)

bot = telebot.TeleBot(BOT_TOKEN if BOT_TOKEN and BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE" else "123456:dummy")

ITEMS_PER_PAGE = 6

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS

def generate_random_code(length=6) -> str:
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(random.choice(chars) for _ in range(length))

def make_key_code(package: str) -> str:
    prefix_map = {
        "trial_1day": "VD-TEST",
        "1_month": "VD-1M",
        "3_months": "VD-3M",
        "6_months": "VD-6M",
        "1_year": "VD-1Y",
        "lifetime": "VD-VIP",
        "custom": "VD-KEY"
    }
    prefix = prefix_map.get(package, "VD-KEY")
    code = generate_random_code(6)
    return f"{prefix}-{code}"

def is_hwid_format(text: str) -> bool:
    """Detects if a string is a device HWID (e.g. VD-5871-B47B-6A58-3FDF)"""
    clean = text.strip().upper()
    parts = clean.split("-")
    if len(parts) >= 4 and parts[0] in ["VD", "HWID", "DEV"]:
        return True
    if len(parts) == 4 and all(len(p) == 4 for p in parts):
        return True
    return False

def parse_iso_time(time_str: str) -> datetime.datetime:
    if not time_str:
        return None
    try:
        clean = time_str.strip().replace("T", " ")[:19]
        return datetime.datetime.fromisoformat(clean)
    except Exception:
        try:
            return datetime.datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

def parse_custom_duration_and_note(input_text: str):
    """
    Parses flexible duration inputs:
    - "30 phút", "30p", "5p", "5phut", "15m"
    - "2h", "2 giờ", "2 tiếng", "12h Demo"
    - "3d", "3 ngày", "45", "10 ngày Anh Nam"
    - "1w", "1 tuần"
    - "1 tháng", "3 tháng"
    - "1 năm"
    - "VD-5871-B47B-6A58-3FDF vu van a: 30p"
    Returns: (timedelta, display_label, clean_note)
    """
    text = input_text.strip()
    
    # Strip HWID if present in text
    hwid_match = re.search(r'VD-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}', text, re.IGNORECASE)
    if hwid_match:
        text = text.replace(hwid_match.group(0), "").strip()

    text = re.sub(r'^[:\-\s]+', '', text).strip()

    # Regex patterns
    min_match = re.search(r'(\d+)\s*(?:phút|phut|min|mins|p)\b', text, re.IGNORECASE)
    hour_match = re.search(r'(\d+)\s*(?:giờ|gio|tiếng|tieng|h|hr|hrs)\b', text, re.IGNORECASE)
    day_match = re.search(r'(\d+)\s*(?:ngày|ngay|d|day|days)\b', text, re.IGNORECASE)
    week_match = re.search(r'(\d+)\s*(?:tuần|tuan|w|week|weeks)\b', text, re.IGNORECASE)
    month_match = re.search(r'(\d+)\s*(?:tháng|thang|month|months)\b', text, re.IGNORECASE)
    year_match = re.search(r'(\d+)\s*(?:năm|nam|y|year|years)\b', text, re.IGNORECASE)

    delta = None
    label = ""
    matched_span = None

    if min_match:
        val = int(min_match.group(1))
        delta = datetime.timedelta(minutes=val)
        label = f"{val} Phút"
        matched_span = min_match.span()
    elif hour_match:
        val = int(hour_match.group(1))
        delta = datetime.timedelta(hours=val)
        label = f"{val} Giờ"
        matched_span = hour_match.span()
    elif day_match:
        val = int(day_match.group(1))
        delta = datetime.timedelta(days=val)
        label = f"{val} Ngày"
        matched_span = day_match.span()
    elif week_match:
        val = int(week_match.group(1))
        delta = datetime.timedelta(weeks=val)
        label = f"{val} Tuần"
        matched_span = week_match.span()
    elif month_match:
        val = int(month_match.group(1))
        delta = datetime.timedelta(days=val * 30)
        label = f"{val} Tháng"
        matched_span = month_match.span()
    elif year_match:
        val = int(year_match.group(1))
        delta = datetime.timedelta(days=val * 365)
        label = f"{val} Năm"
        matched_span = year_match.span()
    else:
        # Standalone number: e.g. "45" or "1" or "vu van a: 1"
        num_match = re.search(r'\b(\d+)\b', text)
        if num_match:
            val = int(num_match.group(1))
            delta = datetime.timedelta(days=val)
            label = f"{val} Ngày"
            matched_span = num_match.span()

    if not delta:
        return None, "", text

    # Extract note from remaining text
    note = (text[:matched_span[0]] + " " + text[matched_span[1]:]).strip()
    note = re.sub(r'[:\-\s]+', ' ', note).strip()
    if not note:
        note = f"Gói {label}"

    return delta, label, note

def safe_edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except ApiTelegramException as e:
        if "message is not modified" not in str(e).lower():
            try:
                bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")
            except Exception:
                pass
    except Exception:
        pass

def safe_send_message(chat_id, text, reply_markup=None):
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        clean_text = text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "")
        return bot.send_message(chat_id, clean_text, reply_markup=reply_markup)

# ==================== MAIN MENUS & KEYBOARDS ====================

def get_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("➕ Cấp Key Mới", callback_data="menu_gen_key")
    b2 = types.InlineKeyboardButton("💻 Kích Hoạt Theo Mã Máy", callback_data="menu_paste_hwid")
    b3 = types.InlineKeyboardButton("📋 Danh Sách Key", callback_data="menu_list_0_all")
    b4 = types.InlineKeyboardButton("⏳ Gia Hạn Key / Máy", callback_data="menu_extend_key")
    b5 = types.InlineKeyboardButton("🔄 Reset HWID (Đổi máy)", callback_data="menu_reset_hwid")
    b6 = types.InlineKeyboardButton("📊 Thống Kê Key", callback_data="menu_stats")
    b7 = types.InlineKeyboardButton("🟢 Thống Kê Online", callback_data="menu_online_stats")
    b8 = types.InlineKeyboardButton("🔍 Tra Cứu Key / HWID", callback_data="menu_search_key")
    b9 = types.InlineKeyboardButton("💾 Sao Lưu Dữ Liệu (Backup)", callback_data="menu_backup_data")
    b10 = types.InlineKeyboardButton("⚙ Cài Đặt / Kết Nối", callback_data="menu_settings")
    markup.add(b1, b2)
    markup.add(b3, b4)
    markup.add(b5, b6)
    markup.add(b7, b8)
    markup.add(b9, b10)
    return markup

def get_gen_package_markup(target_hwid: str = ""):
    markup = types.InlineKeyboardMarkup(row_width=2)
    prefix = f"genfor_{target_hwid}_" if target_hwid else "gen_"
    
    p1 = types.InlineKeyboardButton("📦 Gói 1 Tháng (30 Ngày)", callback_data=f"{prefix}1_month")
    p2 = types.InlineKeyboardButton("📦 Gói 3 Tháng (90 Ngày)", callback_data=f"{prefix}3_months")
    p3 = types.InlineKeyboardButton("📦 Gói 6 Tháng (180 Ngày)", callback_data=f"{prefix}6_months")
    p4 = types.InlineKeyboardButton("👑 Gói 1 Năm (365 Ngày)", callback_data=f"{prefix}1_year")
    p5 = types.InlineKeyboardButton("💎 Gói Vĩnh Viễn", callback_data=f"{prefix}lifetime")
    p6 = types.InlineKeyboardButton("✏ Tự Nhập Thời Gian (Phút/Giờ/Ngày)", callback_data=f"{prefix}custom")
    back = types.InlineKeyboardButton("⬅ Quay Lại Menu Chính", callback_data="main_menu")
    markup.add(p1, p2)
    markup.add(p3, p4)
    markup.add(p5)
    markup.add(p6)
    markup.add(back)
    return markup

def get_key_action_markup(key: str, status: str):
    markup = types.InlineKeyboardMarkup(row_width=2)
    b_reset = types.InlineKeyboardButton("🔄 Reset HWID (Đổi máy)", callback_data=f"act_reset_{key}")
    b_extend = types.InlineKeyboardButton("⏳ Gia Hạn Nhanh", callback_data=f"act_ext_{key}")
    
    ban_label = "🟢 Mở Khóa Key" if status == "banned" else "🚫 Khóa Key"
    b_ban = types.InlineKeyboardButton(ban_label, callback_data=f"act_toggleban_{key}")
    b_del = types.InlineKeyboardButton("🗑 Xóa Key", callback_data=f"act_delask_{key}")
    
    b_back = types.InlineKeyboardButton("📋 Về Danh Sách", callback_data="menu_list_0_all")
    b_menu = types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu")
    
    markup.add(b_reset)
    markup.add(b_extend, b_ban)
    markup.add(b_del)
    markup.add(b_back, b_menu)
    return markup

def get_extend_options_markup(key: str):
    markup = types.InlineKeyboardMarkup(row_width=2)
    e1 = types.InlineKeyboardButton("📦 Gói 1 Tháng (30 Ngày)", callback_data=f"do_ext_{key}_30d")
    e2 = types.InlineKeyboardButton("📦 Gói 3 Tháng (90 Ngày)", callback_data=f"do_ext_{key}_90d")
    e3 = types.InlineKeyboardButton("📦 Gói 6 Tháng (180 Ngày)", callback_data=f"do_ext_{key}_180d")
    e4 = types.InlineKeyboardButton("👑 Gói 1 Năm (365 Ngày)", callback_data=f"do_ext_{key}_365d")
    e5 = types.InlineKeyboardButton("💎 Gói Vĩnh Viễn", callback_data=f"do_ext_{key}_9999d")
    e6 = types.InlineKeyboardButton("✏ Tự Nhập Thời Gian (Phút/Giờ/Ngày)", callback_data=f"custom_ext_{key}")
    back = types.InlineKeyboardButton("⬅ Quay Lại Menu Chính", callback_data="main_menu")
    markup.add(e1, e2)
    markup.add(e3, e4)
    markup.add(e5)
    markup.add(e6)
    markup.add(back)
    return markup

# ==================== HANDLERS ====================

@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        safe_send_message(
            message.chat.id,
            f"⛔ <b>Bạn không có quyền truy cập hệ thống quản trị Key.</b>\nID của bạn: <code>{user_id}</code>\nVui lòng liên hệ Quản trị viên để được cấp phép."
        )
        return

    first_name = html.escape(message.from_user.first_name or "Admin")
    db_status = "✅ Firebase Realtime" if storage.is_cloud_enabled() else "📁 Lưu Cục Bộ (Local DB)"

    text = (
        "🤖 <b>HỆ THỐNG QUẢN LÝ BẢN QUYỀN - VU DUYEN TOOLS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Quản trị viên:</b> {first_name} (ID: <code>{user_id}</code>)\n"
        f"🌐 <b>Cơ sở dữ liệu:</b> {db_status}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Bạn có thể dán thẳng <b>Mã Máy (HWID)</b> hoặc <b>Mã Key</b> vào tin nhắn để kích hoạt / gia hạn ngay lập tức!</i>\n\n"
        "Chọn chức năng bên dưới:"
    )
    safe_send_message(message.chat.id, text, reply_markup=get_main_menu_markup())

@bot.message_handler(commands=['help'])
def handle_help(message):
    if not is_admin(message.from_user.id): return
    text = (
        "📖 <b>DANH SÁCH LỆNH QUẢN TRỊ BOT KEY:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <code>/menu</code> : Mở menu quản trị chính\n"
        "🔹 <code>/genkey [thời_gian] [ghi_chú]</code> : Tạo key nhanh\n"
        "   <i>Ví dụ:</i>\n"
        "   • <code>/genkey 30p Test 30 phut</code>\n"
        "   • <code>/genkey 2h Test 2 gio</code>\n"
        "   • <code>/genkey 1m Anh Nam</code>\n"
        "   • <code>/genkey 1y VIP Tran B</code>\n"
        "🔹 <code>/hwid [mã_máy]</code> : Kích hoạt trực tiếp theo mã máy\n"
        "🔹 <code>/extend [mã_key_hoặc_hwid] [thời_gian]</code> : Gia hạn key/máy\n"
        "   <i>Ví dụ:</i> <code>/extend VD-1M-ABC123 30m</code> hoặc <code>/extend VD-1M-ABC123 30d</code>\n"
        "🔹 <code>/reset [mã_key]</code> : Reset HWID (Đổi máy tính)\n"
        "🔹 <code>/check [mã_key_hoặc_hwid]</code> : Tra cứu chi tiết\n"
        "🔹 <code>/ban [mã_key]</code> & <code>/unban [mã_key]</code> : Khóa/Mở key\n"
        "🔹 <code>/delkey [mã_key]</code> : Xóa vĩnh viễn key\n"
        "🔹 <code>/stats</code> : Thống kê tổng quan tất cả key\n"
        "🔹 <code>/online</code> : Thống kê người dùng online\n"
        "🔹 <code>/backup</code> : Tải file sao lưu dữ liệu (.json) ngay lập tức\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_send_message(message.chat.id, text)

@bot.message_handler(commands=['backup', 'export', 'saoluu'])
def handle_backup_cmd(message):
    if not is_admin(message.from_user.id): return
    safe_send_message(message.chat.id, "⏳ <i>Đang đóng gói và xuất file sao lưu dữ liệu...</i>")
    send_backup_data(message.chat.id, is_auto=False)

@bot.message_handler(commands=['stats'])
def handle_stats_cmd(message):
    if not is_admin(message.from_user.id): return
    show_stats(message.chat.id)

@bot.message_handler(commands=['online'])
def handle_online_cmd(message):
    if not is_admin(message.from_user.id): return
    show_online_stats(message.chat.id)

@bot.message_handler(commands=['hwid'])
def handle_hwid_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/hwid [MÃ_MÁY]</code> (Ví dụ: <code>/hwid VD-5871-B47B-6A58-3FDF</code>)")
        return
    handle_hwid_detected(message.chat.id, parts[1])

@bot.message_handler(commands=['genkey'])
def handle_genkey_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        safe_send_message(
            message.chat.id,
            "ℹ <b>Cú pháp tạo key:</b> <code>/genkey [thời_gian] [tên_khách]</code>\n"
            "<i>Ví dụ:</i>\n"
            "• <code>/genkey 30p Test thu</code>\n"
            "• <code>/genkey 2h Khach Demo</code>\n"
            "• <code>/genkey 1m Anh Nam</code>\n"
            "• <code>/genkey 1y VIP Tran B</code>"
        )
        return

    delta, label, note = parse_custom_duration_and_note(parts[1])
    if not delta:
        safe_send_message(message.chat.id, "❌ Thời gian không hợp lệ! (Ví dụ: 30p, 2h, 3 ngày, 1m, 1y).")
        return

    create_and_send_key(message.chat.id, "custom", delta, label, note=note)

@bot.message_handler(commands=['extend'])
def handle_extend_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 3:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/extend [MÃ_KEY_HOẶC_HWID] [THỜI_GIAN]</code> (Ví dụ: <code>/extend VD-1M-ABC 30m</code> hoặc <code>/extend VD-1M-ABC 30d</code>)")
        return
    target = parts[1]
    duration_str = parts[2]
    delta, label, _ = parse_custom_duration_and_note(duration_str)
    if not delta:
        safe_send_message(message.chat.id, "❌ Thời gian gia hạn không hợp lệ (Ví dụ: 30p, 2h, 30d, 1m).")
        return
    execute_extend_key_delta(message.chat.id, target, delta, label)

@bot.message_handler(commands=['reset'])
def handle_reset_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split()
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/reset [MÃ_KEY]</code>")
        return
    reset_hwid_for_key(message.chat.id, parts[1])

@bot.message_handler(commands=['check'])
def handle_check_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split()
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/check [MÃ_KEY_HOẶC_HWID]</code>")
        return
    target = parts[1].strip()
    if is_hwid_format(target):
        handle_hwid_detected(message.chat.id, target)
    else:
        show_key_detail(message.chat.id, target)

@bot.message_handler(commands=['ban'])
def handle_ban_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split()
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/ban [MÃ_KEY]</code>")
        return
    set_key_ban_status(message.chat.id, parts[1], True)

@bot.message_handler(commands=['unban'])
def handle_unban_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split()
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/unban [MÃ_KEY]</code>")
        return
    set_key_ban_status(message.chat.id, parts[1], False)

@bot.message_handler(commands=['delkey', 'delete'])
def handle_delkey_cmd(message):
    if not is_admin(message.from_user.id): return
    parts = message.text.strip().split()
    if len(parts) < 2:
        safe_send_message(message.chat.id, "❌ Cú pháp: <code>/delkey [MÃ_KEY]</code>")
        return
    execute_delete_key(message.chat.id, parts[1])

# ==================== SMART TEXT RECEIVER ====================

@bot.message_handler(func=lambda msg: True)
def handle_incoming_text(message):
    user_id = message.from_user.id
    if not is_admin(user_id): return
    
    text = message.text.strip()
    if text.startswith("/"): return

    # 1. Check if text contains both HWID and duration (e.g. "VD-5871-B47B-6A58-3FDF 30p")
    hwid_match = re.search(r'VD-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}', text, re.IGNORECASE)
    if hwid_match:
        hwid_val = hwid_match.group(0).upper()
        rem_text = text.replace(hwid_match.group(0), "").strip()
        delta, label, note = parse_custom_duration_and_note(rem_text)
        if delta:
            create_and_bind_key_for_hwid(message.chat.id, hwid_val, "custom", delta, label, note=note or f"Gói {label}")
            return
        elif is_hwid_format(text):
            handle_hwid_detected(message.chat.id, hwid_val)
            return

    # 2. Check if text is a standalone duration (e.g. "30p", "2h", "1m", "30 ngày", "3 tháng")
    delta, label, note = parse_custom_duration_and_note(text)
    if delta:
        create_and_send_key(message.chat.id, "custom", delta, label, note=note or f"Gói {label}")
        return

    # 3. Check if text is exact Key
    key_data = storage.get_key(text)
    if key_data:
        show_key_detail(message.chat.id, text)
        return

    # 4. Search
    process_search_key(message)

# ==================== CALLBACK QUERY ROUTER ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    user_id = call.from_user.id
    if not is_admin(user_id):
        return

    data = call.data

    if data == "main_menu":
        text = "🤖 <b>HỆ THỐNG QUẢN LÝ BẢN QUYỀN - VU DUYEN TOOLS</b>\nChọn chức năng quản lý bên dưới:"
        safe_edit_message(call.message.chat.id, call.message.message_id, text, reply_markup=get_main_menu_markup())
        return

    elif data == "menu_gen_key":
        text = (
            "➕ <b>CẤP KEY MỚI (TỰ ĐỘNG GÁN KHI KHÁCH NHẬP):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Chọn gói bản quyền bên dưới để tạo mã Key gửi cho khách hàng:</i>"
        )
        safe_edit_message(call.message.chat.id, call.message.message_id, text, reply_markup=get_gen_package_markup())
        return

    elif data == "menu_paste_hwid":
        msg = safe_send_message(
            call.message.chat.id,
            "💻 <b>NHẬP MÃ THIẾT BỊ (HWID) CỦA KHÁCH:</b>\n"
            "<i>(Ví dụ dán: <code>VD-5871-B47B-6A58-3FDF</code> hoặc gửi /cancel để hủy):</i>"
        )
        bot.register_next_step_handler(msg, lambda m: handle_hwid_detected(m.chat.id, m.text.strip()))
        return

    elif data.startswith("genfor_"):
        # Format: genfor_{hwid}_{package}
        parts = data.split("_")
        target_hwid = parts[1]
        package_type = "_".join(parts[2:])

        if package_type == "custom":
            msg = safe_send_message(
                call.message.chat.id,
                f"✏ <b>NHẬP THỜI GIAN SỬ DỤNG CHO MÁY <code>{html.escape(target_hwid)}</code>:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>Bạn có thể nhập phút, giờ, ngày bất kỳ kèm tên khách:</i>\n"
                "• <code>30 phút</code> hoặc <code>30p</code> (30 Phút)\n"
                "• <code>5p</code> hoặc <code>5 phút Khach Nam</code> (5 Phút)\n"
                "• <code>2 giờ</code> hoặc <code>2h Test Tool</code> (2 Giờ)\n"
                "• <code>3 ngày</code> hoặc <code>45 Khach Nguyen Van A</code>\n"
                "• <code>1</code> (1 ngày)\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Nhập ngay bên dưới (hoặc gửi /cancel để hủy):</i>"
            )
            bot.register_next_step_handler(msg, lambda m: process_custom_gen_for_hwid(m, target_hwid))
            return

        pkg_map = {
            "1_month": ("1 Tháng", datetime.timedelta(days=30)),
            "3_months": ("3 Tháng", datetime.timedelta(days=90)),
            "6_months": ("6 Tháng", datetime.timedelta(days=180)),
            "1_year": ("1 Năm", datetime.timedelta(days=365)),
            "lifetime": ("Vĩnh Viễn", datetime.timedelta(days=9999)),
            "trial_1day": ("Dùng Thử 1 Ngày", datetime.timedelta(days=1))
        }
        name, delta = pkg_map.get(package_type, ("1 Tháng", datetime.timedelta(days=30)))
        create_and_bind_key_for_hwid(call.message.chat.id, target_hwid, package_type, delta, name, note=f"Kích hoạt máy {target_hwid[:8]}")
        return

    elif data.startswith("gen_"):
        package_type = data.replace("gen_", "")
        if package_type == "custom":
            msg = safe_send_message(
                call.message.chat.id,
                "✏ <b>NHẬP THỜI GIAN SỬ DỤNG CHO KEY MỚI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>Bạn có thể nhập phút, giờ, ngày bất kỳ kèm tên khách:</i>\n"
                "• <code>30 phút</code> hoặc <code>30p</code> (30 Phút)\n"
                "• <code>5p</code> hoặc <code>5 phút Khach Nam</code> (5 Phút)\n"
                "• <code>2 giờ</code> hoặc <code>2h Test Tool</code> (2 Giờ)\n"
                "• <code>3 ngày</code> hoặc <code>45 Khach Nguyen Van A</code>\n"
                "• <code>1</code> (1 ngày)\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Nhập ngay bên dưới (hoặc gửi /cancel để hủy):</i>"
            )
            bot.register_next_step_handler(msg, process_custom_gen_key)
            return

        pkg_map = {
            "1_month": ("1 Tháng", datetime.timedelta(days=30)),
            "3_months": ("3 Tháng", datetime.timedelta(days=90)),
            "6_months": ("6 Tháng", datetime.timedelta(days=180)),
            "1_year": ("1 Năm", datetime.timedelta(days=365)),
            "lifetime": ("Vĩnh Viễn", datetime.timedelta(days=9999)),
            "trial_1day": ("Dùng Thử 1 Ngày", datetime.timedelta(days=1))
        }
        name, delta = pkg_map.get(package_type, ("1 Tháng", datetime.timedelta(days=30)))
        create_and_send_key(call.message.chat.id, package_type, delta, name, note=f"Tạo bởi {call.from_user.first_name}")
        return

    elif data.startswith("menu_list_"):
        parts = data.split("_")
        page = int(parts[2]) if len(parts) > 2 else 0
        filter_type = parts[3] if len(parts) > 3 else "all"
        show_keys_list(call.message.chat.id, call.message.message_id, page=page, filter_type=filter_type)
        return

    elif data.startswith("view_key_"):
        key = data.replace("view_key_", "")
        show_key_detail(call.message.chat.id, key, message_id=call.message.message_id)
        return

    elif data == "menu_search_key":
        msg = safe_send_message(
            call.message.chat.id,
            "🔍 <b>Nhập mã Key hoặc Mã Máy (HWID) cần tra cứu:</b>\n<i>(Gửi /cancel để hủy)</i>"
        )
        bot.register_next_step_handler(msg, process_search_key)
        return

    elif data == "menu_reset_hwid":
        msg = safe_send_message(
            call.message.chat.id,
            "🔄 <b>Nhập mã Key cần Reset Thiết Bị (HWID):</b>\n<i>Sau khi reset, khách hàng có thể kích hoạt trên máy tính mới.</i>"
        )
        bot.register_next_step_handler(msg, process_reset_hwid)
        return

    elif data == "menu_extend_key":
        msg = safe_send_message(
            call.message.chat.id,
            "⏳ <b>Nhập mã Key (hoặc HWID) và thời gian cần gia hạn:</b>\n"
            "Cú pháp: <code>MÃ_KEY THỜI_GIAN</code>\n"
            "<i>Ví dụ:</i>\n"
            "• <code>VD-1M-ABC123 30m</code> (Thêm 30 phút)\n"
            "• <code>VD-1M-ABC123 2h</code> (Thêm 2 giờ)\n"
            "• <code>VD-1M-ABC123 30d</code> (Thêm 30 ngày)"
        )
        bot.register_next_step_handler(msg, process_extend_key)
        return

    elif data == "menu_stats":
        show_stats(call.message.chat.id, call.message.message_id)
        return

    elif data == "menu_online_stats":
        show_online_stats(call.message.chat.id, call.message.message_id)
        return

    elif data == "menu_backup_data":
        safe_send_message(call.message.chat.id, "⏳ <i>Đang đóng gói và xuất file sao lưu dữ liệu...</i>")
        send_backup_data(call.message.chat.id, is_auto=False)
        return

    elif data == "menu_settings":
        cfg = load_bot_config()
        db_url = cfg.get('firebase_url') or 'Chưa cấu hình (Đang dùng Local DB)'
        text = (
            "⚙ <b>CẤU HÌNH HỆ THỐNG BẢN QUYỀN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <b>Firebase Database:</b> <code>{html.escape(db_url)}</code>\n"
            f"👑 <b>Admin IDs:</b> <code>{cfg.get('admin_ids')}</code>\n"
            f"🤖 <b>User ID của bạn:</b> <code>{call.from_user.id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Để cập nhật Firebase URL hoặc thêm Admin, hãy chỉnh sửa file bot_license/config.json.</i>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Quay lại Menu", callback_data="main_menu"))
        safe_edit_message(call.message.chat.id, call.message.message_id, text, reply_markup=markup)
        return

    # Action Handlers on Key
    elif data.startswith("act_reset_"):
        key = data.replace("act_reset_", "")
        reset_hwid_for_key(call.message.chat.id, key)
        show_key_detail(call.message.chat.id, key)
        return

    elif data.startswith("act_ext_"):
        key = data.replace("act_ext_", "")
        text = f"⏳ <b>GIA HẠN CHO KEY:</b> <code>{html.escape(key)}</code>\nChọn gói gia hạn bên dưới:"
        safe_edit_message(call.message.chat.id, call.message.message_id, text, reply_markup=get_extend_options_markup(key))
        return

    elif data.startswith("do_ext_"):
        # Format: do_ext_{key}_{dur}
        parts = data.split("_")
        dur_str = parts[-1]
        key = "_".join(parts[2:-1])
        delta, label, _ = parse_custom_duration_and_note(dur_str)
        if delta:
            execute_extend_key_delta(call.message.chat.id, key, delta, label)
            show_key_detail(call.message.chat.id, key)
        return

    elif data.startswith("custom_ext_"):
        key = data.replace("custom_ext_", "")
        msg = safe_send_message(
            call.message.chat.id,
            f"✏ <b>Nhập thời gian muốn gia hạn cho key <code>{html.escape(key)}</code>:</b>\n"
            "<i>(Ví dụ: <code>30p</code>, <code>2h</code>, <code>5 ngày</code>, <code>30d</code>)</i>"
        )
        bot.register_next_step_handler(msg, lambda m: process_custom_extend_days(m, key))
        return

    elif data.startswith("act_toggleban_"):
        key = data.replace("act_toggleban_", "")
        toggle_ban_key(call.message.chat.id, key)
        show_key_detail(call.message.chat.id, key)
        return

    elif data.startswith("act_delask_"):
        key = data.replace("act_delask_", "")
        text = (
            f"⚠ <b>XÁC NHẬN XÓA KEY:</b> <code>{html.escape(key)}</code>\n\n"
            "<i>Sau khi xóa, key này sẽ bị hủy vĩnh viễn khỏi hệ thống và không thể khôi phục!</i>\n"
            "Bạn có chắc chắn muốn xóa không?"
        )
        markup = types.InlineKeyboardMarkup()
        b_yes = types.InlineKeyboardButton("🗑 Có, Xóa Ngay", callback_data=f"act_delyes_{key}")
        b_no = types.InlineKeyboardButton("❌ Không, Quay Lại", callback_data=f"view_key_{key}")
        markup.add(b_yes, b_no)
        safe_edit_message(call.message.chat.id, call.message.message_id, text, reply_markup=markup)
        return

    elif data.startswith("act_delyes_"):
        key = data.replace("act_delyes_", "")
        execute_delete_key(call.message.chat.id, key)
        return

# ==================== HWID HANDLING ====================

def handle_hwid_detected(chat_id, hwid: str, message_id=None):
    clean_hwid = hwid.strip()
    if clean_hwid.startswith("/"): return

    existing_key = storage.get_key_by_hwid(clean_hwid)
    if existing_key:
        k_code = existing_key.get("key", "")
        status = existing_key.get("status", "active")
        status_str = "🟢 Đang hoạt động" if status == "active" else "🚫 Bị khóa"
        exp_str = existing_key.get("expires_at", "Chưa rõ")
        pkg = existing_key.get("package", "")

        text = (
            "💻 <b>ĐÃ NHẬN DIỆN MÃ THIẾT BỊ (HWID)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥 <b>Mã Máy:</b> <code>{html.escape(clean_hwid)}</code>\n"
            f"🔑 <b>Key Đang Gắn:</b> <code>{html.escape(k_code)}</code>\n"
            f"📦 <b>Gói:</b> {html.escape(pkg)} ({existing_key.get('duration_days', 0)} ngày)\n"
            f"🚦 <b>Trạng thái:</b> {status_str}\n"
            f"⏳ <b>Hạn dùng đến:</b> <code>{html.escape(exp_str)}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Chọn thao tác bên dưới:</i>"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⏳ Gia Hạn Cho Máy Này", callback_data=f"act_ext_{k_code}"))
        markup.add(types.InlineKeyboardButton("🔄 Reset Đổi Máy Mới", callback_data=f"act_reset_{k_code}"))
        markup.add(types.InlineKeyboardButton("🔍 Xem Chi Tiết Key", callback_data=f"view_key_{k_code}"))
        markup.add(types.InlineKeyboardButton("➕ Cấp Gói Mới Cho Máy", callback_data=f"genfor_{clean_hwid}_custom"))
        markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))
    else:
        text = (
            "💻 <b>ĐÃ NHẬN DIỆN MÃ THIẾT BỊ (HWID) CỦA KHÁCH:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥 <b>Mã Thiết Bị:</b> <code>{html.escape(clean_hwid)}</code>\n\n"
            "✨ <b>Thiết bị này chưa kích hoạt bản quyền.</b>\n"
            "<i>Vui lòng bấm chọn gói bên dưới để <b>KÍCH HOẠT NGAY</b> cho máy tính này:</i>"
        )
        markup = get_gen_package_markup(target_hwid=clean_hwid)

    if message_id:
        safe_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, text, reply_markup=markup)

def create_and_bind_key_for_hwid(chat_id, target_hwid: str, package_type: str, delta: datetime.timedelta, pkg_name: str, note: str = ""):
    key_code = make_key_code(package_type)
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    exp_dt = now + delta
    exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

    days_float = round(delta.total_seconds() / 86400, 2)

    key_data = {
        "key": key_code,
        "type": "paid",
        "package": package_type,
        "duration_label": pkg_name,
        "duration_days": days_float,
        "status": "active",
        "hwid": target_hwid.strip(),
        "device_name": f"PC-{target_hwid[-4:]}",
        "created_at": now_str,
        "activated_at": now_str,
        "expires_at": exp_str,
        "last_seen": now_str,
        "note": note
    }

    saved = storage.save_key(key_data)
    storage.save_device_license(target_hwid.strip(), key_data)

    signed_token = generate_signed_license_token(
        hwid=target_hwid.strip(),
        key_code=key_code,
        package=package_type,
        duration_days=days_float,
        duration_label=pkg_name,
        expires_at=exp_str,
        created_at=now_str,
        note=note
    )

    if saved:
        text = (
            "🎉 <b>KÍCH HOẠT BẢN QUYỀN THÀNH CÔNG!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💻 <b>Mã Thiết Bị (HWID):</b> <code>{html.escape(target_hwid)}</code>\n"
            f"📦 <b>Gói:</b> {pkg_name} ({days_float} ngày)\n"
            f"⏳ <b>Hạn dùng đến:</b> <code>{exp_str}</code>\n"
            f"🔑 <b>Mã Quản Lý (Key):</b> <code>{key_code}</code>\n"
            f"📝 <b>Ghi chú:</b> {html.escape(note or 'Gói ' + pkg_name)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 <b>MÃ KÍCH HOẠT CHO KHÁCH (CHẠM ĐỂ COPY):</b>\n\n"
            f"<code>{signed_token}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>HƯỚNG DẪN GỬI KHÁCH:</b>\n"
            "Gửi đoạn mã <code>LIC-...</code> bên trên cho khách. Khách mở Tool dán vào là <b>KÍCH HOẠT DÙNG ĐƯỢC NGAY 100% TRÊN MÁY KHÁCH</b> (Khóa đúng máy khách, không thể chia sẻ sang máy khác)!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⏳ Gia Hạn Thêm Thời Gian", callback_data=f"act_ext_{key_code}"))
        markup.add(types.InlineKeyboardButton("📋 Danh Sách Key", callback_data="menu_list_0_all"))
        markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))
        safe_send_message(chat_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, "❌ <b>Lỗi: Không thể lưu thông tin kích hoạt vào cơ sở dữ liệu!</b>")

def process_custom_gen_for_hwid(message, hwid: str):
    text = message.text.strip()
    if text.startswith("/"): return
    
    delta, label, note = parse_custom_duration_and_note(text)
    if not delta:
        safe_send_message(
            message.chat.id,
            "❌ <b>Thời gian không hợp lệ!</b>\n"
            "<i>Ví dụ bạn có thể nhập:</i>\n"
            "• <code>30p</code> hoặc <code>30 phút</code>\n"
            "• <code>5p</code> hoặc <code>5 phút Test</code>\n"
            "• <code>2h</code> hoặc <code>2 giờ Demo</code>\n"
            "• <code>3 ngày</code> hoặc <code>45 Khach Nguyen Van A</code>"
        )
        return

    create_and_bind_key_for_hwid(message.chat.id, hwid, "custom", delta, label, note=note)

# ==================== CORE BUSINESS LOGIC ====================

def create_and_send_key(chat_id, package_type, delta: datetime.timedelta, pkg_name: str, note: str = ""):
    key_code = make_key_code(package_type)
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    days_float = round(delta.total_seconds() / 86400, 2)

    exp_dt = now + delta
    exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

    key_data = {
        "key": key_code,
        "type": "paid",
        "package": package_type,
        "duration_label": pkg_name,
        "duration_days": days_float,
        "status": "active",
        "hwid": "",
        "device_name": "",
        "created_at": now_str,
        "activated_at": "",
        "expires_at": "",
        "last_seen": "",
        "note": note
    }

    saved = storage.save_key(key_data)

    signed_token = generate_signed_license_token(
        hwid="ANY",
        key_code=key_code,
        package=package_type,
        duration_days=days_float,
        duration_label=pkg_name,
        expires_at=exp_str,
        created_at=now_str,
        note=note
    )

    if saved:
        clean_note = html.escape(note or "Không có")
        text = (
            "🎉 <b>TẠO KEY BẢN QUYỀN THÀNH CÔNG!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 <b>Mã Key:</b> <code>{key_code}</code>\n"
            f"📦 <b>Thời hạn:</b> {pkg_name} ({days_float} ngày)\n"
            f"📅 <b>Ngày tạo:</b> <code>{now_str}</code>\n"
            f"📝 <b>Ghi chú:</b> {clean_note}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 <b>MÃ KÍCH HOẠT TOÀN NĂNG (GỬI CHO KHÁCH):</b>\n\n"
            f"<code>{signed_token}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>HƯỚNG DẪN:</b>\n"
            "Gửi mã <code>LIC-...</code> trên cho khách. Máy nào dán vào kích hoạt đầu tiên sẽ <b>TỰ ĐỘNG KHÓA VÀO MÁY ĐÓ</b> và sử dụng ngay lập tức!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Cấp Thêm Key Khác", callback_data="menu_gen_key"))
        markup.add(types.InlineKeyboardButton("📋 Danh Sách Key", callback_data="menu_list_0_all"))
        markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))
        safe_send_message(chat_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, "❌ <b>Lỗi: Không thể lưu Key vào cơ sở dữ liệu!</b>")

def process_custom_gen_key(message):
    text = message.text.strip()
    if text.startswith("/"): return
    
    delta, label, note = parse_custom_duration_and_note(text)
    if not delta:
        safe_send_message(
            message.chat.id,
            "❌ <b>Thời gian không hợp lệ!</b>\n"
            "<i>Ví dụ bạn có thể nhập:</i>\n"
            "• <code>30 phút</code> hoặc <code>30p</code>\n"
            "• <code>5p</code> hoặc <code>5 phút Khach Nam</code>\n"
            "• <code>2 giờ</code> hoặc <code>2h Test Tool</code>\n"
            "• <code>3 ngày</code> hoặc <code>45 Khach Nguyen Van A</code>\n"
            "• <code>1</code> (1 ngày)"
        )
        return

    create_and_send_key(message.chat.id, "custom", delta, label, note=note)

def process_search_key(message):
    query = message.text.strip()
    if query.startswith("/"): return
    
    if is_hwid_format(query):
        handle_hwid_detected(message.chat.id, query)
        return

    keys = storage.list_all_keys()
    matches = []
    q_lower = query.lower()
    for k in keys:
        if (q_lower in str(k.get("key", "")).lower() or 
            q_lower in str(k.get("hwid", "")).lower() or 
            q_lower in str(k.get("device_name", "")).lower() or 
            q_lower in str(k.get("note", "")).lower()):
            matches.append(k)

    if not matches:
        safe_send_message(message.chat.id, f"❌ Không tìm thấy Key nào phù hợp với từ khóa: <code>{html.escape(query)}</code>")
        return

    if len(matches) == 1:
        show_key_detail(message.chat.id, matches[0].get("key"))
    else:
        text = f"🔍 <b>Tìm thấy {len(matches)} kết quả phù hợp:</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for k in matches[:10]:
            k_code = k.get("key")
            pkg = k.get("duration_label") or k.get("package", "")
            status = "🟢" if k.get("status") == "active" else "🔴"
            btn_text = f"{status} {k_code} ({pkg}) - {k.get('note', '')[:15]}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_key_{k_code}"))
        markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))
        safe_send_message(message.chat.id, text, reply_markup=markup)

def show_key_detail(chat_id, key_code: str, message_id=None):
    data = storage.get_key(key_code)
    if not data:
        safe_send_message(chat_id, f"❌ Không tìm thấy mã Key <code>{html.escape(key_code)}</code>!")
        return

    status = data.get("status", "active")
    status_icon = "🟢 Đang hoạt động" if status == "active" else "🚫 Bị Khóa (Ban)"
    hwid = data.get("hwid") or "🔓 Chưa kích hoạt (Chưa gán máy)"
    dev_name = data.get("device_name") or "Chưa có"
    created_at = data.get("created_at") or "Chưa rõ"
    act_at = data.get("activated_at") or "Chưa kích hoạt"
    exp_at = data.get("expires_at") or "Chưa tính (Đợi kích hoạt)"
    last_seen = data.get("last_seen") or "Chưa có dữ liệu"
    note = html.escape(data.get("note", "") or "Không có")
    dur_label = data.get("duration_label") or f"{data.get('duration_days', 0)} ngày"

    now = datetime.datetime.now()
    exp_dt = parse_iso_time(exp_at)
    time_left_str = ""
    if exp_dt:
        if exp_dt < now:
            time_left_str = " (❌ Đã Hết Hạn)"
        else:
            diff = exp_dt - now
            if diff.days > 0:
                time_left_str = f" (Còn {diff.days} ngày {diff.seconds // 3600}h)"
            elif diff.seconds >= 3600:
                time_left_str = f" (Còn {diff.seconds // 3600}h {(diff.seconds % 3600) // 60}p)"
            else:
                time_left_str = f" (Còn {max(1, diff.seconds // 60)} phút)"

    signed_token = generate_signed_license_token(
        hwid=hwid if hwid and "Chưa" not in hwid else "ANY",
        key_code=key_code,
        package=data.get("package", "custom"),
        duration_days=data.get("duration_days", 30),
        duration_label=dur_label,
        expires_at=exp_at if "Chưa" not in exp_at else "",
        created_at=created_at if "Chưa" not in created_at else None,
        note=data.get("note", "")
    )

    text = (
        "🔑 <b>THÔNG TIN CHI TIẾT KEY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 <b>Mã Key:</b> <code>{html.escape(data.get('key', ''))}</code>\n"
        f"📦 <b>Thời hạn:</b> {html.escape(dur_label)}\n"
        f"🚦 <b>Trạng thái:</b> {status_icon}\n"
        f"💻 <b>Mã máy (HWID):</b> <code>{html.escape(hwid)}</code>\n"
        f"🖥 <b>Tên thiết bị:</b> {html.escape(dev_name)}\n"
        f"📅 <b>Ngày tạo:</b> <code>{html.escape(created_at)}</code>\n"
        f"🚀 <b>Kích hoạt lúc:</b> <code>{html.escape(act_at)}</code>\n"
        f"⏳ <b>Hạn dùng đến:</b> <code>{html.escape(exp_at)}</code>{time_left_str}\n"
        f"🟢 <b>Online lần cuối:</b> <code>{html.escape(last_seen)}</code>\n"
        f"📝 <b>Ghi chú:</b> {note}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>Mã Kích Hoạt Ký Số Cho Khách:</b>\n"
        f"<code>{signed_token}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    markup = get_key_action_markup(key_code, status)
    if message_id:
        safe_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, text, reply_markup=markup)

def process_reset_hwid(message):
    key = message.text.strip()
    if key.startswith("/"): return
    reset_hwid_for_key(message.chat.id, key)

def reset_hwid_for_key(chat_id, key):
    data = storage.get_key(key)
    if not data:
        safe_send_message(chat_id, f"❌ Không tìm thấy mã Key <code>{html.escape(key)}</code>!")
        return

    old_hwid = data.get("hwid", "")
    success = storage.update_key_fields(key, {"hwid": "", "device_name": ""})
    if old_hwid:
        try: storage.delete_trial(old_hwid)
        except Exception: pass

    if success:
        safe_send_message(
            chat_id,
            f"✔ <b>Đã Reset Thiết Bị (HWID) thành công!</b>\n"
            f"🔑 Key: <code>{html.escape(key)}</code>\n"
            f"💡 <i>Khách hàng có thể mở tool trên máy tính mới và nhập mã key này để tiếp tục sử dụng.</i>"
        )
    else:
        safe_send_message(chat_id, "❌ Lỗi khi cập nhật cơ sở dữ liệu.")

def process_extend_key(message):
    text = message.text.strip()
    if text.startswith("/"): return

    # If the user typed "VD-1M-ABC 30m" -> Direct extend
    parts = text.split(maxsplit=1)
    if len(parts) >= 2:
        target = parts[0].strip().upper()
        delta, label, _ = parse_custom_duration_and_note(parts[1])
        if delta:
            execute_extend_key_delta(message.chat.id, target, delta, label)
            return

    target = text.strip().upper()
    data = storage.get_key(target)
    if not data and is_hwid_format(target):
        data = storage.get_key_by_hwid(target)

    text_out = (
        f"✏ <b>Nhập số ngày sử dụng cho máy <code>{html.escape(target)}</code>:</b>\n"
        f"<i>(Ví dụ: <code>45</code> hoặc <code>45 Khach Nguyen Van A</code> hoặc <code>30p</code>)</i>"
    )

    if data:
        key_code = data.get("key", target)
        markup = get_extend_options_markup(key_code)
        safe_send_message(message.chat.id, text_out, reply_markup=markup)
    else:
        markup = get_gen_package_markup(target_hwid=target)
        safe_send_message(message.chat.id, text_out, reply_markup=markup)

def process_custom_extend_days(message, key: str):
    text = message.text.strip()
    if text.startswith("/"): return
    delta, label, _ = parse_custom_duration_and_note(text)
    if not delta:
        safe_send_message(message.chat.id, "❌ Vui lòng nhập thời gian hợp lệ (Ví dụ: 30p, 2h, 5 ngày, 30d).")
        return
    execute_extend_key_delta(message.chat.id, key, delta, label)
    show_key_detail(message.chat.id, key)

def execute_extend_key_delta(chat_id, target: str, delta: datetime.timedelta, label: str):
    data = storage.get_key(target)
    if not data and is_hwid_format(target):
        data = storage.get_key_by_hwid(target)

    if not data:
        safe_send_message(chat_id, f"❌ Không tìm thấy Key hoặc Thiết Bị <code>{html.escape(target)}</code>!")
        return

    key = data.get("key", target)
    now = datetime.datetime.now()
    exp_str = data.get("expires_at", "")
    exp_dt = parse_iso_time(exp_str)

    if exp_dt and exp_dt > now:
        new_exp = exp_dt + delta
    else:
        new_exp = now + delta

    new_exp_str = new_exp.strftime("%Y-%m-%d %H:%M:%S")
    updated = storage.update_key_fields(key, {
        "expires_at": new_exp_str,
        "status": "active"
    })

    hwid = data.get("hwid")
    if hwid:
        data["expires_at"] = new_exp_str
        data["status"] = "active"
        storage.save_device_license(hwid, data)

    signed_token = generate_signed_license_token(
        hwid=hwid or "ANY",
        key_code=key,
        package=data.get("package", "custom"),
        duration_days=data.get("duration_days", 30),
        duration_label=data.get("duration_label", "Gia hạn"),
        expires_at=new_exp_str,
        note=data.get("note", "")
    )

    if updated:
        safe_send_message(
            chat_id,
            f"🎉 <b>ĐÃ GIA HẠN THÀNH CÔNG (+{label})!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 <b>Key:</b> <code>{html.escape(key)}</code>\n"
            f"💻 <b>Mã máy:</b> <code>{html.escape(hwid or 'Chưa gán')}</code>\n"
            f"⏳ <b>Hạn dùng mới đến:</b> <code>{new_exp_str}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 <b>MÃ KÍCH HOẠT MỚI CHO KHÁCH (CHẠM ĐỂ COPY):</b>\n\n"
            f"<code>{signed_token}</code>\n\n"
            "<i>(Gửi mã này cho khách để cập nhật thời hạn trên máy của họ)</i>"
        )
    else:
        safe_send_message(chat_id, "❌ Lỗi khi cập nhật thời hạn trên cơ sở dữ liệu.")

def toggle_ban_key(chat_id, key: str):
    data = storage.get_key(key)
    if not data:
        safe_send_message(chat_id, f"❌ Không tìm thấy Key <code>{html.escape(key)}</code>!")
        return

    curr_status = data.get("status", "active")
    new_status = "banned" if curr_status == "active" else "active"
    storage.update_key_fields(key, {"status": new_status})
    
    hwid = data.get("hwid")
    if hwid:
        data["status"] = new_status
        storage.save_device_license(hwid, data)

    msg = "🚫 <b>ĐÃ KHÓA (BAN) Key</b>" if new_status == "banned" else "🟢 <b>ĐÃ MỞ KHÓA Key</b>"
    safe_send_message(chat_id, f"{msg} <code>{html.escape(key)}</code> thành công!\n<i>Khách hàng đang mở Tool hoặc mở lại Tool sẽ bị khóa ngay lập tức.</i>")

def set_key_ban_status(chat_id, key: str, is_ban: bool):
    data = storage.get_key(key)
    if not data:
        safe_send_message(chat_id, f"❌ Không tìm thấy Key <code>{html.escape(key)}</code>!")
        return
    new_status = "banned" if is_ban else "active"
    storage.update_key_fields(key, {"status": new_status})
    
    hwid = data.get("hwid")
    if hwid:
        data["status"] = new_status
        storage.save_device_license(hwid, data)

    msg = "🚫 <b>Đã Khóa Key</b>" if is_ban else "🟢 <b>Đã Mở Khóa Key</b>"
    safe_send_message(chat_id, f"{msg} <code>{html.escape(key)}</code> thành công!")

def execute_delete_key(chat_id, key: str):
    data = storage.get_key(key)
    hwid = data.get("hwid", "") if data else ""
    deleted = storage.delete_key(key)
    if hwid:
        try: storage.delete_trial(hwid)
        except: pass

    if deleted:
        safe_send_message(
            chat_id,
            f"🗑 <b>Đã XÓA VĨNH VIỄN Key:</b> <code>{html.escape(key)}</code> khỏi hệ thống!"
        )
    else:
        safe_send_message(chat_id, f"❌ Không thể xóa mã Key <code>{html.escape(key)}</code>!")

# ==================== LIST & PAGINATION ====================

def show_keys_list(chat_id, message_id=None, page=0, filter_type="all"):
    all_keys = storage.list_all_keys()
    if not all_keys:
        text = "ℹ Chưa có mã Key nào trong cơ sở dữ liệu."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Cấp Key Đầu Tiên", callback_data="menu_gen_key"))
        markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))
        if message_id:
            safe_edit_message(chat_id, message_id, text, reply_markup=markup)
        else:
            safe_send_message(chat_id, text, reply_markup=markup)
        return

    now = datetime.datetime.now()
    filtered_keys = []

    for k in all_keys:
        status = k.get("status", "active")
        hwid = k.get("hwid", "")
        exp_dt = parse_iso_time(k.get("expires_at", ""))
        is_expired = bool(exp_dt and exp_dt < now)

        if filter_type == "active" and (status != "active" or is_expired or not hwid):
            continue
        elif filter_type == "unused" and hwid:
            continue
        elif filter_type == "expired" and not is_expired:
            continue
        elif filter_type == "banned" and status != "banned":
            continue
        filtered_keys.append(k)

    filtered_keys.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

    total_items = len(filtered_keys)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_items = filtered_keys[start_idx:end_idx]

    filter_names = {
        "all": "Tất Cả",
        "active": "Đang Dùng",
        "unused": "Chưa Kích Hoạt",
        "expired": "Hết Hạn",
        "banned": "Bị Khóa"
    }

    text = (
        f"📋 <b>DANH SÁCH BẢN QUYỀN</b> ({filter_names.get(filter_type, 'Tất Cả')})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Tổng cộng: {total_items} Keys | Trang {page+1}/{total_pages}</i>\n\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    for k in page_items:
        k_code = k.get("key", "")
        pkg = k.get("duration_label") or k.get("package", "")
        status = k.get("status", "active")
        hwid = k.get("hwid", "")
        exp_dt = parse_iso_time(k.get("expires_at", ""))
        is_expired = bool(exp_dt and exp_dt < now)

        if status == "banned":
            icon = "🚫"
        elif is_expired:
            icon = "⏳"
        elif hwid:
            icon = "🟢"
        else:
            icon = "🔓"

        note = k.get("note", "")
        note_str = f" - {note[:12]}" if note else ""
        btn_text = f"{icon} {k_code} ({pkg}){note_str}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_key_{k_code}"))

    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton("⬅ Trước", callback_data=f"menu_list_{page-1}_{filter_type}"))
    nav_row.append(types.InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(types.InlineKeyboardButton("Sau ➡", callback_data=f"menu_list_{page+1}_{filter_type}"))
    markup.row(*nav_row)

    f_row = [
        types.InlineKeyboardButton("Tất Cả", callback_data=f"menu_list_0_all"),
        types.InlineKeyboardButton("🟢 Đang Dùng", callback_data=f"menu_list_0_active"),
        types.InlineKeyboardButton("🔓 Trống", callback_data=f"menu_list_0_unused"),
        types.InlineKeyboardButton("⏳ Hết Hạn", callback_data=f"menu_list_0_expired")
    ]
    markup.row(*f_row)

    markup.add(types.InlineKeyboardButton("🔍 Tìm Kiếm Key", callback_data="menu_search_key"))
    markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))

    if message_id:
        safe_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, text, reply_markup=markup)

# ==================== STATISTICS ====================

def show_stats(chat_id, message_id=None):
    keys = storage.list_all_keys()
    total = len(keys)
    now = datetime.datetime.now()

    active_count = 0
    expired_count = 0
    unused_count = 0
    banned_count = 0

    pkg_counts = {}

    for k in keys:
        status = k.get("status", "active")
        hwid = k.get("hwid", "")
        exp_dt = parse_iso_time(k.get("expires_at", ""))
        pkg = k.get("duration_label") or k.get("package", "Tùy chỉnh")
        pkg_counts[pkg] = pkg_counts.get(pkg, 0) + 1

        if status == "banned":
            banned_count += 1
        elif not hwid:
            unused_count += 1
        elif exp_dt and exp_dt < now:
            expired_count += 1
        else:
            active_count += 1

    trials = storage.list_all_trials()
    total_trials = len(trials)
    active_trials = sum(1 for t in trials if (parse_iso_time(t.get("expires_at", "")) or now) > now)

    text = (
        "📊 <b>THỐNG KÊ TOÀN DIỆN HỆ THỐNG KEY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 <b>BẢN QUYỀN CHÍNH THỨC:</b>\n"
        f"🔑 Tổng số Key đã tạo: <code>{total}</code>\n"
        f"🟢 Key đang hoạt động: <code>{active_count}</code>\n"
        f"🔓 Key chưa kích hoạt (Trống): <code>{unused_count}</code>\n"
        f"⏳ Key đã hết hạn: <code>{expired_count}</code>\n"
        f"🚫 Key bị khóa (Ban): <code>{banned_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>PHÂN BỔ THEO GÓI:</b>\n"
    )

    for p_label, count in sorted(pkg_counts.items(), key=lambda x: x[1], reverse=True):
        text += f"• {p_label}: <code>{count}</code>\n"

    text += (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>DÙNG THỬ MIỄN PHÍ:</b>\n"
        f"📱 Tổng thiết bị đăng ký: <code>{total_trials}</code>\n"
        f"🟢 Đang trong hạn dùng thử: <code>{active_trials}</code>\n"
        f"⏳ Đã hết hạn dùng thử: <code>{total_trials - active_trials}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🟢 Xem Thống Kê Online", callback_data="menu_online_stats"))
    markup.add(types.InlineKeyboardButton("📋 Xem Danh Sách Key", callback_data="menu_list_0_all"))
    markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))

    if message_id:
        safe_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, text, reply_markup=markup)

def show_online_stats(chat_id, message_id=None):
    keys = storage.list_all_keys()
    trials = storage.list_all_trials()
    now = datetime.datetime.now()

    today_str = now.strftime("%Y-%m-%d")
    this_month_str = now.strftime("%Y-%m")
    this_year_str = now.strftime("%Y")

    online_15m = 0
    online_today = 0
    online_month = 0
    online_year = 0

    all_records = []
    for k in keys:
        if k.get("last_seen"):
            all_records.append({
                "type": "Key",
                "id": k.get("key"),
                "name": k.get("device_name") or k.get("hwid", "")[:12],
                "last_seen": k.get("last_seen"),
                "package": k.get("duration_label") or k.get("package", "")
            })
    for t in trials:
        if t.get("last_seen"):
            all_records.append({
                "type": "Trial",
                "id": t.get("hwid", "")[:10],
                "name": t.get("device_name") or t.get("hwid", "")[:12],
                "last_seen": t.get("last_seen"),
                "package": "Dùng Thử"
            })

    for r in all_records:
        ls_str = str(r["last_seen"]).strip()
        ls_dt = parse_iso_time(ls_str)
        if not ls_dt: continue

        diff_seconds = (now - ls_dt).total_seconds()

        if diff_seconds <= 15 * 60:
            online_15m += 1
        if ls_str.startswith(today_str):
            online_today += 1
        if ls_str.startswith(this_month_str):
            online_month += 1
        if ls_str.startswith(this_year_str):
            online_year += 1

    all_records.sort(key=lambda x: str(x["last_seen"]), reverse=True)
    top_active = all_records[:8]

    text = (
        "🟢 <b>THỐNG KÊ NGƯỜI DÙNG & THIẾT BỊ ONLINE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Đang Online (15 phút qua):</b> <code>{online_15m}</code> người/thiết bị\n"
        f"📅 <b>Online Hôm Nay ({today_str}):</b> <code>{online_today}</code> người\n"
        f"📆 <b>Online Tháng Này ({this_month_str}):</b> <code>{online_month}</code> người\n"
        f"📊 <b>Online Năm Này ({this_year_str}):</b> <code>{online_year}</code> người\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💻 <b>THIẾT BỊ HOẠT ĐỘNG GẦN ĐÂY:</b>\n"
    )

    if not top_active:
        text += "<i>Chưa ghi nhận lượt online nào từ các thiết bị.</i>\n"
    else:
        for item in top_active:
            t_icon = "👑" if item["type"] == "Key" else "🎁"
            text += f"{t_icon} <b>{html.escape(item['id'])}</b> ({html.escape(item['name'])})\n   ⏱ <code>{item['last_seen']}</code>\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Làm Mới Thống Kê", callback_data="menu_online_stats"))
    markup.add(types.InlineKeyboardButton("📊 Thống Kê Tổng Quan", callback_data="menu_stats"))
    markup.add(types.InlineKeyboardButton("🏠 Menu Chính", callback_data="main_menu"))

    if message_id:
        safe_edit_message(chat_id, message_id, text, reply_markup=markup)
    else:
        safe_send_message(chat_id, text, reply_markup=markup)

# ==================== BACKUP SYSTEM ====================

def send_backup_data(chat_id=None, is_auto=False):
    """
    Exports the local database file (and/or cloud data),
    compiles a clean readable summary, and sends it directly to Admin Telegram.
    """
    keys = storage.list_all_keys()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    
    total = len(keys)
    active = sum(1 for k in keys if k.get("status") == "active")
    banned = sum(1 for k in keys if k.get("status") == "banned")
    devices = sum(1 for k in keys if k.get("hwid"))

    tag = "⏰ <b>BÁO CÁO SAO LƯU DỮ LIỆU TỰ ĐỘNG HÀNG NGÀY</b>" if is_auto else "💾 <b>SAO LƯU DỮ LIỆU BẢN QUYỀN (BACKUP)</b>"
    caption = (
        f"{tag}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Thời gian:</b> <code>{now_str}</code>\n"
        f"📊 <b>Tổng số Key:</b> <b>{total}</b> mã\n"
        f"🟢 <b>Đang hoạt động:</b> {active} | 🚫 <b>Đã khóa:</b> {banned}\n"
        f"💻 <b>Máy đã liên kết:</b> {devices} thiết bị\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📁 <i>File database <code>local_keys_db.json</code> đính kèm bên dưới chứa 100% toàn bộ thông tin Key & Thiết bị. Bạn có thể lưu lại file này để dự phòng an toàn tuyệt đối!</i>"
    )

    db_path = storage.local_db_path
    if not os.path.exists(db_path):
        alt_path = os.path.join(BASE_DIR, "local_keys_db.json")
        if os.path.exists(alt_path):
            db_path = alt_path

    # If in cloud mode or file not on disk, also generate an on-the-fly JSON file
    temp_json_path = None
    if not os.path.exists(db_path):
        try:
            temp_json_path = os.path.join(BASE_DIR, f"temp_backup_{date_str}.json")
            full_data = {"_devices": {}, **{k.get("key"): k for k in keys if k.get("key")}}
            with open(temp_json_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, indent=4, ensure_ascii=False)
            db_path = temp_json_path
        except Exception:
            pass

    recipients = [chat_id] if chat_id else ADMIN_IDS

    for cid in recipients:
        if not cid: continue
        try:
            if db_path and os.path.exists(db_path):
                with open(db_path, "rb") as f:
                    bot.send_document(
                        cid,
                        f,
                        caption=caption,
                        parse_mode="HTML",
                        visible_file_name=f"backup_keys_{date_str}.json"
                    )
            else:
                safe_send_message(cid, f"{caption}\n\n⚠️ <i>(Chưa có file database vật lý cục bộ)</i>")
        except Exception as e:
            print(f"[Backup] Error sending backup to {cid}: {e}")
            try:
                safe_send_message(cid, f"{caption}\n\n⚠️ Lỗi khi gửi file đính kèm: {e}")
            except Exception:
                pass

    if temp_json_path and os.path.exists(temp_json_path):
        try:
            os.remove(temp_json_path)
        except Exception:
            pass

def daily_backup_scheduler_worker():
    """
    Background worker that runs continuously and sends the database backup
    to all admins every day at 08:00 AM (Vietnam time).
    """
    last_sent_date = ""
    while True:
        try:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            
            # Send once every day at 08:00 AM
            if now.hour == 8 and last_sent_date != today_str:
                last_sent_date = today_str
                print(f"[DailyBackup] Triggering automated daily backup for {today_str}...")
                send_backup_data(is_auto=True)
                
            time.sleep(30)
        except Exception as e:
            print(f"[DailyBackup] Scheduler error: {e}")
            time.sleep(60)

# ==================== MAIN RUNNER ====================

def start_bot_polling():
    print("=" * 60)
    print("🚀 TELEGRAM KEY BOT QUẢN TRỊ BẢN QUYỀN ĐANG KHỞI CHẠY...")
    if storage.is_cloud_enabled():
        print(f"🌐 Chế độ: Firebase Cloud Realtime DB ({storage.firebase_url})")
    else:
        print("📁 Chế độ: Database Cục Bộ (Local JSON DB)")
    print("=" * 60)
    
    try:
        bot.remove_webhook()
    except Exception:
        pass

    # Start automated daily backup scheduler in background
    threading.Thread(target=daily_backup_scheduler_worker, daemon=True).start()
    print("⏰ Đã kích hoạt luồng Tự Động Sao Lưu Dữ Liệu Hàng Ngày (Auto Daily Backup lúc 08:00 AM)")

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"⚠️ Đang duy trì kết nối Bot: {e}")
            time.sleep(3)

if __name__ == "__main__":
    start_bot_polling()
