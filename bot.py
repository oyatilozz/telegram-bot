import os
import sqlite3
import datetime
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN", "8964988664:AAHn4OnFl-huujz5gME5WvqT-yji6CWrAio")
ADMIN_ID = 811276490

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE (BAZA) =================
def get_db():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            referrer_id INTEGER,
            last_bonus TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= KEYBOARD (MENYU) =================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("🎯 Vazifa bajarish")
    btn2 = types.KeyboardButton("💰 Balansim")
    btn3 = types.KeyboardButton("📢 Post qilish")
    btn4 = types.KeyboardButton("🏆 Reyting")
    btn5 = types.KeyboardButton("👤 Profilim")
    btn6 = types.KeyboardButton("🎁 Kunlik bonus")
    btn7 = types.KeyboardButton("🤝 Taklif qilish")
    btn8 = types.KeyboardButton("ℹ️ Qoidalar")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    return markup

# ================= COMMANDS & HANDLERS =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username
    args = message.text.split()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        cursor.execute(
            "INSERT INTO users (user_id, username, balance, referrer_id) VALUES (?, ?, ?, ?)",
            (user_id, username, 0.0, referrer_id)
        )
        
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id = ?", (referrer_id,))
            try:
                bot.send_message(referrer_id, "🎉 Taklifingiz orqali yangi a'zo qo'shildi! Sizga +10 tanga berildi.")
            except:
                pass
        conn.commit()
    conn.close()
    
    bot.send_message(
        message.chat.id, 
        f"Assalomu alaykum, {message.from_user.first_name}!\nBotimizga xush kelibsiz.", 
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: "Balansim" in m.text or "Profilim" in m.text)
def show_balance(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    bal = row["balance"] if row else 0.0
    bot.send_message(
        message.chat.id, 
        f"👤 **Sizning profilingiz:**\n\n🆔 ID: `{user_id}`\n💰 Balansingiz: **{bal}** tanga", 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: "Reyting" in m.text)
def show_rating(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()
    conn.close()
    
    text = "🏆 **Eng ko'p tanga to'plagan foydalanuvchilar:**\n\n"
    for idx, u in enumerate(users, start=1):
        uname = f"@{u['username']}" if u['username'] else "Foydalanuvchi"
        text += f"{idx}. {uname} — {u['balance']} tanga\n"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: "Kunlik bonus" in m.text)
def daily_bonus(message):
    today = str(datetime.date.today())
    user_id = message.from_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row and row["last_bonus"] == today:
        bot.send_message(message.chat.id, "❌ Siz bugungi bonusni allaqachon olib bo'lgansiz. Ertaga qayta urinib ko'ring!")
    else:
        cursor.execute("UPDATE users SET balance = balance + 5, last_bonus = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "🎁 Tabriklaymiz! Sizga kunlik **5 tanga** bonus berildi!", parse_mode="Markdown")
    conn.close()

@bot.message_handler(func=lambda m: "Taklif qilish" in m.text)
def invite_link(message):
    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    bot.send_message(
        message.chat.id, 
        f"🤝 **Do'stlaringizni taklif qiling!**\n\nSizning shaxsiy havolangiz:\n{link}\n\nHar bir taklif qilingan do'stingiz uchun **10 tanga** olasiz!", 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: "Vazifa bajarish" in m.text)
def tasks(message):
    markup = types.InlineKeyboardMarkup()
    btn_channel = types.InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url="https://t.me/telegram")
    btn_check = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
    markup.add(btn_channel)
    markup.add(btn_check)
    
    bot.send_message(
        message.chat.id,
        "🎯 **Mavjud vazifalar:**\n\n1. Quyidagi kanalga obuna bo'ling va **✅ Tekshirish** tugmasini bosing.\n🎁 Mukofot: **10 tanga**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, "🎉 Vazifa bajarildi! +10 tanga qo'shildi.", show_alert=True)
    try:
        bot.edit_message_text(
            "✅ **Vazifa muvaffaqiyatli bajarildi!**\nSizga **10 tanga** berildi.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    except:
        pass

@bot.message_handler(func=lambda m: "Post qilish" in m.text)
def create_post(message):
    bot.send_message(message.chat.id, "📢 Obunachi yig'ish uchun post yaratish xizmati tez orada ishga tushadi.")

@bot.message_handler(func=lambda m: "Qoidalar" in m.text)
def rules(message):
    bot.send_message(
        message.chat.id, 
        "ℹ️ **Bot qoidalari:**\n1. Botdan foydalanish mutlaqo bepul.\n2. Sovrinlarni olish uchun shartlarni to'g'ri bajaring.\n3. Har qanday hiyla ishlatish qat'iyan taqiqlanadi.", 
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()