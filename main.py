import os
import logging
from telegram.ext import Updater, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def start(update, context):
    update.message.reply_text("✅ 机器人部署成功！")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("❌ 错误：BOT_TOKEN 环境变量未设置！")
        return

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    logging.info("🤖 机器人已启动，正在运行...")
    updater.idle()

if __name__ == "__main__":
    main()
