from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8627249948:AAFRM36zecoOu239ZF54zux5JjIeJqGOBxs"
API_ID = 23785846
API_HASH = "bd740ea2acee7390e0b354ec809c870f"

IMAGE_PATH = r"G:\project\embykeeper\test1.jpg"  # 按你的要求写；如果实际是图片请改为 test.jpg 等

app = Client(
    "checkin_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

@app.on_message(filters.command("checkin"))
async def handle_checkin(client, message):
    buttons = [
        [
            InlineKeyboardButton("购物平台", callback_data="Shopping Website"),
            InlineKeyboardButton("灯", callback_data="lamp"),
        ],
        [
            InlineKeyboardButton("口罩", callback_data="mask"),
            InlineKeyboardButton("丝袜", callback_data="stocking"),
        ],
    ]
    await message.reply_photo(
        photo=IMAGE_PATH,
        caption="请选择正确验证码",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_message(filters.command("cancel"))
async def handle_cancel(client, message):
    await message.reply("会话已取消")

@app.on_callback_query()
async def handle_button_click(client, callback_query):
    text = callback_query.data or ""
    if text:
        await callback_query.message.reply(text)
    await callback_query.answer()

if __name__ == "__main__":
    if not (BOT_TOKEN and API_ID and API_HASH):
        raise SystemExit("请设置环境变量: BOT_TOKEN, API_ID, API_HASH")
    app.run()
