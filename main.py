import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ 机器人部署成功！")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("❌ 错误：BOT_TOKEN 环境变量未设置")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    logging.info("🤖 机器人已启动，正在运行...")
    app.run_polling()

if __name__ == "__main__":
    main()
