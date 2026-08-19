import logging
import os
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import database as db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
COIN_PER_FOLLOW = int(os.getenv("COIN_PER_FOLLOW", "10"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Conversation states
ASK_LINK, ASK_COUNT = range(2)
WAITING_SCREENSHOT = 10

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["🎯 Vazifa bajarish", "💰 Balansim"],
        ["📢 Post qilish", "🏆 Reyting"],
        ["👤 Profilim", "🎁 Kunlik bonus"],
        ["ℹ️ Qoidalar"],
    ],
    resize_keyboard=True,
)


# ---------- asosiy menyu ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username or user.first_name)
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Bu bot orqali boshqalarning Instagram sahifasiga obuna bo'lib tanga "
        f"({COIN_PER_FOLLOW} tanga har bir obuna uchun) topasiz, keyin o'zingizga "
        "obunachi olish uchun shu tangalarni sarflaysiz.\n\n"
        "Quyidagi menyudan foydalaning:",
        reply_markup=MAIN_MENU,
    )


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = db.get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 Sizning balansingiz: <b>{balance} tanga</b>", parse_mode="HTML")


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = db.get_balance(user.id)
    await update.message.reply_text(
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"ism: {user.first_name}\n"
        f"💰 Balans: <b>{balance} tanga</b>",
        parse_mode="HTML",
        reply_markup=MAIN_MENU,
    )


async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bu yerda oddiy kunlik bonus berish mantiqi (bazaga bog'liq holda kengaytirish mumkin)
    user_id = update.effective_user.id
    bonus_amount = 5
    db.approve_submission  # yoki bazaga tanga qo'shish funksiyasi
    # Hozircha oddiy xabar sifatida:
    await update.message.reply_text(
        f"🎁 Siz kunlik bonus sifatida <b>{bonus_amount} tanga</b> oldingiz! (Tez orada to'liq ishga tushadi)",
        parse_mode="HTML",
        reply_markup=MAIN_MENU,
    )


async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Qoidalar</b>\n\n"
        f"1. Vazifa bajaring (birov aytgan Instagram sahifasiga obuna bo'ling) — {COIN_PER_FOLLOW} tanga olasiz.\n"
        "2. Obuna bo'lganingizga dalil sifatida screenshot yuboring.\n"
        "3. Admin screenshotni tekshirib, tasdiqlaydi yoki rad etadi.\n"
        "4. Yig'gan tangalaringiz bilan o'z sahifangizni \"Post qilish\" orqali "
        "vazifa qilib qo'yishingiz mumkin — boshqalar sizga obuna bo'lib beradi.\n\n"
        "⚠️ Screenshot soxta bo'lsa yoki obuna bo'lmasdan yuborilsa, rad etiladi.",
        reply_markup=MAIN_MENU,
        parse_mode="HTML",
    )


async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = db.get_top_users()
    if not top:
        await update.message.reply_text("Hali hech kim tanga to'plamagan.")
        return
    lines = ["🏆 <b>Eng ko'p tanga to'plaganlar</b>\n"]
    for i, u in enumerate(top, 1):
        name = u["username"] or "Foydalanuvchi"
        lines.append(f"{i}. @{name} — {u['coins']} tanga")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ---------- vazifa bajarish (obuna bo'lish -> screenshot) ----------

async def next_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    worker_id = update.effective_user.id
    task = db.get_next_task(worker_id)
    if not task:
        await update.message.reply_text(
            "Hozircha bajarish uchun vazifa yo'q. Keyinroq qayta urinib ko'ring.",
            reply_markup=MAIN_MENU,
        )
        return ConversationHandler.END

    context.user_data["current_task_id"] = task["task_id"]
    await update.message.reply_text(
        f"🎯 <b>Vazifa</b>\n\nUshbu sahifaga obuna bo'ling:\n{task['ig_link']}\n\n"
        f"Mukofot: {task['coin_cost']} tanga\n\n"
        "Obuna bo'lgach, shu yerga screenshot (rasm) yuboring 👇",
        parse_mode="HTML",
    )
    return WAITING_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get("current_task_id")
    if not task_id or not update.message.photo:
        await update.message.reply_text("Iltimos, rasm (screenshot) yuboring.")
        return WAITING_SCREENSHOT

    worker = update.effective_user
    photo_file_id = update.message.photo[-1].file_id
    submission_id = db.create_submission(task_id, worker.id, photo_file_id)
    task = db.get_task(task_id)

    await update.message.reply_text(
        "✅ Screenshot qabul qilindi. Admin tekshirgach, tanga hisobingizga qo'shiladi.",
        reply_markup=MAIN_MENU,
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{submission_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{submission_id}"),
        ]
    ])
    caption = (
        f"Yangi tasdiqlash so'rovi\n\n"
        f"Foydalanuvchi: @{worker.username or worker.first_name} (ID: {worker.id})\n"
        f"Vazifa: {task['ig_link']}\n"
        f"Mukofot: {task['coin_cost']} tanga"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id, photo=photo_file_id, caption=caption, reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"Adminga yuborishda xatolik ({admin_id}): {e}")

    return ConversationHandler.END


