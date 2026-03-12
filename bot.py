import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7262983874:AAGa8e6ZAfUMASN9elczOYsEH5Ow3oDXjsY"

# =========================
# 配置区域
# =========================

# 频道ID
CHANNEL_ID = -1002586399808

# 群组ID
GROUP_ID = -1002586737029

# 频道链接
CHANNEL_LINK = "https://t.me/+-SnBS1difV5lMGJl"

# 群组链接
GROUP_LINK = "https://t.me/+xfF5eNVmYJw5ODE1"

# 需要邀请人数
NEED_INVITES = 3


# =========================
# 初始化数据库
# =========================

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
inviter INTEGER,
join_time INTEGER
)
""")

conn.commit()


# =========================
# 检查是否加入
# =========================

async def check_member(user_id, chat_id, context):

    try:

        member = await context.bot.get_chat_member(chat_id, user_id)

        return member.status in ["member", "administrator", "creator"]

    except:

        return False


# =========================
# 强制加入频道+群组
# =========================

async def force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    in_channel = await check_member(user_id, CHANNEL_ID, context)
    in_group = await check_member(user_id, GROUP_ID, context)

    if not (in_channel and in_group):

        keyboard = [

            [InlineKeyboardButton("📢 Tham gia kênh", url=CHANNEL_LINK)],

            [InlineKeyboardButton("👥 Tham gia nhóm", url=GROUP_LINK)],

            [InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check")]

        ]

        text = "⚠️ Bạn phải tham gia kênh và nhóm trước khi sử dụng bot"

        if update.message:

            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif update.callback_query:

            await update.callback_query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return False

    return True


# =========================
# /start 命令
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    # 防止机器人刷邀请
    if user.is_bot:
        return

    # 强制加入检测
    joined = await force_join(update, context)

    if not joined:
        return

    inviter = None

    # 获取邀请参数
    if context.args:

        try:
            inviter = int(context.args[0])
        except:
            inviter = None

    # 防止自己邀请自己
    if inviter == user_id:
        inviter = None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    # 新用户写入数据库
    if not user_data:

        if inviter:

            cursor.execute("SELECT * FROM users WHERE user_id=?", (inviter,))
            inviter_check = cursor.fetchone()

            if not inviter_check:
                inviter = None

        cursor.execute(
            "INSERT INTO users VALUES (?,?,?)",
            (user_id, inviter, int(time.time()))
        )

        conn.commit()


    # =========================
    # 统计邀请人数
    # =========================

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

    # 完成任务
    if invites >= NEED_INVITES:

        text += f"""

🎉 Chúc mừng!

Bạn đã mời đủ {NEED_INVITES} người.

👇 Vào nhóm VIP tại đây
{GROUP_LINK}
"""

    else:

        remain = NEED_INVITES - invites

        text += f"""

❌ Bạn cần mời thêm {remain} người
để mở khóa nhóm VIP
"""

    await update.message.reply_text(text)


# =========================
# 验证加入按钮
# =========================

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    user_id = query.from_user.id

    in_channel = await check_member(user_id, CHANNEL_ID, context)
    in_group = await check_member(user_id, GROUP_ID, context)

    if in_channel and in_group:

        await query.answer("✅ Xác minh thành công")

        await query.message.delete()

        fake_update = Update(update.update_id, message=query.message)

        await start(fake_update, context)

    else:

        await query.answer(
            "❌ Bạn vẫn chưa tham gia kênh hoặc nhóm",
            show_alert=True
        )


# =========================
# 邀请排行榜
# =========================

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("""
    SELECT inviter, COUNT(*) as total
    FROM users
    WHERE inviter IS NOT NULL
    GROUP BY inviter
    ORDER BY total DESC
    LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:

        await update.message.reply_text("Chưa có bảng xếp hạng")

        return

    text = "🏆 BẢNG XẾP HẠNG MỜI BẠN\n\n"

    for i, row in enumerate(rows, start=1):

        inviter = row[0]
        total = row[1]

        text += f"{i}. {inviter} — {total} người\n"

    await update.message.reply_text(text)


# =========================
# 启动机器人
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("top", top))
app.add_handler(CallbackQueryHandler(check, pattern="check"))

print("Bot đang chạy...")

app.run_polling()
