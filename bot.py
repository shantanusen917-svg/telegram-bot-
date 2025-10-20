from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import csv, os
from datetime import datetime

# ===== CONFIGURATION =====
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token Render এ Environment Variable এ থাকবে
ADMIN_ID = int(os.getenv("ADMIN_ID", 6345288802))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@ajahajahh")
PAYEER_UID = os.getenv("PAYEER_UID", "P1123839604")
CSV_FILE = "exchange_requests.csv"
current_rate = int(os.getenv("CURRENT_RATE", 125))

# Steps
AMOUNT, METHOD, NUMBER, SCREENSHOT = range(4)

# CSV তৈরি করা যদি না থাকে
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["সময়সূচি","UserID","Username","Amount","Method","Number","ScreenshotFileID"])

# ===== FUNCTION =====
def save_to_csv(user_id, username, amount, method, number, screenshot_file_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, user_id, username, amount, method, number, screenshot_file_id])
    print(f"✅ সংরক্ষণ করা হয়েছে: {username}, {amount} USD")

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("💰 Rate"), KeyboardButton("🔁 Exchange")],
                [KeyboardButton("🆘 Help")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🌐 স্বাগতম আমাদের USD → BDT এক্সচেঞ্জ বটে 💵\n\n"
        "👇 নিচের অপশন থেকে বেছে নিন:", reply_markup=reply_markup)

async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💱 আজকের এক্সচেঞ্জ রেট:\n1 USD = {current_rate} BDT\n\n⚡ রেট সময় অনুযায়ী পরিবর্তিত হতে পারে।")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆘 সাহায্য দরকার?\n\n👨‍💼 Admin: {ADMIN_USERNAME}\n⏰ সময়: সকাল 10টা - রাত 10টা\n\n⚠️ শুধুমাত্র অফিসিয়াল Admin-এর সাথেই যোগাযোগ করুন।"
    )

async def exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💸 আপনি কত USD এক্সচেঞ্জ করতে চান?\nউদাহরণ: 10, 20, 50 ইত্যাদি", reply_markup=ReplyKeyboardRemove())
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("⚠️ দয়া করে শুধুমাত্র সংখ্যা লিখুন। উদাহরণ: 10, 20, 50")
        return AMOUNT
    context.user_data["amount"] = update.message.text
    keyboard = [[KeyboardButton("📱 Nagad"), KeyboardButton("💳 Bkash"), KeyboardButton("🏦 Rocket")]]
    await update.message.reply_text(
        f"✅ ধন্যবাদ! আপনি {context.user_data['amount']} USD এক্সচেঞ্জ করতে চাচ্ছেন।\n\n"
        "এখন বলুন — কোন মাধ্যমে টাকা নিতে চান 👇", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return METHOD

async def get_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["method"] = update.message.text
    await update.message.reply_text(f"📲 অনুগ্রহ করে আপনার {context.user_data['method']} নাম্বার পাঠান (যেমন: 017XXXXXXXX)")
    return NUMBER

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["number"] = update.message.text
    await update.message.reply_text(
        f"✅ অনুগ্রহ করে এখন আমাদের Payeer Account-এ {context.user_data['amount']} USD পাঠান:\n\n"
        f"💼 Payeer UID: {PAYEER_UID}\n\n📷 পাঠানো হয়ে গেলে ট্রান্সফার স্ক্রিনশট দিন এখানে।"
    )
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    amount = context.user_data["amount"]
    method = context.user_data["method"]
    number = context.user_data["number"]

    photo_id = None
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        photo_id = update.message.document.file_id

    if photo_id:
        save_to_csv(user.id, user.username or "Unknown", amount, method, number, photo_id)
        await update.message.reply_text("📩 স্ক্রিনশট পাওয়া গেছে ✅ যাচাই চলছে...")
        caption = (
            f"🆕 নতুন এক্সচেঞ্জ রিকোয়েস্ট\n\n"
            f"👤 User: @{user.username or 'Unknown'}\n"
            f"💵 Amount: {amount} USD\n"
            f"💳 Method: {method}\n"
            f"📲 Number: {number}"
        )
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption)
    else:
        await update.message.reply_text("⚠️ অনুগ্রহ করে স্ক্রিনশট পাঠান (image আকারে)।")
        return SCREENSHOT
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ এক্সচেঞ্জ প্রক্রিয়া বাতিল করা হয়েছে।",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("💰 Rate"), KeyboardButton("🔁 Exchange")],
             [KeyboardButton("🆘 Help")]], resize_keyboard=True
        )
    )
    return ConversationHandler.END

# ===== Admin Commands =====
async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_rate
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        try:
            current_rate = int(context.args[0])
            await update.message.reply_text(f"✅ রেট আপডেট হয়েছে!\n1 USD = {current_rate} BDT")
        except:
            await update.message.reply_text("⚠️ ব্যবহার: /setrate <Rate>")
    else:
        await update.message.reply_text("❌ শুধুমাত্র Admin ব্যবহার করতে পারবেন।")

async def set_payeer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PAYEER_UID
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        try:
            PAYEER_UID = context.args[0]
            await update.message.reply_text(f"✅ নতুন Payeer UID সেট করা হলো: {PAYEER_UID}")
        except:
            await update.message.reply_text("⚠️ ব্যবহার: /setpayeer <PayeerUID>")
    else:
        await update.message.reply_text("❌ শুধুমাত্র Admin ব্যবহার করতে পারবেন।")

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID, ADMIN_USERNAME
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        try:
            new_admin_id = int(context.args[0])
            new_admin_username = context.args[1]
            ADMIN_ID = new_admin_id
            ADMIN_USERNAME = new_admin_username
            await update.message.reply_text(f"✅ নতুন Admin সেট করা হলো:\nID: {ADMIN_ID}\nUsername: {ADMIN_USERNAME}")
        except:
            await update.message.reply_text("⚠️ ব্যবহার: /setadmin <AdminID> <@Username>")
    else:
        await update.message.reply_text("❌ শুধুমাত্র বর্তমান Admin এই কমান্ড ব্যবহার করতে পারবেন।")

# ===== MAIN =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔁 Exchange$"), exchange)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_method)],
            NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
            SCREENSHOT: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^💰 Rate$"), rate))
    app.add_handler(MessageHandler(filters.Regex("^🆘 Help$"), help_cmd))
    app.add_handler(conv_handler)

    app.add_handler(CommandHandler("setrate", set_rate))
    app.add_handler(CommandHandler("setpayeer", set_payeer))
    app.add_handler(CommandHandler("setadmin", set_admin))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