async def cancel_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ---------- admin tasdiqlash tugmalari ----------

async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    action, sub_id_str = query.data.split(":")
    submission_id = int(sub_id_str)

    if action == "approve":
        result = db.approve_submission(submission_id)
        if result is None:
            await query.edit_message_caption(caption=(query.message.caption or "") + "\n\n⚠️ Allaqachon ko'rib chiqilgan.")
            return
        await context.bot.send_message(
            chat_id=result["worker_id"],
            text=f"✅ Screenshotingiz tasdiqlandi! +{result['coin_cost']} tanga hisobingizga qo'shildi.",
        )
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\n✅ Tasdiqlandi")

    elif action == "reject":
        result = db.reject_submission(submission_id)
        if result is None:
            await query.edit_message_caption(caption=(query.message.caption or "") + "\n\n⚠️ Allaqachon ko'rib chiqilgan.")
            return
        await context.bot.send_message(
            chat_id=result["worker_id"],
            text="❌ Screenshotingiz rad etildi. Iltimos, haqiqiy obuna bo'lganingizni tasdiqlaydigan rasm yuboring.",
        )
        await query.edit_message_caption(caption=(query.message.caption or "") + "\n\n❌ Rad etildi")


# ---------- post qilish (o'z sahifasini vazifa qilib qo'yish) ----------

async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Instagram sahifangiz havolasini yuboring (masalan: https://instagram.com/username):"
    )
    return ASK_LINK


async def post_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    if "instagram.com" not in link:
        await update.message.reply_text("Iltimos, to'g'ri Instagram havolasini yuboring.")
        return ASK_LINK
    context.user_data["post_link"] = link
    balance = db.get_balance(update.effective_user.id)
    await update.message.reply_text(
        f"Nechta obunachi kerak? (1 obunachi = {COIN_PER_FOLLOW} tanga)\n"
        f"Sizning balansingiz: {balance} tanga"
    )
    return ASK_COUNT


async def post_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Iltimos, musbat butun son kiriting.")
        return ASK_COUNT

    count = int(text)
    cost = count * COIN_PER_FOLLOW
    user_id = update.effective_user.id
    balance = db.get_balance(user_id)

    if balance < cost:
        await update.message.reply_text(
            f"Yetarli tangangiz yo'q. Kerak: {cost}, mavjud: {balance}.\n"
            "Avval \"🎯 Vazifa bajarish\" orqali tanga to'plang.",
            reply_markup=MAIN_MENU,
        )
        return ConversationHandler.END

    link = context.user_data["post_link"]
    db.deduct_coins(user_id, cost)
    db.create_task(user_id, link, count, COIN_PER_FOLLOW)

    await update.message.reply_text(
        f"✅ Vazifa yaratildi! {count} ta obunachi uchun {cost} tanga yechildi.\n"
        "Boshqa foydalanuvchilar sahifangizga obuna bo'la boshlaydi.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


# ---------- admin: statistika ----------

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    stats = db.get_stats()
    await update.message.reply_text(
        f"📊 <b>Statistika</b>\n\n"
        f"Foydalanuvchilar: {stats['users']}\n"
        f"Faol vazifalar: {stats['active_tasks']}\n"
        f"Kutilayotgan tasdiqlar: {stats['pending']}\n"
        f"Tasdiqlangan: {stats['approved']}",
        parse_mode="HTML",
    )


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini tekshiring.")

    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(MessageHandler(filters.Regex("^💰 Balansim$"), show_balance))
    app.add_handler(MessageHandler(filters.Regex("^👤 Profilim$"), show_profile))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Kunlik bonus$"), daily_bonus))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Qoidalar$"), show_rules))
    app.add_handler(MessageHandler(filters.Regex("^🏆 Reyting$"), show_top))

    task_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎯 Vazifa bajarish$"), next_task)],
        states={
            WAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel_task)],
    )
    app.add_handler(task_conv)

    post_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Post qilish$"), post_start)],
        states={
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_link)],
            ASK_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel_task)],
    )
    app.add_handler(post_conv)

    app.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(approve|reject):"))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()