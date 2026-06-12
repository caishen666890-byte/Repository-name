import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yfinance as yf
import requests
import json

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-6be607c962f04bb9948808118c96c0ec")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 触发词配置
TRIGGER_CONFIG = {
    "qw": "TSLA",      # qw → 特斯拉
    "apple": "AAPL",   # apple → 苹果
    "nv": "NVDA",      # nv → 英伟达
    "ms": "MSFT",      # ms → 微软
}

# ==================== AI 问答功能 ====================
async def ask_deepseek(question: str) -> str:
    """调用 DeepSeek API 回答问题"""
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的股票投资助手，擅长分析股市、地缘政治对市场的影响、板块轮动、利多利空消息等。回答要简洁、专业、实用，给出中肯的投资建议。注意提醒用户仅供参考，不构成投资建议。"},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"DeepSeek API 错误: {response.status_code} - {response.text}")
            return f"❌ AI 服务暂时不可用，请稍后再试。\n\n错误码: {response.status_code}"
            
    except Exception as e:
        logger.error(f"DeepSeek 调用失败: {e}")
        return "❌ 网络错误，请稍后再试。"

# ==================== 触发词配置函数 ====================
async def process_stock_query(update: Update, ticker_symbol: str, trigger_word: str = None):
    """查询股票 + AI 分析"""
    
    stock_names = {"TSLA": "特斯拉", "AAPL": "苹果", "NVDA": "英伟达", "MSFT": "微软"}
    stock_name = stock_names.get(ticker_symbol, ticker_symbol)
    
    await update.message.reply_text(f"🔍 正在分析 {stock_name}({ticker_symbol})...")

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        price = info.get('regularMarketPrice', info.get('currentPrice', 'N/A'))
        change_percent = info.get('regularMarketChangePercent', 0)
        
        if change_percent > 0:
            trend = "上涨"
            sign = "+"
        else:
            trend = "下跌"
            sign = ""
        
        # 获取 AI 分析
        ai_prompt = f"请分析{ticker_symbol}({stock_name})股票：当前价格{price}美元，今日{trend}{sign}{change_percent:.2f}%。请给出：1. 短期走势判断 2. 近期重要影响因素 3. 中肯的投资建议。简短回答。"
        ai_analysis = await ask_deepseek(ai_prompt)
        
        await update.message.reply_text(
            f"📊 {stock_name} ({ticker_symbol})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 价格：{price} USD  ({sign}{change_percent:.2f}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 AI 分析：\n{ai_analysis}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ 仅供参考，不构成投资建议"
        )
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        await update.message.reply_text(f"❌ 查询失败，请稍后再试。")

# ==================== 处理普通消息（触发词 + AI 问答） ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()
    
    # 1. 检查是否是触发词
    if text_lower in TRIGGER_CONFIG:
        ticker = TRIGGER_CONFIG[text_lower]
        await process_stock_query(update, ticker, text_lower)
        return
    
    # 2. 否则当作 AI 问答处理
    await update.message.reply_text("🤔 正在思考，请稍候...")
    answer = await ask_deepseek(text)
    await update.message.reply_text(f"🤖 分析结果：\n\n{answer}\n\n⚠️ 仅供参考，不构成投资建议")

# ==================== 指令函数 ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    trigger_list = "\n".join([f"• {w.upper()} → {c}" for w, c in TRIGGER_CONFIG.items()])
    
    await update.message.reply_text(
        f"👋 你好 {user.first_name}！我是智能股票助手\n\n"
        "📈 功能：\n"
        "• 直接提问任何投资问题（AI 智能回答）\n"
        "• 快捷触发词查询：\n" + trigger_list + "\n"
        "• /price 股票代码 - 查询股价\n"
        "• /info 股票代码 - 公司信息\n"
        "• /help - 帮助\n\n"
        "💡 例如直接发送：\n"
        "「地缘政治对科技股的影响」\n"
        "「特斯拉最近有什么消息」\n"
        "「最近哪个板块最值得关注」\n\n"
        "⚠️ 仅供参考，不构成投资建议"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ 请输入股票代码，例如：/price AAPL")
        return
    
    ticker = context.args[0].upper()
    await process_stock_query(update, ticker)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ 请输入股票代码，例如：/info AAPL")
        return
    
    ticker_symbol = context.args[0].upper()
    await update.message.reply_text(f"⏳ 正在查询 {ticker_symbol} 的公司信息...")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        name = info.get('longName', '暂无')
        sector = info.get('sector', '暂无')
        industry = info.get('industry', '暂无')
        country = info.get('country', '暂无')
        website = info.get('website', '暂无')
        
        await update.message.reply_text(
            f"🏢 {ticker_symbol}\n"
            f"名称：{name}\n"
            f"行业：{sector} - {industry}\n"
            f"国家：{country}\n"
            f"官网：{website}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ 查询失败，请检查股票代码")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 帮助\n\n"
        "💬 直接发送任何问题 → AI 分析\n"
        "⚡ 触发词：qw(特斯拉)、apple、nv、ms\n"
        "/price 代码 → 股价\n"
        "/info 代码 → 公司信息"
    )

# ==================== 主函数 ====================
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN 未设置")
        return
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ 机器人已启动")
    app.run_polling()

if __name__ == "__main__":
    main()
