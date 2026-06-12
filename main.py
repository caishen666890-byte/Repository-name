import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yfinance as yf
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

TRIGGER_CONFIG = {"qw": "TSLA", "apple": "AAPL", "nv": "NVDA", "ms": "MSFT"}

async def ask_deepseek(question):
    if not DEEPSEEK_API_KEY:
        return "❌ DeepSeek API Key 未配置"
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "你是股票投资助手"}, {"role": "user", "content": question}], "temperature": 0.7, "max_tokens": 800}
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "❌ AI 服务暂时不可用"
    except Exception as e:
        return "❌ 网络错误"

async def process_stock_query(update, ticker_symbol):
    stock_names = {"TSLA": "特斯拉", "AAPL": "苹果", "NVDA": "英伟达", "MSFT": "微软"}
    stock_name = stock_names.get(ticker_symbol, ticker_symbol)
    await update.message.reply_text(f"🔍 正在分析 {stock_name}...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        price = info.get('regularMarketPrice', info.get('currentPrice', 'N/A'))
        change = info.get('regularMarketChangePercent', 0)
        sign = "+" if change > 0 else ""
        ai = await ask_deepseek(f"分析{ticker_symbol}({stock_name})股价{price}美元，今日{sign}{change:.2f}%，给出简短分析和建议")
        await update.message.reply_text(f"📊 {stock_name} ({ticker_symbol})\n💰 价格：{price} USD ({sign}{change:.2f}%)\n\n🤖 {ai}\n\n⚠️ 仅供参考")
    except Exception as e:
        await update.message.reply_text("❌ 查询失败")

async def handle_message(update, context):
    text = update.message.text.strip().lower()
    if text in TRIGGER_CONFIG:
        await process_stock_query(update, TRIGGER_CONFIG[text])
    else:
        await update.message.reply_text("🤔 思考中...")
        answer = await ask_deepseek(update.message.text)
        await update.message.reply_text(f"🤖 {answer}\n\n⚠️ 仅供参考")

async def start(update, context):
    await update.message.reply_text("👋 我是智能股票助手\n发送 qw 查特斯拉，或直接提问投资问题")

async def price(update, context):
    if context.args:
        await process_stock_query(update, context.args[0].upper())
    else:
        await update.message.reply_text("用法：/price AAPL")

async def info(update, context):
    if not context.args:
        await update.message.reply_text("用法：/info AAPL")
        return
    try:
        t = yf.Ticker(context.args[0].upper())
        i = t.info
        await update.message.reply_text(f"🏢 {context.args[0].upper()}\n名称：{i.get('longName','暂无')}\n行业：{i.get('sector','暂无')}")
    except:
        await update.message.reply_text("查询失败")

async def help_cmd(update, context):
    await update.message.reply_text("指令：/price 代码、/info 代码\n触发词：qw(特斯拉) apple nv ms\n直接提问任何投资问题")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN 未设置")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("机器人启动成功")
    app.run_polling()

if __name__ == "__main__":
    main()
