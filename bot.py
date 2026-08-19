import telebot
from telebot import types
import sqlite3
import os

# Telegram Bot Token va Admin ID
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = 811276490  # Sizning Telegram ID'ingiz

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 1. MA'LUMOTLAR BAZASI (SQLITE)
# ==========================================

def get_db():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            referrer_id INTEGER,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Vazifalar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            link TEXT,
            required_subs INTEGER,
            completed_subs INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Bajarilgan vazifalar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. YORDAMCHI FUNKSIYALAR
# ==========================================

def register_user(user_id, username, referrer_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    is_new = False
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, balance, referrer_id) VALUES (?, ?, ?, ?)",
            (user_id, username, 0.0, referrer_id)
        )
        conn.commit()
        is_new = True
        
    conn.close()
    return is_new

def get_balance(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["balance"] if row else 0.0

def update_balance(user_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ==========================================
# 3. MENYU TUGMALARI
# ==========================================

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎯 Vazifa bajarish"),
        types.KeyboardButton("💰 Balansim"),
        types.KeyboardButton("📢 Post qilish"),
        types.KeyboardButton("🏆 Reyting"),
        types.KeyboardButton("👤 Profilim"),
        types.KeyboardButton("🎁 Kunlik bonus"),
        types.KeyboardButton("🤝 Taklif qilish"),
        types.KeyboardButton("ℹ️ Qoidalar")
    )
    return markup

# ==========================================
# 4. HANDLERLAR (AMALLAR)
# ==========================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Referal ID'sini tekshirish (/start 123456)
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    is_new = register_user(user_id, username, referrer_id)
    
    # Yangi foydalanuvchi bo'lsa va taklif qilgan odam bo'lsa
    if is_new and referrer_id and referrer_id != user_id:
        update_balance(referrer_id, 10.0) # Referal uchun 10 tanga
        try:
            bot.send_message(referrer_id, "🎉 Siz taklif qilgan do'stingiz botga qo'shildi! Sizga +10 tanga berildi.")
        except:
            pass

    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Instagram sahifalarga obuna bo'lib tanga ishlang va o me profilingizga obunachi to'plang.\n"
        "📌 **Narx:** 100 obunachi = 50 tanga"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "💰 Balansim")
def show_balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 Sizning balansingiz: **{bal} tanga**", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Profilim")
def show_profile(message):
    user_id = message.from_user.id
    bal = get_balance(user_id)
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Ism: {message.from_user.first_name}\n"
        f"💰 Balans: **{bal} tanga**"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎁 Kunlik bonus")
def daily_bonus(message):
    user_id = message.from_user.id
    update_balance(user_id, 5.0)
    new_bal = get_balance(user_id)
    bot.send_message(
        message.chat.id, 
        f"🎁 Sizga **5 tanga** kunlik bonus berildi!\nHozirgi balansingiz: **{new_bal} tanga**", 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🤝 Taklif qilish")
def invite_friends(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    text = (
        "🤝 **Do'stlaringizni taklif qiling!**\n\n"
        f"Sizning taklif havolangiz:\n`{ref_link}`\n\n"
        "Har bir yangi do'stingiz uchun **10 tanga** beriladi!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def rating(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()
    conn.close()
    
    text = "🏆 **Eng ko'p tanga to'plaganlar:**\n\n"
    for idx, u in enumerate(users, start=1):
        uname = u["username"] or "Foydalanuvchi"
        text += f"{idx}. @{uname} — {u['balance']} tanga\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "ℹ️ Qoidalar")
def rules(message):
    text = "ℹ️ **Qoidalar:**\n\n1. Halol bo'ling.\n2. Obunani bekor qilmang.\n3. 100 obunachi = 50 tanga."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ==========================================
# 5. POST QILISH (VAZIFA JOYLASHTIRISH)
# ==========================================

@bot.message_handler(func=lambda m: m.text == "📢 Post qilish")
def start_post(message):
    msg = bot.send_message(message.chat.id, "Instagram sahifangiz havolasini yuboring (masalan: https://instagram.com/username):")
    bot.register_next_step_handler(msg, step_link)

def step_link(message):
    link = message.text.strip()
    if "instagram.com" not in link:
        bot.send_message(message.chat.id, "❌ Noto'g'ri havola. Qayta urinib ko'ring.")
        return
    
    bal = get_balance(message.from_user.id)
    msg = bot.send_message(
        message.chat.id, 
        f"Nechta obunachi kerak? (100 obunachi = 50 tanga)\nBalansingiz: **{bal} tanga**", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, step_count, link)

def step_count(message, link):
    user_id = message.from_user.id
    try:
        count = int(message.text)
        if count <= 0:
            bot.send_message(message.chat.id, "❌ Musbat son kiriting!")
            return
            
        required_coins = count * 0.5  # 100 obunachi = 50 tanga
        current_bal = get_balance(user_id)
        
        if current_bal < required_coins:
            bot.send_message(
                message.chat.id, 
                f"❌ Mablag' yetarli emas!\nKerak: **{required_coins} tanga**, sizda: **{current_bal} tanga**", 
                parse_mode="Markdown"
            )
        else:
            update_balance(user_id, -required_coins)
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (user_id, link, required_subs) VALUES (?, ?, ?)", (user_id, link, count))
            conn.commit()
            conn.close()
            
            bot.send_message(message.chat.id, f"✅ Vazifa yaratildi!\n{count} ta obunachi uchun **{required_coins} tanga** yechildi.", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Faqat raqam yuboring!")

# ==========================================
# 6. VAZIFA BAJARISH VA ADMIN BUYRUG'I
# ==========================================

@bot.message_handler(func=lambda m: m.text == "🎯 Vazifa bajarish")
def do_task(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE status = 'active' AND user_id != ? AND id NOT IN (
            SELECT task_id FROM completed_tasks WHERE user_id = ?
        ) LIMIT 1
    """, (user_id, user_id))
    task = cursor.fetchone()
    conn.close()
    
    if task:
        bot.send_message(message.chat.id, f"Ushbu sahifaga obuna bo'ling:\n{task['link']}")
    else:
        bot.send_message(message.chat.id, "Hozircha vazifalar yo'q. Keyinroq qayta urinib ko'ring.")

@bot.message_handler(commands=['addcoins'])
def add_coins_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        update_balance(int(target_id), float(amount))
        bot.send_message(message.chat.id, f"✅ `{target_id}` foydalanuvchiga {amount} tanga qo'shildi.")
    except:
        bot.send_message(message.chat.id, "Format: `/addcoins USER_ID TANGA`", parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()