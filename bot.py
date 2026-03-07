import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7262983874:AAGa8e6ZAfUMASN9elczOYsEH5Ow3oDXjsY"

CHANNEL_ID = -1002586399808
GROUP_ID = -1002586737029

CHANNEL_LINK = "https://t.me/+-SnBS1difV5lMGJl"
GROUP_LINK = "https://t.me/+xfF5eNVmYJw5ODE1"

NEED_INVITES = 3


conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
inviter INTEGER
)
""")
conn.commit()


async def check_member(user_id, chat_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    inviter = None

    if context.args:
        inviter = int(context.args[0])

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users VALUES (?,?)", (user_id, inviter))
        conn.commit()

    in_channel = await check_member(user_id, CHANNEL_ID, context)
    in_group = await check_member(user_id, GROUP_ID, context)

    if not (in_channel and in_group):

        keyboard = [
            [InlineKeyboardButton("📢 Tham gia kênh", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👥 Tham gia nhóm", url=GROUP_LINK)],
            [InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check")]
        ]

        await update.message.reply_text(
            "⚠️ Bạn phải tham gia kênh và nhóm trước",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return


    cursor.execute("SELECT COUNT(*) FROM users WHERE inviter=?", (user_id,))
    invites = cursor.fetchone()[0]

    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"

    text = f"""
📊 THỐNG KÊ MỜI BẠN

👤 ID của bạn: {user_id}

👥 Số người đã mời: {invites}

🎯 Cần mời: {NEED_INVITES}

🔗 Link mời của bạn:
{invite_link}
"""

    if invites >= NEED_INVITES:

        text += f"""

✅ Bạn đã mời đủ {NEED_INVITES} người!

🎉 Bạn có thể vào nhóm:
{GROUP_LINK}
"""

    else:

        remain = NEED_INVITES - invites

        text += f"""

❌ Bạn cần mời thêm {remain} người
để mở khóa nhóm.
"""

    await update.message.reply_text(text)


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    in_channel = await check_member(user_id, CHANNEL_ID, context)
    in_group = await check_member(user_id, GROUP_ID, context)

    if in_channel and in_group:
        await query.answer("✅ Xác minh thành công")
    else:
        await query.answer("❌ Bạn chưa tham gia", show_alert=True)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check, pattern="check"))

print("Bot đang chạy...")

app.run_polling()